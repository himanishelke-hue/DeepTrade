import os
import subprocess
import os
import subprocess

# Print all env vars for debugging
print("GOOGLE_ID:", os.environ.get('GOOGLE_CLIENT_ID', 'NOT FOUND'))

# Run migrations
subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=False)

# Collect static files
subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=False)

# Create superuser
subprocess.run([
    "python", "manage.py", "shell", "-c",
    "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','a@a.com','pass123'); print('admin ready')"
], check=False)

# Gunicorn config
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1
worker_class = "gthread"
threads = 2
timeout = 120