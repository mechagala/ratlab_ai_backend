from rest_framework import serializers
from core.models import Clip, Behavior, ExperimentObject
import logging

logger = logging.getLogger(__name__)

class ExperimentObjectRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentObject
        fields = ['id', 'reference', 'label']

class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = ['id', 'name', 'description']

class ClipBasicSerializer(serializers.ModelSerializer):
    """Serializer mínimo para clips (usado en listados)"""
    behavior_name = serializers.SerializerMethodField()
    object_label = serializers.SerializerMethodField()
    object_time = serializers.SerializerMethodField()

    class Meta:
        model = Clip
        fields = [
            'id', 'duration', 'start_time', 'end_time',
            'behavior_name', 'object_label', 'object_time', 'video_url'
        ]
        read_only_fields = fields

    def get_behavior_name(self, obj):
        try:
            behavior = Behavior.objects.get(id=obj.behavior_id)
            return behavior.name
        except Behavior.DoesNotExist:
            return "Desconocido"

    def get_object_label(self, obj):
        if obj.experiment_object_id:
            try:
                exp_obj = ExperimentObject.objects.get(id=obj.experiment_object_id)
                return exp_obj.label
            except ExperimentObject.DoesNotExist:
                return None
        return None

    def get_object_time(self, obj):
        if obj.experiment_object_id:
            try:
                exp_obj = ExperimentObject.objects.get(id=obj.experiment_object_id)
                return exp_obj.time
            except ExperimentObject.DoesNotExist:
                return 0.0
        return 0.0

class ClipSerializer(serializers.ModelSerializer):
    """Serializer completo para clips"""
    behavior = serializers.SerializerMethodField()
    experiment_object = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()  # 🆕 agregado

    class Meta:
        model = Clip
        fields = [
            'id', 'experiment_id', 'start_time', 'end_time', 'duration',
            'behavior', 'experiment_object', 'video_url', 'thumbnail_url',  # 🆕 agregado
            'valid'
        ]
        read_only_fields = ['id', 'duration', 'video_url', 'thumbnail_url']

    def get_behavior(self, obj):
        try:
            logger.info(f"Fetching behavior for Clip id {obj.id} with behavior_id {obj.behavior_id}")
            behavior = Behavior.objects.get(id=obj.behavior_id)
            return BehaviorSerializer(behavior).data
        except Behavior.DoesNotExist:
            logger.info(f"Behavior with id {obj.behavior_id} does not exist.")
            return None

    def get_experiment_object(self, obj):
        if obj.experiment_object_id:
            try:
                exp_obj = ExperimentObject.objects.get(id=obj.experiment_object_id)
                return ExperimentObjectRefSerializer(exp_obj).data
            except ExperimentObject.DoesNotExist:
                return None
        return None

    def get_video_url(self, obj):
        return obj.video_clip.url if obj.video_clip else None

    def get_thumbnail_url(self, obj):
        """Devuelve la URL absoluta o relativa de la miniatura del clip"""
        if hasattr(obj, 'thumbnail') and obj.thumbnail:
            return obj.thumbnail.url
        return None


class ClipDeleteSerializer(serializers.Serializer):
    """Serializer para eliminación masiva de clips"""
    clip_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )

    def validate_clip_ids(self, value):
        experiment_id = self.context.get('experiment_id')
        if not experiment_id:
            raise serializers.ValidationError("experiment_id es requerido en el contexto")
        
        existing_ids = set(Clip.objects.filter(
            experiment_id=experiment_id
        ).values_list('id', flat=True))
        
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"IDs no válidos para este experimento: {invalid_ids}"
            )
        return value


class ClipValidationItemSerializer(serializers.Serializer):
    """Serializer para un item de validación de clip"""
    id = serializers.IntegerField()
    valid = serializers.BooleanField()


class ClipValidationUpdateSerializer(serializers.Serializer):
    """Serializer para actualización masiva de validación de clips"""
    clips = serializers.ListField(
        child=ClipValidationItemSerializer(),
        min_length=1,
        max_length=500
    )

    def validate_clips(self, value):
        experiment_id = self.context.get('experiment_id')
        if not experiment_id:
            raise serializers.ValidationError("experiment_id es requerido en el contexto")
        
        clip_ids = [item['id'] for item in value]
        existing_ids = set(Clip.objects.filter(
            experiment_id=experiment_id
        ).values_list('id', flat=True))
        
        invalid_ids = set(clip_ids) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"IDs de clips no válidos para este experimento: {invalid_ids}"
            )
        return value