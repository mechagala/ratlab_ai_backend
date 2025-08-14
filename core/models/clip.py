from django.db import models
from django.core.exceptions import ValidationError

class Clip(models.Model):
    # Reemplazados todos los ForeignKey con IntegerField
    experiment_id = models.IntegerField(help_text="ID del experimento relacionado")
    experiment_object_id = models.IntegerField(
        help_text="ID del objeto asociado al clip",
        null=True,
        blank=True
    )
    
    # En tu modelo Clip (clip.py)
    behavior_id = models.IntegerField(
        help_text="ID del comportamiento asociado",
        null=True,
        blank=True
    )
    
    video_clip = models.FileField(upload_to='experiments/clips/')
    duration = models.FloatField(
        help_text="Duración en segundos (calculada como end_time - start_time)"
    )
    valid = models.BooleanField(
        default=True,
        help_text="Clip validado manualmente"
    )
    start_time = models.FloatField(
        help_text="Tiempo de inicio en el video original (segundos)"
    )
    end_time = models.FloatField(
        help_text="Tiempo de finalización en el video original (segundos)",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Clip de Comportamiento"
        verbose_name_plural = "Clips de Comportamiento"
        ordering = ['experiment_id', 'start_time']
        indexes = [
            models.Index(fields=['experiment_id', 'valid']),
            models.Index(fields=['behavior_id']),
        ]

    def clean(self):
        """Validación manual de la referencia del objeto"""
        # Nota: Ahora necesitarías obtener el objeto para validar la referencia
        # Esto es menos eficiente que con ForeignKey
        if self.experiment_object_id:
            from .experiment_object import ExperimentObject
            obj = ExperimentObject.objects.filter(id=self.experiment_object_id).first()
            if obj and obj.reference not in [1, 2]:
                raise ValidationError("La referencia del objeto debe ser 1 o 2")

    def save(self, *args, **kwargs):
        self.clean()
        if self.end_time is not None:
            self.duration = round(self.end_time - self.start_time, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Clip {self.id} (Exp: {self.experiment_id})"