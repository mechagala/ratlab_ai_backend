from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    institution = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'custom_user'  # Evita conflicto con auth_user
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.username}"