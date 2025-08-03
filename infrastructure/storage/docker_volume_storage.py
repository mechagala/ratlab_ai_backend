import os
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from interfaces.storage.video_storage import VideoStorage

class DockerVolumeStorage(VideoStorage):
    def __init__(self):
        # Configuración para volumen Docker
        self.volume_path = '/mnt/experiments_volume'  # Ruta montada en el contenedor
        self.fs = FileSystemStorage(
            location=self.volume_path,
            base_url='/experiments/'  # URL base para acceso
        )

    def save(self, video_file) -> str:
        """Guarda en volumen Docker con estructura organizada"""
        filename = f"{timezone.now().strftime('%Y%m%d')}/{video_file.name}"
        return self.fs.save(filename, video_file)

    def get_url(self, path: str) -> str:
        """Genera URL accesible para el frontend"""
        return f"/media/{path}"  # Ajustar según configuración NGINX/Apache
