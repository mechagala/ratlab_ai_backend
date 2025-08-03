from django.db import transaction
from core.models import Experiment, ExperimentObject
from interfaces.ai.video_processor import VideoProcessor
from infrastructure.storage.docker_volume_storage import DockerVolumeStorage  # Import directo, no factory

class ExperimentService:
    def __init__(self, processor=None, storage=None):
        self.storage = storage or LocalVideoStorage()  # Usa implementación directa
        self.processor = processor or VideoProcessor()  # Interfaz, no implementación

    @transaction.atomic
    def create_experiment(self, user, name, mouse_name, date, video_file):
        """Reemplaza la lógica actual de tu vista"""
        # 1. Almacenar video
        video_path = self.storage.save(video_file)
        
        # 2. Crear experimento (igual a tu lógica actual)
        experiment = Experiment.objects.create(
            user=user,
            name=name,
            mouse_name=mouse_name,
            date=date,
            video_file=video_path,
            status='UPL'  # Usar el Status que añadiremos al modelo
        )
        
        # 3. Objetos por defecto (igual a tu vista actual)
        ExperimentObject.objects.bulk_create([
            ExperimentObject(experiment=experiment, reference=1, name="Objeto 1", label="NOVEL", time=0.0),
            ExperimentObject(experiment=experiment, reference=2, name="Objeto 2", label="FAMILIAR", time=0.0)
        ])
        
        # 4. Procesamiento async (nuevo)
        self.processor.enqueue_processing(experiment.id)

        return experiment
