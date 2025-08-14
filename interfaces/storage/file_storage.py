from abc import ABC, abstractmethod

class FileStorage(ABC):
    """Contrato para almacenamiento de archivos"""
    @abstractmethod
    def save(self, file) -> str:
        """Guarda un archivo y devuelve ruta relativa"""
        raise NotImplementedError