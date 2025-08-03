from rest_framework import serializers
from core.models import Experiment, ExperimentObject, Clip
from django.db.models import Sum, Prefetch

# ----------------------------
# Mixin para validación común
# ----------------------------
class ExperimentObjectReferenceValidator:
    """Valida que la referencia del objeto sea única por experimento"""
    def validate_reference(self, value):
        experiment_id = self.context.get('experiment_id')
        if not experiment_id:
            raise serializers.ValidationError("Se requiere experiment_id en el contexto")
        
        if ExperimentObject.objects.filter(
            experiment_id=experiment_id,
            reference=value
        ).exists():
            raise serializers.ValidationError(
                f"Ya existe un objeto con referencia {value} en este experimento"
            )
        return value

# ----------------------------
# Serializers principales
# ----------------------------
class BaseExperimentSerializer(serializers.ModelSerializer):
    """Serializer base para Experimentos (evita duplicación)"""
    class Meta:
        model = Experiment
        fields = ['id', 'name', 'mouse_name', 'date', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

class ExperimentObjectSerializer(serializers.ModelSerializer):
    """Serializer para objetos de experimento (Object1/Object2)"""
    label_display = serializers.CharField(source='get_label_display', read_only=True)
    time_object = serializers.FloatField(source='time')  # Renombrado a time_object

    class Meta:
        model = ExperimentObject
        fields = ['id', 'reference', 'name', 'label', 'label_display', 'time_object']
        read_only_fields = ['id', 'time_object']

class ExperimentSerializer(BaseExperimentSerializer):
    """Serializer para listado de experimentos"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    objects = ExperimentObjectSerializer(many=True, read_only=True)

    class Meta(BaseExperimentSerializer.Meta):
        fields = BaseExperimentSerializer.Meta.fields + ['status_display', 'objects']

class ExperimentDetailSerializer(ExperimentSerializer):
    """Serializer extendido para detalle de experimento"""
    clips = serializers.SerializerMethodField()
    total_exploration_time = serializers.SerializerMethodField()

    class Meta(ExperimentSerializer.Meta):
        fields = ExperimentSerializer.Meta.fields + ['clips', 'total_exploration_time']

    def get_clips(self, obj):
        return ClipBasicSerializer(
            obj.clips.filter(valid=True),
            many=True,
            context=self.context
        ).data

    def get_total_exploration_time(self, obj):
        return obj.clips.filter(valid=True).aggregate(
            total=Sum('duration')
        )['total'] or 0.0

class UploadExperimentSerializer(BaseExperimentSerializer):
    """Serializer específico para upload de experimentos"""
    class Meta(BaseExperimentSerializer.Meta):
        fields = BaseExperimentSerializer.Meta.fields + ['video_file']
        extra_kwargs = {'video_file': {'required': True}}

class UpdateObjectLabelSerializer(serializers.Serializer, ExperimentObjectReferenceValidator):
    """Serializer para actualizar labels de objetos"""
    reference = serializers.IntegerField(min_value=1, max_value=2)
    label = serializers.ChoiceField(choices=ExperimentObject.Label.choices)
    new_name = serializers.CharField(required=False, max_length=100)

    def update(self, instance, validated_data):
        instance.label = validated_data['label']
        if 'new_name' in validated_data:
            instance.name = validated_data['new_name']
        instance.save()
        return instance