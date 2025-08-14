from rest_framework import serializers
from core.models import Experiment, ExperimentObject, Clip
from django.db.models import Sum

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

class BaseExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = ['id', 'name', 'mouse_name', 'date', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class ExperimentObjectSerializer(serializers.ModelSerializer):
    label_display = serializers.CharField(source='get_label_display', read_only=True)
    time_object = serializers.FloatField(source='time', read_only=True)

    class Meta:
        model = ExperimentObject
        fields = ['id', 'reference', 'name', 'label', 'label_display', 'time_object']
        read_only_fields = ['id', 'time_object']

class ExperimentSerializer(BaseExperimentSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    experiment_objects = serializers.SerializerMethodField()

    class Meta(BaseExperimentSerializer.Meta):
        fields = BaseExperimentSerializer.Meta.fields + ['status_display', 'experiment_objects']

    def get_experiment_objects(self, obj):
        objects = ExperimentObject.objects.filter(experiment_id=obj.id)
        return ExperimentObjectSerializer(objects, many=True).data

class ExperimentDetailSerializer(ExperimentSerializer):
    clips = serializers.SerializerMethodField()
    total_exploration_time = serializers.SerializerMethodField()

    class Meta(ExperimentSerializer.Meta):
        fields = ExperimentSerializer.Meta.fields + ['clips', 'total_exploration_time']

    def get_clips(self, obj):
        clips = Clip.objects.filter(experiment_id=obj.id, valid=True)
        from api.serializers.clip_serializer import ClipBasicSerializer
        return ClipBasicSerializer(clips, many=True, context=self.context).data

    def get_total_exploration_time(self, obj):
        result = Clip.objects.filter(
            experiment_id=obj.id, 
            valid=True
        ).aggregate(total=Sum('duration'))
        return result['total'] or 0.0

class UploadExperimentSerializer(BaseExperimentSerializer):
    class Meta(BaseExperimentSerializer.Meta):
        fields = BaseExperimentSerializer.Meta.fields + ['video_file']
        extra_kwargs = {
            'video_file': {'required': True}
        }

class UpdateObjectLabelSerializer(serializers.Serializer, ExperimentObjectReferenceValidator):
    reference = serializers.IntegerField(min_value=1, max_value=2)
    label = serializers.ChoiceField(choices=ExperimentObject.Label.choices)
    new_name = serializers.CharField(required=False, max_length=100)

    def update(self, instance, validated_data):
        instance.label = validated_data['label']
        if 'new_name' in validated_data:
            instance.name = validated_data['new_name']
        instance.save()
        return instance