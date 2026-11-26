# Generated manually to remove EquipoInterfichas.planilla_inscripcion

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interfichas', '0006_equipointerfichas_escudo_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipointerfichas',
            name='planilla_inscripcion',
        ),
    ]
