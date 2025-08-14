from interfaces.ai.video_processor import VideoProcessor
from core.tasks.experiment_tasks import process_experiment_task

class CeleryVideoAdapter(VideoProcessor):
    """Implementación concreta para Celery"""
    def process(self, experiment_id: int) -> dict:
        task = process_experiment_task.delay(experiment_id)
        return {
            'task_id': task.id,
            'status': 'queued'
        }