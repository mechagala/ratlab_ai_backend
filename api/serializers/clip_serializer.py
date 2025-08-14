from rest_framework import serializers
from core.models import Clip, Behavior, ExperimentObject

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

    class Meta:
        model = Clip
        fields = [
            'id', 'experiment_id', 'start_time', 'end_time', 'duration',
            'behavior', 'experiment_object', 'video_url', 'valid'
        ]
        read_only_fields = ['id', 'duration', 'video_url']

    def get_behavior(self, obj):
        try:
            behavior = Behavior.objects.get(id=obj.behavior_id)
            return BehaviorSerializer(behavior).data
        except Behavior.DoesNotExist:
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