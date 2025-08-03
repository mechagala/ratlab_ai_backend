from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from django.shortcuts import get_object_or_404
from core.models import Experiment, ExperimentObject, Clip
from core.services.experiment_service import ExperimentService
from api.serializers import (
    UploadExperimentSerializer,
    ExperimentSerializer,
    ExperimentDetailSerializer,
    UpdateObjectLabelSerializer
)

class ExperimentUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = UploadExperimentSerializer(
            data=request.data,
            context={'user': request.user}
        )
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=400)

        service = ExperimentService()
        experiment = service.create_experiment(
            user=request.user,
            name=serializer.validated_data['name'],
            mouse_name=serializer.validated_data['mouse_name'],
            date=serializer.validated_data['date'],
            video_file=serializer.validated_data['video_file']
        )

        return Response({
            "status": "success",
            "data": {
                "experiment_id": experiment.id,
                "objects_created": True
            }
        }, status=201)

# Previous status -> before queues implementation
# class ExperimentUploadView(APIView):
#     """Endpoint para subir nuevos experimentos (POST)"""
#     parser_classes = [MultiPartParser]

#     @transaction.atomic
#     def post(self, request):
#         serializer = UploadExperimentSerializer(
#             data=request.data,
#             context={'user': request.user}
#         )
#         if not serializer.is_valid():
#             return Response(
#                 {"status": "error", "errors": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         experiment = serializer.save()

#         # Creación de objetos por defecto
#         ExperimentObject.objects.bulk_create([
#             ExperimentObject(
#                 experiment=experiment,
#                 reference=1,
#                 name="Objeto 1",
#                 label=ExperimentObject.Label.NOVEL,
#                 time=0.0
#             ),
#             ExperimentObject(
#                 experiment=experiment,
#                 reference=2,
#                 name="Objeto 2",
#                 label=ExperimentObject.Label.FAMILIAR,
#                 time=0.0
#             )
#         ])

#         return Response({
#             "status": "success",
#             "data": {
#                 "experiment_id": experiment.id,
#                 "objects_created": True
#             }
#         }, status=status.HTTP_201_CREATED)

class ExperimentListView(APIView):
    """Endpoint para listar experimentos (GET)"""
    def get(self, request):
        manager = Experiment._meta.default_manager
        queryset = manager.select_related('user').prefetch_related(
            'objects', 'clips'
        ).order_by('-created_at')

        # Filtrado opcional
        if name := request.query_params.get('name'):
            queryset = queryset.filter(name__iexact=name)

        serializer = ExperimentSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data,
            "count": queryset.count()
        })

class ExperimentDetailView(APIView):
    """Endpoint para detalle de experimento (GET)"""
    def get(self, request, experiment_id):
        experiment = get_object_or_404(
            Experiment.objects.prefetch_related(
                'objects', 
                'clips__behavior', 
                'clips__experiment_object'
            ),
            id=experiment_id
        )
        serializer = ExperimentDetailSerializer(experiment)
        return Response({
            "status": "success",
            "data": serializer.data
        })

class UpdateObjectLabelView(APIView):
    """Endpoint para actualizar labels de objetos (PATCH)"""
    @transaction.atomic
    def patch(self, request, experiment_id):
        experiment = get_object_or_404(Experiment, id=experiment_id)
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
            obj = experiment.objects.get(
                reference=serializer.validated_data['reference']
            )
            serializer.update(obj, serializer.validated_data)
            return Response({
                "status": "success",
                "data": {
                    "object_updated": obj.reference,
                    "new_label": obj.label
                }
            })
        except ExperimentObject.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Object not found for this experiment"
            }, status=status.HTTP_404_NOT_FOUND)