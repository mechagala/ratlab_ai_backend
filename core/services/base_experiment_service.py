# core/services/base_experiment_service.py (NUEVO ARCHIVO)
from abc import ABC, abstractmethod

class BaseExperimentService(ABC):
    @abstractmethod
    def create_experiment(self, user, video_file):
        pass