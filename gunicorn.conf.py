# gunicorn.conf.py — production configuration
import os

# Workers: 1 worker + 4 threads is safe on 512MB RAM (free tier)
# Each numpy/statsmodels/pandas worker uses ~200MB
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
threads = int(os.environ.get('GUNICORN_THREADS', 4))
timeout = 120
keepalive = 5
max_requests = 500          # recycle workers to avoid memory leaks
max_requests_jitter = 50
worker_class = 'gthread'    # threaded worker

# Logging
accesslog = '-'
errorlog  = '-'
loglevel  = 'info'

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
