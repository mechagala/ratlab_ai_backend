FROM python:3.10-slim

# Instala dependencias del sistema para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ratlab_ai_backend

# Instala dependencias de Python (incluyendo OpenCV)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python opencv-python-headless || true && \
    pip install --no-cache-dir opencv-python-headless==4.12.0.88 && \
    pip install certifi

# Crea la carpeta media y asegura permisos
RUN mkdir -p media && chmod 777 media
RUN mkdir -p /tmp/ultralytics && chmod 777 /tmp/ultralytics

# Copia TODO el proyecto (incluyendo core/, config/, etc.)
COPY . .

# Variables para Celery
ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/1

# Comando para iniciar Django (ajusta "config" al nombre de tu módulo de settings)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]