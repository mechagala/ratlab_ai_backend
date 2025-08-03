# infrastructure/ai/celery_processor.py
from celery import shared_task
from interfaces.ai.video_processor import VideoProcessor

class CeleryVideoProcessor(VideoProcessor):
    def enqueue_processing(self, experiment_id):
        process_experiment_task.delay(experiment_id)

@shared_task(bind=True)
def process_experiment_task(self, experiment_id):
    """Task que contiene TODA la lógica de procesamiento"""
    from core.models import Experiment
    from core.services.experiment_service import ExperimentService
    
    try:
        experiment = Experiment.objects.get(id=experiment_id)
        # Aquí va toda tu lógica de procesamiento:
        # 1. Procesar video con IA
        # 2. Actualizar estado del experimento
        # 3. Guardar resultados
        experiment.status = Status.COMPLETED
        experiment.save()
    except Exception as e:
        experiment.status = Status.FAILED
        experiment.save()
        raise self.retry(exc=e, countdown=60)