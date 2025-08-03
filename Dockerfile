FROM python:3.10-slim

# Usa el mismo nombre que tu proyecto (donde está manage.py)
WORKDIR /ratlab_ai_backend

# Crea la carpeta media y asegura permisos
RUN mkdir -p media && chmod 777 media

# Instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODO el proyecto (incluyendo core/, config/, etc.)
COPY . .

# Variables para Celery
ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/1

# Comando para iniciar Django (ajusta "config" al nombre de tu módulo de settings)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]