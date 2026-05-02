"""
DeepTrade — views.py
All external API calls (yfinance, Groq) are wrapped with try/except so a
network failure or API outage never crashes the whole page.
"""
import json
import logging
import datetime
import threading
 
import numpy as np
import pandas as pd
import yfinance as yf
from plotly.offline import plot
import plotly.graph_objects as go
 
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing, model_selection
from statsmodels.tsa.arima.model import ARIMA
 
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
 
from .models import Project
 
logger = logging.getLogger(__name__)
 
# How long (seconds) to keep yfinance data in cache — default 5 min
_CACHE_TTL = getattr(settings, 'YFINANCE_CACHE_SECONDS', 300)
 
# Semaphore: allow at most 2 concurrent yfinance requests so we never flood
# Yahoo Finance's servers — prevents YFRateLimitError and "connection pool full"
_yf_sem = threading.Semaphore(2)
 
 
# ─── Helpers ─────────────────────────────────────────────────────────────────
 
def _safe_download(ticker, **kwargs):
    """Download yfinance data; caches results to avoid rate-limit errors."""
    ticker_key = ticker if isinstance(ticker, str) else ','.join(sorted(ticker))
    cache_key = f'yf_dl_{ticker_key}_{str(sorted(kwargs.items()))}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    with _yf_sem:
        # Double-check after acquiring semaphore
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            df = yf.download(ticker, progress=False, auto_adjust=True, **kwargs)
            # FIX 1: Flatten MultiIndex columns only for single-ticker downloads.
            # For multi-ticker downloads keep MultiIndex intact so per-ticker
            # column access works correctly in the index view.
            if isinstance(df.columns, pd.MultiIndex):
                if isinstance(ticker, str):
                    # Single ticker — safe to flatten: take the field-name level
                    df.columns = df.columns.get_level_values(0)
                # else: leave MultiIndex for multi-ticker callers
        except Exception as e:
            logger.warning(f"yfinance download failed for {ticker}: {e}")
            df = pd.DataFrame()
    if not df.empty:
        cache.set(cache_key, df, _CACHE_TTL)
    return df
 
 
def _safe_ticker_info(ticker_sym):
    """Fetch yfinance Ticker.info; caches the result to avoid rate-limit errors."""
    cache_key = f'ticker_info_{ticker_sym}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    with _yf_sem:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            info = yf.Ticker(ticker_sym).info or {}
        except Exception as e:
            logger.warning(f"yfinance .info failed for {ticker_sym}: {e}")
            info = {}
    if info:
        cache.set(cache_key, info, _CACHE_TTL)
    return info
 
 
def _popular_stocks_data():
    """Return sidebar popular stocks list — cached for _CACHE_TTL seconds."""
    cached = cache.get('popular_stocks_data')
    if cached is not None:
        return cached
 
    tickers = [
        "RELIANCE.NS", "BHARTIARTL.NS", "HDFCBANK.NS",
        "ICICIBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    ]
    result = []
    for t in tickers:
        info = _safe_ticker_info(t)
        cur  = float(info.get("currentPrice",  0) or 0)
        prev = float(info.get("previousClose", 0) or 0)
        # FIX 2: guard against zero previousClose before dividing
        change_pct = round((cur - prev) / prev * 100, 2) if prev else 0.0
        result.append({
            "Ticker":         t,
            "Name":           info.get("shortName", t),
            "Current_Price":  f"₹{round(cur, 2)}",
            "Previous_Close": f"₹{round(prev, 2)}",
            "Change":         f"{change_pct}%",
        })
    cache.set('popular_stocks_data', result, _CACHE_TTL)
    return result
 
 
# ─── AI Analyst ──────────────────────────────────────────────────────────────
 
def ai_analyst(request):
    return render(request, "ai_analyst.html")
 
 
# ─── Chatbot (Groq) ──────────────────────────────────────────────────────────
 
@csrf_exempt
def chatbot(request):
    if request.method != "POST":
        return render(request, "ai_analyst.html")
 
    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"response": "Invalid request."}, status=400)
 
    if not user_message:
        return JsonResponse({"response": "Please type a message."}, status=400)
 
    # Enrich with live price only if ticker fetch succeeds
    if "analyze" in user_message.lower():
        try:
            sym = user_message.split()[-1].upper() + ".NS"
            hist = _safe_download(sym, period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]
                user_message += (
                    f". Current price of {sym.replace('.NS', '')} "
                    f"is ₹{round(float(price), 2)}"
                )
        except Exception as e:
            logger.debug(f"Price enrichment skipped: {e}")
 
    groq_key = getattr(settings, "GROQ_API_KEY", "")
    if not groq_key:
        return JsonResponse({
            "response": (
                "⚠️ The AI chatbot is not configured on this server. "
                "Please set the GROQ_API_KEY environment variable."
            )
        })
 
    try:
        import httpx
        from groq import Groq
        client = Groq(api_key=groq_key, http_client=httpx.Client(trust_env=False))
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant for Indian stock market analysis.\n"
                        "Answer any question directly and concisely.\n"
                        "For stock/company questions use:\n"
                        "📊 Overview | 💰 Financials | 📈 Market Insight | ⚠️ Risks | ✅ Verdict"
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        answer = (
            "⚠️ The AI service is temporarily unavailable. "
            "Please try again in a moment."
        )
 
    return JsonResponse({"response": answer})
 
 
# ─── Home / Index ─────────────────────────────────────────────────────────────
 
@login_required
def index(request):
    homepage_tickers = [
        "RELIANCE.NS", "BHARTIARTL.NS", "HDFCBANK.NS",
        "ICICIBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    ]
 
    fig_left = go.Figure()
    try:
        data = _safe_download(homepage_tickers, period="1mo", interval="1d")
        if not data.empty:
            # FIX 3: Detect the date column name — reset_index() can produce
            # "Date" or "Datetime" depending on the yfinance version / interval.
            data.reset_index(inplace=True)
            date_col = "Date" if "Date" in data.columns else (
                "Datetime" if "Datetime" in data.columns else data.columns[0]
            )
            for t in homepage_tickers:
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        # Multi-ticker download keeps MultiIndex intact (FIX 1)
                        if ("Close", t) in data.columns:
                            y_vals = data[("Close", t)]
                        elif (t, "Close") in data.columns:
                            y_vals = data[(t, "Close")]
                        else:
                            continue
                    else:
                        # Flattened (shouldn't happen for multi-ticker, but safe)
                        y_vals = data.get("Close", pd.Series(dtype=float))
                    fig_left.add_trace(go.Scatter(x=data[date_col], y=y_vals, name=t))
                except Exception as e:
                    logger.debug(f"Trace skip {t}: {e}")
        else:
            fig_left.add_annotation(
                text="Market data unavailable", showarrow=False,
                font=dict(color="white", size=16),
            )
    except Exception as e:
        logger.error(f"Index chart error: {e}")
 
    fig_left.update_layout(
        paper_bgcolor="#020617", plot_bgcolor="#020617", font_color="white",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,255,255,0.1)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,255,255,0.1)"),
    )
    plot_div_left = plot(fig_left, auto_open=False, output_type="div")
 
    # Recent stocks table — each ticker independent, never blocks others
    recent_data = []
    for t in homepage_tickers:
        row = {
            "Ticker": t.replace(".NS", ""),
            "Open": "N/A", "High": "N/A", "Low": "N/A",
            "Close": "N/A", "Adj Close": "N/A", "Volume": "N/A",
        }
        try:
            df = _safe_download(t, period="1d", interval="1m")
            if df.empty:
                df = _safe_download(t, period="5d", interval="1d")
            if df.empty:
                df = _safe_download(t, period="1mo", interval="1d")
            if not df.empty:
                row.update({
                    "Open":      f"₹{float(df['Open'].dropna().iloc[0]):,.2f}",
                    "High":      f"₹{float(df['High'].dropna().max()):,.2f}",
                    "Low":       f"₹{float(df['Low'].dropna().min()):,.2f}",
                    "Close":     f"₹{float(df['Close'].dropna().iloc[-1]):,.2f}",
                    "Adj Close": f"₹{float(df['Close'].dropna().iloc[-1]):,.2f}",
                    "Volume":    f"{int(df['Volume'].dropna().sum()):,}",
                })
        except Exception as e:
            logger.debug(f"Row error {t}: {e}")
        recent_data.append(row)
 
    return render(request, "index.html", {
        "plot_div_left": plot_div_left,
        "recent_stocks":  recent_data,
    })
 
 
# ─── Search ───────────────────────────────────────────────────────────────────
 
@login_required
def search(request):
    popular_tickers = [
        "RELIANCE.NS", "BHARTIARTL.NS", "HDFCBANK.NS",
        "ICICIBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    ]
    popular_stocks = []
    for t in popular_tickers:
        info = _safe_ticker_info(t)
        cur  = float(info.get("currentPrice",  0) or 0)
        prev = float(info.get("previousClose", 0) or 0)
        # FIX 2 (same guard as _popular_stocks_data)
        change_pct = round((cur - prev) / prev * 100, 2) if prev else 0.0
        popular_stocks.append({
            "Ticker":         t,
            "Name":           info.get("shortName", t),
            "Current_Price":  f"₹{round(cur, 2)}",
            "Previous_Close": f"₹{round(prev, 2)}",
            "Change":         f"{change_pct}%",
            "Market_Cap":     f"₹{round((info.get('marketCap') or 0) / 10_000_000, 2)}Cr",
            "Volume":         format(info.get("volume") or 0, ",d"),
        })
    return render(request, "search.html", {"popular_stocks": popular_stocks})
 
 
# ─── Ticker list ──────────────────────────────────────────────────────────────
 
@login_required
def ticker(request):
    import os
    csv_path = os.path.join(settings.BASE_DIR, "app", "Data", "new_tickers.csv")
    try:
        df = pd.read_csv(csv_path)
        ticker_list = json.loads(df.reset_index().to_json(orient="records"))
    except Exception as e:
        logger.error(f"Tickers CSV error: {e}")
        ticker_list = []
    return render(request, "ticker.html", {"ticker_list": ticker_list})
 
 
# ─── Valid Tickers ────────────────────────────────────────────────────────────
 
VALID_TICKERS = {
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","HINDUNILVR.NS",
    "BHARTIARTL.NS","ITC.NS","SBIN.NS","LICI.NS","LT.NS","BAJFINANCE.NS","HCLTECH.NS",
    "KOTAKBANK.NS","AXISBANK.NS","ASIANPAINT.NS","TITAN.NS","ADANIENT.NS","MARUTI.NS",
    "ULTRACEMCO.NS","SUNPHARMA.NS","NTPC.NS","BAJAJFINSV.NS","DMART.NS","TATAMOTORS.NS",
    "ONGC.NS","NESTLEIND.NS","ADANIGREEN.NS","WIPRO.NS","COALINDIA.NS","ADANIPORTS.NS",
    "POWERGRID.NS","JSWSTEEL.NS","M&M.NS","ADANIPOWER.NS","BAJAJ-AUTO.NS","HAL.NS",
    "LTIM.NS","IOC.NS","DLF.NS","TATASTEEL.NS","VBL.NS","JIOFIN.NS","SBILIFE.NS",
    "SIEMENS.NS","GRASIM.NS","HDFCLIFE.NS","HINDALCO.NS","PIDILITIND.NS","BEL.NS",
    "HINDZINC.NS","IRFC.NS","BRITANNIA.NS","PFC.NS","INDUSINDBK.NS","TECHM.NS",
    "BANKBARODA.NS","ADANIENSOL.NS","GODREJCP.NS","INDIGO.NS","EICHERMOT.NS","RECLTD.NS",
    "ATGL.NS","TRENT.NS","ZOMATO.NS","GAIL.NS","TATAPOWER.NS","CHOLAFIN.NS","PNB.NS",
    "DIVISLAB.NS","AMBUJACEM.NS","SHREECEM.NS","TATACONSUM.NS","CIPLA.NS","ABB.NS",
    "DABUR.NS","LODHA.NS","BPCL.NS","DRREDDY.NS","TVSMOTOR.NS","VEDL.NS","UNIONBANK.NS",
    "HAVELLS.NS","BAJAJHLDNG.NS","HEROMOTOCO.NS","POLYCAB.NS","APOLLOHOSP.NS","IOB.NS",
    "MCDOWELL-N.NS","MANKIND.NS","CANBK.NS","TORNTPHARM.NS","IDEA.NS","SHRIRAMFIN.NS",
    "ICICIPRULI.NS","JINDALSTEL.NS","SRF.NS","IDBI.NS","SBICARD.NS","IRCTC.NS",
    "MARICO.NS","BERGEPAINT.NS","ICICIGI.NS","ZYDUSLIFE.NS","CGPOWER.NS","MOTHERSON.NS",
    "COLPAL.NS","TIINDIA.NS","HDFCAMC.NS","BHEL.NS","JSWENERGY.NS","MAXHEALTH.NS",
    "NAUKRI.NS","BOSCHLTD.NS","NHPC.NS","AUROPHARMA.NS","IDFCFIRSTB.NS","INDHOTEL.NS",
    "ALKEM.NS","YESBANK.NS","NMDC.NS","SOLARINDS.NS","LUPIN.NS","MUTHOOTFIN.NS",
    "SUPREMEIND.NS","BHARATFORG.NS","PATANJALI.NS","PERSISTENT.NS","INDIANB.NS",
    "HINDPETRO.NS","PGHH.NS","GODREJPROP.NS","LTTS.NS","MRF.NS","TATAELXSI.NS",
    "CUMMINSIND.NS","GICRE.NS","INDUSTOWER.NS","PIIND.NS","ASHOKLEY.NS","AUBANK.NS",
    "OBEROIRLTY.NS","CONCOR.NS","FACT.NS","SUZLON.NS","MPHASIS.NS","BANKINDIA.NS",
    "ASTRAL.NS","SAIL.NS","TATACOMM.NS","SCHAEFFLER.NS","BALKRISIND.NS","NYKAA.NS",
    "GMRINFRA.NS","LINDEINDIA.NS","TATATECH.NS","UCOBANK.NS","PRESTIGE.NS","UBL.NS",
    "TORNTPOWER.NS","UPL.NS","JSWINFRA.NS","CENTRALBK.NS","PAGEIND.NS","DALBHARAT.NS",
    "APLAPOLLO.NS","ACC.NS","KPITTECH.NS","OIL.NS","PAYTM.NS","PHOENIXLTD.NS",
    "DIXON.NS","SUNDARMFIN.NS","BANDHANBNK.NS","COFORGE.NS","FEDERALBNK.NS","RVNL.NS",
    "JUBLFOOD.NS","OFSS.NS","CDSL.NS","ANGELONE.NS","BSE.NS","BIOCON.NS",
}
 
 
# ─── Predict ──────────────────────────────────────────────────────────────────
 
@login_required
def predict(request, ticker_value, number_of_days):
    ticker_value = ticker_value.upper()
    if not ticker_value.endswith(".NS"):
        ticker_value += ".NS"
 
    try:
        number_of_days = int(number_of_days)
    except (ValueError, TypeError):
        return render(request, "Invalid_Days_Format.html",
                      {"error_message": "Invalid number of days."})
 
    if number_of_days < 0:
        return render(request, "Negative_Days.html",
                      {"error_message": "Number of days cannot be negative."})
    if number_of_days >= 365:
        return render(request, "Overflow_days.html",
                      {"error_message": "Maximum forecast is 364 days."})
    if number_of_days == 0:
        number_of_days = 1
 
    if ticker_value not in VALID_TICKERS:
        return render(request, "Invalid_Ticker.html",
                      {"error_message": f"Ticker '{ticker_value}' is not supported."})
 
    # ── Candlestick chart ────────────────────────────────────────────────────
    df = _safe_download(ticker_value, period="1d", interval="1m")
    if df.empty:
        df = _safe_download(ticker_value, period="1mo", interval="1d")
 
    fig = go.Figure()
    if not df.empty:
        try:
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                name="Market Data",
            ))
            fig.update_xaxes(rangeslider_visible=True, rangeselector=dict(
                buttons=[
                    dict(count=15, label="15m", step="minute", stepmode="backward"),
                    dict(count=45, label="45m", step="minute", stepmode="backward"),
                    dict(count=1,  label="HTD", step="hour",   stepmode="todate"),
                    dict(count=3,  label="3h",  step="hour",   stepmode="backward"),
                    dict(step="all"),
                ]
            ))
        except Exception as e:
            logger.warning(f"Candlestick error: {e}")
    else:
        fig.add_annotation(
            text="Live data unavailable — try again shortly.",
            showarrow=False, font=dict(color="orange", size=14),
        )
 
    fig.update_layout(
        title=f"{ticker_value} — Price",
        yaxis_title="Price (INR)",
        paper_bgcolor="#14151b", plot_bgcolor="#14151b", font_color="white",
    )
    plot_div = plot(fig, auto_open=False, output_type="div")
 
    # ── Machine Learning ─────────────────────────────────────────────────────
    confidence, forecast1, forecast2 = 0, [], []
 
    try:
        # FIX 4: use 6mo daily data instead of 3mo hourly — far more rows,
        # avoids the "not enough data" error for large number_of_days values.
        df_ml = _safe_download(ticker_value, period="6mo", interval="1d")
        if df_ml.empty:
            raise ValueError("No ML data available")
 
        df_ml = df_ml[["Close"]].dropna().copy()
        n = number_of_days
 
        # Need at least n + 30 rows for a meaningful train/test split
        min_rows = n + 30
        if len(df_ml) < min_rows:
            raise ValueError(
                f"Not enough rows ({len(df_ml)}) for a {n}-day forecast "
                f"(need {min_rows})."
            )
 
        df_ml["Prediction"] = df_ml["Close"].shift(-n)
        X = preprocessing.scale(np.array(df_ml.drop(columns=["Prediction"])))
        X_forecast = X[-n:]
        X_train_all = X[:-n]
        y_train_all = np.array(df_ml["Prediction"].iloc[:-n])
 
        # FIX 5: drop NaN targets that shift() produces at the tail
        valid_mask = ~np.isnan(y_train_all)
        X_train_all = X_train_all[valid_mask]
        y_train_all = y_train_all[valid_mask]
 
        if len(X_train_all) < 10:
            raise ValueError("Too few valid training samples after NaN drop.")
 
        X_train, X_test, y_train, y_test = model_selection.train_test_split(
            X_train_all, y_train_all, test_size=0.2, random_state=42
        )
        clf = LinearRegression()
        clf.fit(X_train, y_train)
        confidence = round(clf.score(X_test, y_test), 4)
        forecast1  = clf.predict(X_forecast).tolist()
 
        # ── ARIMA ────────────────────────────────────────────────────────────
        # FIX 6: catch numpy LinAlgError and ValueError from ARIMA separately
        # so a singular matrix doesn't swallow the whole predict view.
        close_vals = df_ml["Close"].values.tolist()
        size       = int(len(close_vals) * 0.80)
        train_a, test_a = close_vals[:size], close_vals[size:]
        history    = list(train_a)
        max_steps  = min(n, len(test_a), 30)   # cap at 30 to avoid timeout
 
        for t_idx in range(max_steps):
            try:
                model_fit = ARIMA(history, order=(6, 1, 0)).fit()
                yhat      = float(model_fit.forecast()[0])
            except (np.linalg.LinAlgError, ValueError, Exception) as arima_err:
                logger.debug(f"ARIMA step {t_idx} fallback: {arima_err}")
                yhat = history[-1]   # carry last known price forward
            forecast2.append(yhat)
            history.append(test_a[t_idx] if t_idx < len(test_a) else yhat)
 
    except Exception as e:
        logger.error(f"ML error for {ticker_value}: {e}")
        # confidence=0, forecast1=[], forecast2=[] — page still renders cleanly
 
    # ── Prediction charts ────────────────────────────────────────────────────
    def _pred_chart(forecasts, title):
        dates = [
            datetime.datetime.today() + datetime.timedelta(days=i)
            for i in range(len(forecasts))
        ]
        f = go.Figure([go.Scatter(x=dates, y=forecasts)])
        if not forecasts:
            f.add_annotation(
                text="Forecast unavailable", showarrow=False,
                font=dict(color="orange", size=14),
            )
        f.update_xaxes(rangeslider_visible=True)
        f.update_layout(
            title=title, paper_bgcolor="#14151b",
            plot_bgcolor="#14151b", font_color="white",
        )
        return plot(f, auto_open=False, output_type="div")
 
    plot_div_pred1 = _pred_chart(forecast1, "Linear Regression Forecast")
    plot_div_pred2 = _pred_chart(forecast2, "ARIMA Forecast")
 
    # ── Stock info ───────────────────────────────────────────────────────────
    info       = _safe_ticker_info(ticker_value)
    last_sale  = float(info.get("previousClose", 0) or 0)
    cur_price  = float(info.get("currentPrice",  0) or 0)
    net_change = round(cur_price - last_sale, 2)
    # FIX 2 (same guard): avoid ZeroDivisionError when previousClose is 0
    pct_change = round((net_change / last_sale * 100) if last_sale else 0.0, 2)
    epoch      = info.get("firstTradeDateEpochUtc", 0) or 0
    try:
        ipo_year = datetime.datetime.utcfromtimestamp(epoch).year if epoch else "N/A"
    except (OSError, OverflowError, ValueError):
        ipo_year = "N/A"
 
    return render(request, "result.html", {
        "plot_div":       plot_div,
        "confidence":     confidence,
        # FIX 7: always pass a list (empty is fine) — templates can safely loop
        "forecast":       forecast1 if forecast1 else [],
        "ticker_value":   ticker_value,
        "number_of_days": number_of_days,
        "plot_div_pred1": plot_div_pred1,
        "plot_div_pred2": plot_div_pred2,
        "Symbol":         ticker_value,
        "Name":           info.get("shortName",  "N/A"),
        "Last_Sale":      last_sale,
        "Net_Change":     str(net_change),
        "Percent_Change": str(pct_change),
        "Market_Cap":     info.get("marketCap",  "N/A"),
        "Country":        info.get("country",    "N/A"),
        "IPO_Year":       ipo_year,
        "Volume":         info.get("volume",     "N/A"),
        "Sector":         info.get("sector",     "N/A"),
        "Industry":       info.get("industry",   "N/A"),
        "popular_stocks": _popular_stocks_data(),
    })
 
 
# ─── Guide & Quiz ─────────────────────────────────────────────────────────────
 
@login_required
def guide(request):
    return render(request, "guide.html")
 
 
@login_required
def quiz(request):
    return render(request, "quiz.html", {})