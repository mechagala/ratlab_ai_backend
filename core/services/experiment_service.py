from django.core.exceptions import ValidationError
import logging
from django.apps import apps
from django.core.files.storage import default_storage
from core.services.video_processing import VideoProcessingService
from config import settings

logger = logging.getLogger(__name__)

class ExperimentService:
    def __init__(self, file_storage, video_processor):
        self.storage = file_storage
        self.processor = video_processor
        self.video_processing = VideoProcessingService(
            model_path=settings.VIDEO_PIPELINE_MODEL_PATH,
            segmenter_path=settings.VIDEO_PIPELINE_SEGMENTER_PATH
        )

    def create_experiment(self, name, mouse_name, date, video_file):
        """Crea y procesa un nuevo experimento"""
        try:
            Experiment = apps.get_model('core', 'Experiment')
            
            if not all([name, mouse_name, date, video_file]):
                raise ValidationError("Todos los campos son requeridos")
            
            # 1. Guardar video en storage
            file_path = self.storage.save(video_file)
            #full_video_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # 2. Crear registro de experimento
            experiment = Experiment(
                name=name,
                mouse_name=mouse_name,
                date=date,
                video_file=file_path,
                status='UPL'
            )
            experiment.save()
            
            # 3. Procesar video de forma asíncrona
            self.processor.process(experiment.id)
            
            return experiment
            
        except Exception as e:
            logger.error(f"Error creando experimento: {str(e)}", exc_info=True)
            raise

    def process_experiment(self, experiment_id):
        """Procesa un experimento completo"""
        Experiment = apps.get_model('core', 'Experiment')
        experiment = Experiment.objects.get(id=experiment_id)
        
        try:
            # 1. Actualizar estado
            experiment.status = 'PRO'
            experiment.save()
            
            # 2. Obtener ruta del video
            video_path = experiment.video_file.path
            
            # 3. Procesar video
            processing_result = self.video_processing.process(
                video_path=video_path,
                experiment_id=experiment_id
            )
            
            # 4. Actualizar estado
            experiment.status = 'COM'
            experiment.save()
            
            return processing_result
            
        except Exception as e:
            experiment.status = 'ERR'
            experiment.save()
            logger.error(f"Error procesando experimento {experiment_id}: {str(e)}")
            raise