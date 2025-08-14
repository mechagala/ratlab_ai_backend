from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from core.services.experiment_service import ExperimentService
from infrastructure.storage.docker_volume_storage import DockerVolumeStorage
from infrastructure.ai.celery_adapter import CeleryVideoAdapter
from api.serializers.experiment_serializer import (
    UploadExperimentSerializer,
    ExperimentSerializer,
    ExperimentDetailSerializer,
    UpdateObjectLabelSerializer
)
from core.models import Experiment, Clip
import logging

logger = logging.getLogger(__name__)

class ExperimentUploadView(APIView):
    """Endpoint para subir nuevos experimentos (POST)"""
    parser_classes = [MultiPartParser]

    def post(self, request):
        try:
            service = ExperimentService(
                file_storage=DockerVolumeStorage(),
                video_processor=CeleryVideoAdapter()
            )
            
            experiment = service.create_experiment(
                name=request.data.get('name'),
                mouse_name=request.data.get('mouse_name'),
                date=request.data.get('date'),
                video_file=request.data.get('video_file')
            )
            
            return Response({
                "status": "success",
                "data": {
                    "experiment_id": experiment.id,
                    "status": experiment.status,
                    "task_status": "queued"
                }
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            logger.warning(f"Validación fallida: {str(e)}")
            return Response(
                {"status": "error", "errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creando experimento: {str(e)}", exc_info=True)
            return Response(
                {"status": "error", "message": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExperimentStatusView(APIView):
    """Endpoint para verificar estado de procesamiento (GET)"""
    def get(self, request, experiment_id):
        experiment = get_object_or_404(
            Experiment.objects.only('status'),
            id=experiment_id
        )
        
        # Contar clips manualmente usando experiment_id
        clips_count = Clip.objects.filter(experiment_id=experiment.id).count()
        
        return Response({
            "status": "success",
            "data": {
                "experiment_id": experiment.id,
                "processing_status": experiment.status,
                "clips_count": clips_count
            }
        })

class ExperimentDetailView(APIView):
    """Endpoint para detalle de experimento (GET)"""
    def get(self, request, experiment_id):
        experiment = get_object_or_404(
            Experiment.objects,  # Eliminado with_full_details() si usaba relaciones
            id=experiment_id
        )
        
        # Obtener datos relacionados manualmente
        experiment_data = {
            'experiment': experiment,
            'objects': experiment.experiment_objects.all(),  # Esto ahora sería un filter manual
            'clips': Clip.objects.filter(experiment_id=experiment.id)
        }
        
        serializer = ExperimentDetailSerializer(experiment_data)
        
        return Response({
            "status": "success",
            "data": serializer.data
        })

class UpdateObjectLabelView(APIView):
    """Endpoint para actualizar labels de objetos (PATCH)"""
    def patch(self, request, experiment_id):
        # Ahora necesitamos obtener el objeto directamente
        from core.models import ExperimentObject
        
        # Validar que el experimento existe
        get_object_or_404(Experiment, id=experiment_id)
        
        serializer = UpdateObjectLabelSerializer(
            data=request.data,
            context={'experiment_id': experiment_id}
        )
        
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ExperimentService(
                file_storage=DockerVolumeStorage(),
                video_processor=CeleryVideoAdapter()
            )
            
            # Obtener el objeto a actualizar
            obj = ExperimentObject.objects.get(
                experiment_id=experiment_id,
                reference=serializer.validated_data['reference']
            )
            
            updated_object = service.update_object_label(
                experiment_id=experiment_id,
                reference=serializer.validated_data['reference'],
                new_label=serializer.validated_data['label']
            )

            return Response({
                "status": "success",
                "data": {
                    "object_id": updated_object.id,
                    "new_label": updated_object.get_label_display()
                }
            })

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ExperimentObject.DoesNotExist:
            return Response(
                {"status": "error", "message": "Objeto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
class ExperimentListView(APIView):
    def get(self, request):
        queryset = Experiment.objects.all().order_by('-created_at')
        
        if name := request.query_params.get('name'):
            queryset = queryset.filter(name__iexact=name)

        serializer = ExperimentSerializer(queryset, many=True)
        
        # Opcional: Agregar datos relacionados si son necesarios
        response_data = []
        for exp in serializer.data:
            exp_data = dict(exp)
            exp_data['clips_count'] = Clip.objects.filter(experiment_id=exp['id']).count()
            response_data.append(exp_data)
            
        return Response({
            "status": "success",
            "data": response_data,
            "count": len(response_data)
        })