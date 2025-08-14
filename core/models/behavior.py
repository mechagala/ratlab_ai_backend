from django.db import models

class Behavior(models.Model):
    class BehaviorType(models.TextChoices):
        EXPLORATION = 'EXP', 'Exploración'
        INTERACTION = 'INT', 'Interacción'
        OTHER = 'OTH', 'Otro'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    behavior_type = models.CharField(
        max_length=3,
        choices=BehaviorType.choices,
        default=BehaviorType.EXPLORATION,
        help_text="Tipo general de comportamiento"
    )
    class_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="ID de clase correspondiente en el modelo de ML"
    )

    class Meta:
        verbose_name = "Comportamiento"
        verbose_name_plural = "Comportamientos"
        ordering = ['class_id']

    def __str__(self):
        return f"{self.name} (Clase {self.class_id})"