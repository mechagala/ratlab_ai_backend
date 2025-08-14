# core/models/__init__.py
from .experiment import Experiment, Status
from .experiment_object import ExperimentObject
from .clip import Clip
from .behavior import Behavior
from .user import User  # Asegúrate de que tu modelo User esté importado

__all__ = ['Experiment', 'ExperimentObject', 'Status', 'Clip', 'Behavior','User']