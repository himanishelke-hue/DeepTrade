import os
import subprocess

print("GOOGLE_ID:", os.environ.get('GOOGLE_CLIENT_ID', 'NOT FOUND'))

subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=False)
subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=False)

GOOGLE_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
SITE_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-7558.up.railway.app')

subprocess.run(["python", "manage.py", "shell", "-c", f"""
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

site, _ = Site.objects.get_or_create(id=1)
site.domain = '{SITE_DOMAIN}'
site.name = 'DeepTrade'
site.save()

if not SocialApp.objects.filter(provider='google').exists():
    app = SocialApp.objects.create(
        provider='google',
        name='Google',
        client_id='{GOOGLE_ID}',
        secret='{GOOGLE_SECRET}',
    )
    app.sites.add(site)
    print('Google app created!')
else:
    print('Google app exists!')
"""], check=False)

subprocess.run(["python", "manage.py", "shell", "-c",
    "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','a@a.com','pass123'); print('admin ready')"
], check=False)

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1
worker_class = "gthread"
threads = 2
timeout = 120