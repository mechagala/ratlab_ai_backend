from abc import ABC, abstractmethod

class VideoStorage(ABC):
    @abstractmethod
    def save(self, video_file) -> str:
        """Returns path where video was saved"""
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        """Returns accessible video URL"""
        pass