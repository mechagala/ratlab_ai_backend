from __future__ import absolute_import
import os
from celery import Celery
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubre las tareas en todas las apps INSTALLED_APPS
# Cambia la línea de autodiscover_tasks para que sea más específica
app.autodiscover_tasks(['core.tasks'])  # Sin force=True