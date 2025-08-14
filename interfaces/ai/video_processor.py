from abc import ABC, abstractmethod

class VideoProcessor(ABC):
    """Contrato para procesamiento de video"""
    @abstractmethod
    def process(self, experiment_id: int) -> dict:
        """Procesa un experimento y devuelve metadata"""
        raise NotImplementedError