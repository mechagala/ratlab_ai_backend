from django.db import models
from django.core.exceptions import ValidationError

class ExperimentObject(models.Model):
    class Reference(models.IntegerChoices):
        OBJECT_1 = 1, 'Objeto 1'
        OBJECT_2 = 2, 'Objeto 2'
    
    class Label(models.TextChoices):
        NOVEL = 'NOV', 'Novel'
        FAMILIAR = 'FAM', 'Familiar'

    # Reemplazado ForeignKey con IntegerField
    experiment_id = models.IntegerField(help_text="ID del experimento relacionado")
    
    name = models.CharField(max_length=100)
    reference = models.IntegerField(
        choices=Reference.choices,
        help_text="Referencia numérica del objeto (1 o 2)"
    )
    label = models.CharField(
        max_length=3,
        choices=Label.choices,
        null=True,
        blank=True,
        help_text="Tipo de objeto (Novel o Familiar)"
    )
    time = models.FloatField(
        default=0.0,
        help_text="Tiempo total de exploración en segundos"
    )

    class Meta:
        verbose_name = "Objeto de Experimento"
        verbose_name_plural = "Objetos de Experimento"
        ordering = ['experiment_id', 'reference']
        constraints = [
            models.UniqueConstraint(
                fields=['experiment_id', 'reference'],
                name='unique_object_reference_per_experiment'
            )
        ]

    def clean(self):
        """Validaciones a nivel de aplicación"""
        if self.reference not in [1, 2]:
            raise ValidationError({
                'reference': 'La referencia debe ser 1 (Objeto 1) o 2 (Objeto 2)'
            })
        
        if self.label == self.Label.NOVEL and self.reference != 1:
            raise ValidationError({
                'label': 'El objeto Novel debe ser la referencia 1'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        label_display = self.get_label_display() if self.label else "Sin etiqueta"
        return f"{self.name} (Ref: {self.reference}, {label_display})"