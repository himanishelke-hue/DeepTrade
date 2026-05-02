# DeepTrade — AI Stock Market Prediction (Django)

NSE India stock analysis with Linear Regression, ARIMA forecasting, and Groq AI chatbot.

---

## ✅ Production Checklist

Before deploying, ensure:
- [ ] `SECRET_KEY` is set (long random string, never the default)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` contains your domain
- [ ] `CSRF_TRUSTED_ORIGINS` contains your `https://` URL
- [ ] `GROQ_API_KEY` set (optional — chatbot shows friendly message without it)
- [ ] `DATABASE_URL` set to PostgreSQL for real deploy (SQLite is fine for demos)

---

## Local Setup

```bash
# 1. Clone / unzip project
cd Stock-Market-Prediction

# 2. Create virtualenv
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows

# 3. Install deps
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Open .env and fill in SECRET_KEY, GROQ_API_KEY, etc.

# 5. Migrate + collect static
python manage.py migrate
python manage.py collectstatic --noinput

# 6. Run
python manage.py runserver
```

---

## Deploy to Render (Recommended — Free Tier)

1. Push project to GitHub
2. Create **New Web Service** on [render.com](https://render.com)
3. Set:
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Add environment variables (from `.env.example`) in Render dashboard
5. Done ✅

### Required Environment Variables on Render:
| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourapp.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://yourapp.onrender.com` |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) |
| `DATABASE_URL` | Add a PostgreSQL addon or leave empty for SQLite |
| `SECURE_SSL_REDIRECT` | `True` |

---

## Deploy to Railway

Same as Render. Railway auto-detects `Procfile`. Set the same env vars above.

---

## API Health Check

`GET /health/` → `{"status": "ok"}` — always returns 200, no auth required.
Use this as your Render/Railway/UptimeRobot health check URL.

---

## Project Structure

```
Stock-Market-Prediction/
├── app/
│   ├── views.py          # All views — every external API call is try/except
│   ├── views_errors.py   # Custom 404 / 500 handlers
│   ├── models.py
│   ├── templates/
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── ...
│   └── static/
├── core/
│   ├── settings.py       # env-var driven, production-safe
│   ├── middleware.py     # HealthCheck + APIError middleware
│   ├── urls.py
│   └── wsgi.py
├── build.sh              # One-command deploy build script
├── Procfile              # gunicorn + release: migrate
├── runtime.txt           # python-3.11.9
├── requirements.txt
└── .env.example          # Copy to .env and fill in values
```
