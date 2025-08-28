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
    clips_count = serializers.SerializerMethodField()

    class Meta(BaseExperimentSerializer.Meta):
        fields = BaseExperimentSerializer.Meta.fields + [
            'status_display', 
            'experiment_objects',
            'clips_count'
        ]

    def get_experiment_objects(self, obj):
        from core.models import ExperimentObject, Clip, Behavior
        
        # Solo procesar si el experimento está completado
        if obj.status != 'COM':
            return []
            
        objects = ExperimentObject.objects.filter(experiment_id=obj.id)
        objects_data = []
        
        for obj in objects:
            # Calcular tiempo total de exploración (clips válidos con behavior_type = 'EXP')
            total_time = Clip.objects.filter(
                experiment_id=obj.experiment_id,
                experiment_object_id=obj.id,
                valid=True,
                behavior_id__in=Behavior.objects.filter(
                    behavior_type='EXP'
                ).values_list('id', flat=True)
            ).aggregate(total=Sum('duration'))['total'] or 0.0
            
            objects_data.append({
                "id": obj.id,
                "reference": obj.reference,
                "name": obj.name,
                "label": obj.label,
                "label_display": obj.get_label_display(),
                "time_object": round(total_time, 2)
            })
            
        return objects_data

    def get_clips_count(self, obj):
        from core.models import Clip
        return Clip.objects.filter(experiment_id=obj.id).count()

class ClipBasicSerializer(serializers.ModelSerializer):
    behavior_name = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()

    class Meta:
        model = Clip
        fields = [
            'id', 'video_clip', 'duration', 'start_time', 'end_time',
            'behavior_id', 'behavior_name', 'experiment_object_id', 'object_name'
        ]
        read_only_fields = fields

    def get_behavior_name(self, obj):
        if obj.behavior_id:
            from core.models import Behavior
            behavior = Behavior.objects.filter(id=obj.behavior_id).first()
            return behavior.name if behavior else None
        return None

    def get_object_name(self, obj):
        if obj.experiment_object_id:
            from core.models import ExperimentObject
            obj = ExperimentObject.objects.filter(id=obj.experiment_object_id).first()
            return obj.name if obj else None
        return None

class ExperimentObjectWithClipsSerializer(serializers.ModelSerializer):
    label_display = serializers.CharField(source='get_label_display', read_only=True)
    clips = serializers.SerializerMethodField()
    total_exploration_time = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentObject
        fields = [
            'id', 'name', 'reference', 'label', 'label_display', 
            'time', 'clips', 'total_exploration_time'
        ]
        read_only_fields = fields

    def get_clips(self, obj):
        from core.models import Clip
        clips = Clip.objects.filter(
            experiment_id=obj.experiment_id,
            experiment_object_id=obj.id,
            valid=True
        )
        return ClipBasicSerializer(clips, many=True).data

    def get_total_exploration_time(self, obj):
        from core.models import Clip, Behavior
        total = Clip.objects.filter(
            experiment_id=obj.experiment_id,
            experiment_object_id=obj.id,
            valid=True,
            behavior_id__in=Behavior.objects.filter(
                behavior_type='EXP'
            ).values_list('id', flat=True)
        ).aggregate(total=Sum('duration'))['total']
        return round(total, 2) if total else 0.0

class ExperimentDetailSerializer(serializers.ModelSerializer):
    objects = ExperimentObjectWithClipsSerializer(
        many=True,
        source='experimentobject_set',
        read_only=True
    )
    total_exploration_time = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Experiment
        fields = [
            'id', 'name', 'mouse_name', 'date', 'video_file',
            'status', 'status_display', 'created_at',
            'objects', 'total_exploration_time'
        ]
        read_only_fields = fields

    def get_total_exploration_time(self, obj):
        from core.models import Clip, Behavior
        total = Clip.objects.filter(
            experiment_id=obj.id,
            valid=True,
            behavior_id__in=Behavior.objects.filter(
                behavior_type='EXP'
            ).values_list('id', flat=True)
        ).aggregate(total=Sum('duration'))['total']
        return round(total, 2) if total else 0.0

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