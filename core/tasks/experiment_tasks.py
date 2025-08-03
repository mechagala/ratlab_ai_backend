from celery import shared_task
from core.services.experiment_service import ExperimentService

@shared_task(bind=True, max_retries=3)
def process_experiment_task(self, experiment_id: int):
    """Tarea Celery que ejecuta el procesamiento real"""
    try:
        service = ExperimentService()
        service.process_experiment(experiment_id)
    except Exception as e:
        self.retry(exc=e, countdown=60)
