from abc import ABC, abstractmethod

class VideoProcessor(ABC):
    """Interfaz para procesamiento de videos con IA"""
    
    @abstractmethod
    def enqueue_processing(self, experiment_id: int):
        """Envía el experimento a la cola de procesamiento"""
        pass
