from celery import shared_task
from django.apps import apps
import logging
from infrastructure.storage.docker_volume_storage import DockerVolumeStorage
from core.services.experiment_service import ExperimentService

logger = logging.getLogger(__name__)

@shared_task(name="process_experiment_task", bind=True, max_retries=3)
def process_experiment_task(self, experiment_id):
    try:
        logger.info(f"Iniciando procesamiento para experimento {experiment_id}")
        
        service = ExperimentService(
            file_storage=DockerVolumeStorage(),
            video_processor=None  # No se necesita para el procesamiento real
        )
        
        result = service.process_experiment(experiment_id)
        logger.info(f"Procesamiento completado para experimento {experiment_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error procesando experimento {experiment_id}: {str(e)}")
        self.retry(exc=e, countdown=60)