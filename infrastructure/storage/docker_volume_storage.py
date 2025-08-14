from interfaces.storage.file_storage import FileStorage
from django.core.files.storage import default_storage

class DockerVolumeStorage(FileStorage):
    """Implementación para Docker volumes"""
    def save(self, file) -> str:
        return default_storage.save(f'experiments/{file.name}', file)