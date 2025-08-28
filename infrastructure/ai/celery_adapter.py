from interfaces.ai.video_processor import VideoProcessor
from core.tasks.experiment_tasks import process_experiment_task

class CeleryVideoAdapter(VideoProcessor):
    """Adaptador para procesamiento asíncrono con Celery"""
    
    def process(self, experiment_id: int) -> dict:
        # Enviar tarea a Celery
        task = process_experiment_task.delay(experiment_id)
        return {
            'task_id': task.id,
            'status': 'queued'
        }