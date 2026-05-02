"""
Data migration: ensure the default Site object has the correct domain.
Reads SITE_DOMAIN from environment (set to your deployment URL).
Falls back to 'localhost:8000' for local dev.
"""
from django.db import migrations
import os


def set_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    domain = os.environ.get('SITE_DOMAIN', 'localhost:8000')
    name   = os.environ.get('SITE_NAME',   'DeepTrade')
    Site.objects.update_or_create(
        id=1,
        defaults={'domain': domain, 'name': name}
    )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, migrations.RunPython.noop),
    ]
