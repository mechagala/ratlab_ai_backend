from celery import shared_task
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

@shared_task(name="core.tasks.experiment_tasks.process_experiment_task" ,bind=True, max_retries=3)
def process_experiment_task(self, experiment_id):
    """Tarea Celery limpia (solo orquesta servicios)"""
    from core.models import Experiment  # Importación local
    try:
        Experiment = apps.get_model('core', 'Experiment')
        ExperimentService = apps.get_model('core.services', 'ExperimentService')
        
        service = ExperimentService.create_default()
        return service.process_experiment(experiment_id)
    except Exception as e:
        self.retry(exc=e)

        