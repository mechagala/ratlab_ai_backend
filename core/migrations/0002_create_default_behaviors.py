from django.db import migrations

def create_default_behaviors(apps, schema_editor):
    Behavior = apps.get_model('core', 'Behavior')
    
    default_behaviors = [
        {'name': 'Exploración', 'behavior_type': 'EXP', 'class_id': 0},
        {'name': 'Desplazamiento', 'behavior_type': 'OTH', 'class_id': 1},
        {'name': 'Acicalamiento', 'behavior_type': 'OTH', 'class_id': 2},
        {'name': 'Erguido', 'behavior_type': 'EXP', 'class_id': 3}
    ]
    
    for behavior_data in default_behaviors:
        Behavior.objects.get_or_create(
            class_id=behavior_data['class_id'],
            defaults=behavior_data
        )

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_behaviors),
    ]