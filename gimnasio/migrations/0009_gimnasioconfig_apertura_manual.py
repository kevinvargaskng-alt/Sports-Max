from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gimnasio', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gimnasioconfig',
            name='apertura_manual',
            field=models.BooleanField(
                default=False,
                help_text='Mantiene la sala abierta fuera del horario normal hasta que se cierre manualmente.',
            ),
        ),
    ]
