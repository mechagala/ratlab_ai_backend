from rest_framework import serializers
from core.models import Clip, Behavior, ExperimentObject

# Añade esto al inicio del archivo
class ExperimentObjectRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentObject
        fields = ['id', 'reference', 'label']

class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = ['id', 'name', 'description']
class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = ['id', 'name', 'description']

class ClipBasicSerializer(serializers.ModelSerializer):
    """Serializer mínimo para clips (usado en listados)"""
    behavior_name = serializers.CharField(source='behavior.name')
    object_label = serializers.CharField(source='experiment_object.label')
    object_time = serializers.FloatField(source='experiment_object.time')

    class Meta:
        model = Clip
        fields = [
            'id', 'duration', 'start_time', 'end_time',
            'behavior_name', 'object_label', 'object_time', 'video_url'
        ]
        read_only_fields = fields

class ClipSerializer(serializers.ModelSerializer):
    """Serializer completo para clips"""
    behavior = BehaviorSerializer(read_only=True)
    experiment_object = ExperimentObjectRefSerializer(read_only=True)
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Clip
        fields = [
            'id', 'experiment', 'start_time', 'end_time', 'duration',
            'behavior', 'experiment_object', 'video_url', 'valid'
        ]
        read_only_fields = ['id', 'duration', 'video_url']

    def get_video_url(self, obj):
        return obj.video_clip.url if obj.video_clip else None

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
        
        invalid_ids = set(value) - set(
            Clip.objects.filter(
                experiment_id=experiment_id
            ).values_list('id', flat=True)
        )
        if invalid_ids:
            raise serializers.ValidationError(
                f"IDs no válidos para este experimento: {invalid_ids}"
            )
        return value