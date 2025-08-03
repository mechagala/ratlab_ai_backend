# infrastructure/ai/celery_processor.py
from celery import shared_task

# Mueve el import DENTRO de la función para evitar circular imports
@shared_task
def process_experiment_task(experiment_id):
    from core.services.experiment_service import ExperimentService
    from infrastructure.storage.local_storage import LocalVideoStorage
    
    service = ExperimentService(
        storage=LocalVideoStorage()
    )
    service._process_experiment(experiment_id)  # Método interno

class CeleryVideoProcessor:
    def enqueue_processing(self, experiment_id):
        process_experiment_task.delay(experiment_id)