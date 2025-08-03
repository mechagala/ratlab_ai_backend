from django.db import transaction
from core.models import Experiment, ExperimentObject, Status
from interfaces.ai.video_processor import VideoProcessor
from infrastructure.storage.docker_volume_storage import DockerVolumeStorage

class ExperimentService:
    def __init__(self, processor: VideoProcessor = None, storage=None):
        self.storage = storage or DockerVolumeStorage()
        self.processor = processor  # Requerido, sin valor por defecto aquí

    @classmethod
    def create_default(cls):
        """Factory method que resuelve la dependencia circular"""
        from infrastructure.ai.celery_processor import CeleryVideoProcessor
        return cls(processor=CeleryVideoProcessor())

    @transaction.atomic
    def create_experiment(self, user, name, mouse_name, date, video_file):
        """Crea un experimento y lo pone en cola para procesamiento"""
        # 1. Almacenar video
        video_path = self.storage.save(video_file)
        
        # 2. Crear experimento en la base de datos
        experiment = Experiment(
            user=user if user.is_authenticated else None,
            name=name,
            mouse_name=mouse_name,
            date=date,
            video_file=video_path,
            status=Status.UPLOADED
        )
        experiment.save()
        
        # 3. Crear objetos por defecto
        ExperimentObject.objects.bulk_create([
            ExperimentObject(
                experiment=experiment,
                reference=1,
                name="Objeto 1",
                label=ExperimentObject.Label.NOVEL,
                time=0.0
            ),
            ExperimentObject(
                experiment=experiment,
                reference=2,
                name="Objeto 2",
                label=ExperimentObject.Label.FAMILIAR,
                time=0.0
            )
        ])
        
        # 4. Poner en cola de procesamiento
        self.processor.enqueue_processing(experiment.id)
        
        return experiment