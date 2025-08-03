from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Experiment, ExperimentObject, Clip, Behavior

class Command(BaseCommand):
    help = 'Crea datos de prueba para la API'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Crear usuario
        user, _ = User.objects.get_or_create(
            username='investigador1',
            defaults={
                'email': 'investigador2@lab.com',
                'password': 'password1234',
                'institution': 'Laboratorio Neurociencias',
                'department': 'Cognición'
            }
        )
        
        # Comportamientos
        exploration, _ = Behavior.objects.get_or_create(
            name='Exploración Novel',
            behavior_type='EXP',
            defaults={'description': 'Exploración de objeto nuevo'}
        )
        interaction, _ = Behavior.objects.get_or_create(
            name='Interacción',
            behavior_type='INT',
            defaults={'description': 'Contacto físico con el objeto'}
        )

        # Crear experimento
        # experiment = Experiment.objects.create(
        #     user=user,
        #     name='Experimento Memoria Objetos',
        #     mouse_name='Rata-001',
        #     video_file='experiments/dummy.mp4',
        #     date=timezone.now().date(),
        #     status='completed'
        # )

        experiment = Experiment(
            user=user,
            name='Experimento Memoria Objetos Rata 2',
            mouse_name='Rata-002',
            date=timezone.now().date(),
            video_file='experiments/dummy.mp4',  # Required field
            status='completed'
        )
        experiment.save()

        # Objetos del experimento
        obj1 = ExperimentObject.objects.create(
            experiment=experiment,
            reference=1,
            name='Objeto Nuevo',
            label='NOV',
            time=15.2
        )
        obj2 = ExperimentObject.objects.create(
            experiment=experiment,
            reference=2,
            name='Objeto Familiar',
            label='FAM',
            time=8.7
        )

        # Clips
        Clip.objects.create(
            experiment=experiment,
            experiment_object=obj1,
            behavior=exploration,
            start_time=5.3,
            end_time=8.1,
            duration=2.8,
            valid=True
        )
        Clip.objects.create(
            experiment=experiment,
            experiment_object=obj2,
            behavior=interaction,
            start_time=12.5,
            end_time=14.3,
            duration=1.8,
            valid=True
        )

        self.stdout.write(self.style.SUCCESS('✅ Datos creados exitosamente'))
        self.stdout.write(f'Usuario: investigador1 / password123')
        self.stdout.write(f'Experiment ID: {experiment.id}')