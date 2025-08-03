import os
from celery import Celery

# Usa el nombre de tu módulo Django (debe coincidir con settings.py)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ratlab')  # Nombre del proyecto
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['core'])  # Busca tasks.py en tus apps