import os
import subprocess

# Run migrations before gunicorn starts
subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=True)

# Gunicorn config
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1
worker_class = "gthread"
threads = 2
timeout = 120