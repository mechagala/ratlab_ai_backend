from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Clip
from api.serializers import ClipDeleteSerializer, ClipValidationUpdateSerializer


class ClipDeleteView(APIView):
    """Endpoint para eliminar múltiples clips (POST)"""
    def post(self, request, experiment_id):
        serializer = ClipDeleteSerializer(
            data=request.data,
            context={'experiment_id': experiment_id}
        )
        
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizado para usar el manager estándar y filter por experiment_id
        deleted_count, _ = Clip.objects.filter(
            id__in=serializer.validated_data['clip_ids'],
            experiment_id=experiment_id
        ).delete()

        return Response({
            "status": "success",
            "data": {
                "deleted_clips": deleted_count,
                "experiment_id": experiment_id
            }
        })


class ClipValidationUpdateView(APIView):
    """Endpoint para actualizar validación de múltiples clips (PATCH)"""
    def patch(self, request, experiment_id):
        serializer = ClipValidationUpdateSerializer(
            data=request.data,
            context={'experiment_id': experiment_id}
        )
        
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        clips_data = serializer.validated_data['clips']
        updated_count = 0
        
        for clip_item in clips_data:
            updated = Clip.objects.filter(
                id=clip_item['id'],
                experiment_id=experiment_id
            ).update(valid=clip_item['valid'])
            updated_count += updated

        return Response({
            "status": "success",
            "data": {
                "updated_clips": updated_count,
                "experiment_id": experiment_id
            }
        })