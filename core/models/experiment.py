from django.db import models
from django.conf import settings
from core.models.user import User

class Status(models.TextChoices):
    UPLOADED = 'UPL', 'Video Subido'
    PROCESSING = 'PRO', 'Procesando'
    COMPLETED = 'COM', 'Completado'
    FAILED = 'ERR', 'Error'

class Experiment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Permite valores nulos
        blank=True  # Permite omitir en formularios/admin
    )
    ##user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    objects = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.mouse_name})"