from django.db import models
from core.models.experiment import Experiment
from core.models.behavior import Behavior
from core.models.experiment_object import ExperimentObject

class Clip(models.Model):
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name='clips'
    )
    experiment_object = models.ForeignKey(
        ExperimentObject,
        on_delete=models.CASCADE,
        related_name='clips',
        help_text="Objeto asociado al clip (1 o 2)"
    )
    video_clip = models.FileField(upload_to='experiments/clips/')
    duration = models.FloatField(
        help_text="Duración en segundos (calculada como end_time - start_time)"
    )
    behavior = models.ForeignKey(
        Behavior,
        on_delete=models.PROTECT,
        related_name='clips'
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
        ordering = ['experiment', 'start_time']
        indexes = [
            models.Index(fields=['experiment', 'valid']),
            models.Index(fields=['behavior']),
        ]

    def clean(self):
        if self.experiment_object.reference not in [1, 2]:
            raise ValidationError("La referencia del objeto debe ser 1 o 2")

    def save(self, *args, **kwargs):
        self.clean()  # Ejecuta validaciones
        if self.end_time is not None:
            self.duration = round(self.end_time - self.start_time, 2)
        super().save(*args, **kwargs)
