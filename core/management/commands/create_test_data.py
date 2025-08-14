from django.core.management.base import BaseCommand
from core.models.experiment import Experiment
from core.models.experiment_object import ExperimentObject
from core.models.clip import Clip
from core.models.behavior import Behavior
from core.models.user import User
from django.core.files import File
import os
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Crea datos de prueba para experimentos'

    def handle(self, *args, **options):
        # Comportamientos ya deberían existir por la migración 0002
        behaviors = Behavior.objects.all()
        if not behaviors.exists():
            self.stdout.write(self.style.ERROR('No hay comportamientos en la base de datos. Ejecuta las migraciones primero.'))
            return

        # Nombres de ratones de prueba
        mouse_names = ['M001', 'M002', 'M003', 'M004', 'M005']

        # Crear 5 experimentos de prueba
        for i in range(1, 6):
            exp = Experiment.objects.create(
                name=f"Experimento_{i}",
                mouse_name=random.choice(mouse_names),
                date=date.today() - timedelta(days=i),
                status=random.choice(['UPL', 'PRO', 'COM', 'ERR']),
                video_file='experiments/dummy_video.mp4'  # Necesitas un archivo dummy o manejar esto diferente
            )

            # Crear objetos para el experimento (Objeto 1 y 2)
            for ref in [1, 2]:
                obj = ExperimentObject.objects.create(
                    experiment_id=exp.id,  # Usamos el ID directamente
                    reference=ref,
                    name=f"Objeto_{ref}",
                    label='NOV' if ref == 1 else 'FAM',
                    time=random.uniform(10.0, 60.0)
                )

                # Crear 3-5 clips por objeto
                for clip_num in range(1, random.randint(3, 6)):
                    Clip.objects.create(
                        experiment_id=exp.id,
                        experiment_object_id=obj.id,
                        behavior_id=random.choice(behaviors).id,
                        start_time=random.uniform(0, 300),
                        end_time=random.uniform(5, 305),
                        duration=random.uniform(5, 30),
                        valid=random.choice([True, False]),
                        video_clip='experiments/clips/dummy_clip.mp4'  # Archivo dummy
                    )

            self.stdout.write(f'Creado experimento {exp.name} con ID {exp.id}')

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados exitosamente!'))