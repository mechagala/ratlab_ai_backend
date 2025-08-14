from django.db import models

class Status(models.TextChoices):
    UPLOADED = 'UPL', 'Video Subido'
    PROCESSING = 'PRO', 'Procesando'
    COMPLETED = 'COM', 'Completado'
    FAILED = 'ERR', 'Error'

class Experiment(models.Model):
    name = models.CharField(max_length=255)
    mouse_name = models.CharField(max_length=100)
    date = models.DateField()
    video_file = models.FileField(upload_to='experiments/')
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.UPLOADED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Eliminado el manager personalizado ya que no es necesario

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Experimento"
        verbose_name_plural = "Experimentos"

    def __str__(self):
        return f"{self.name} ({self.mouse_name})"