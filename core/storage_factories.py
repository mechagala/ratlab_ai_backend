from django.conf import settings
from infrastructure.storage.docker_volume_storage import DockerVolumeStorage
from infrastructure.storage.local_storage import LocalVideoStorage  # Para desarrollo

def get_video_storage():
    if settings.STORAGE_TYPE == 'docker_volume':
        return DockerVolumeStorage()
    return LocalVideoStorage()  # Default para desarrollo