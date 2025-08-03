from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Usuario personalizado para autenticación"""
    institution = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.email})"