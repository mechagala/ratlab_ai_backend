from django.core.exceptions import ValidationError
import logging
from django.apps import apps

logger = logging.getLogger(__name__)

class ExperimentService:
    def __init__(self, file_storage, video_processor):
        self.storage = file_storage
        self.processor = video_processor

    def create_experiment(self, name, mouse_name, date, video_file):
        """Crea un nuevo experimento sin usar relaciones ForeignKey"""
        try:
            Experiment = apps.get_model('core', 'Experiment')
            
            if not all([name, mouse_name, date, video_file]):
                raise ValidationError("Todos los campos son requeridos")
            
            file_path = self.storage.save(video_file)
            
            experiment = Experiment(
                name=name,
                mouse_name=mouse_name,
                date=date,
                video_file=file_path,
                status='UPL'
            )
            experiment.save()
            
            # Procesar el video usando el ID del experimento
            self.processor.process(experiment.id)
            return experiment
            
        except Exception as e:
            logger.error(f"Error creando experimento: {str(e)}", exc_info=True)
            raise

    def update_object_label(self, experiment_id, reference, new_label):
        """Actualiza el label de un objeto de experimento"""
        try:
            ExperimentObject = apps.get_model('core', 'ExperimentObject')
            
            # Obtener el objeto por experiment_id y reference
            obj = ExperimentObject.objects.get(
                experiment_id=experiment_id,
                reference=reference
            )
            
            obj.label = new_label
            obj.save()
            return obj
            
        except ExperimentObject.DoesNotExist:
            raise ValueError(f"No se encontró objeto con referencia {reference} para el experimento {experiment_id}")
        except Exception as e:
            logger.error(f"Error actualizando label: {str(e)}")
            raise