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

    class Meta:
        verbose_name = "Comportamiento"
        verbose_name_plural = "Comportamientos"
        ordering = ['name']

    @classmethod
    def create_defaults(cls):
        cls.objects.get_or_create(
            name='Exploración Novel',
            behavior_type='EXP',
            defaults={'description': 'Exploración de objeto nuevo'}
        )
        cls.objects.get_or_create(
            name='Exploración Familiar',
            behavior_type='EXP',
            defaults={'description': 'Exploración de objeto conocido'}
        )
        cls.objects.get_or_create(
            name='Interacción',
            behavior_type='INT',
            defaults={'description': 'Contacto físico con el objeto'}
        )

    def __str__(self):
        return f"{self.name} ({self.get_behavior_type_display()})"