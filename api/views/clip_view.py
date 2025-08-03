from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Clip
from api.serializers import ClipDeleteSerializer

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