# api/serializers/__init__.py
from .auth_serializer import LoginSerializer
from .experiment_serializer import (
    ExperimentSerializer,
    ExperimentDetailSerializer,
    UploadExperimentSerializer,
    UpdateObjectLabelSerializer,
    ExperimentObjectSerializer  # Asegúrate que esté exportado desde experiment_serializer.py
)
from .clip_serializer import (
    ClipSerializer,
    ClipBasicSerializer,
    ClipDeleteSerializer,
    BehaviorSerializer,
    ExperimentObjectRefSerializer  # Añade esta línea
)
from .auth_serializer import (UserSerializer, LoginSerializer)  # Asegúrate de que tu serializer de usuario esté importado 

__all__ = [
    'LoginSerializer',
    'ExperimentSerializer',
    'ExperimentDetailSerializer',
    'UploadExperimentSerializer',
    'UpdateObjectLabelSerializer',
    'ExperimentObjectSerializer',
    'ClipSerializer',
    'ClipBasicSerializer',
    'ClipDeleteSerializer',
    'BehaviorSerializer',
    'ExperimentObjectRefSerializer',
    'UserSerializer' # Añade esta línea
]