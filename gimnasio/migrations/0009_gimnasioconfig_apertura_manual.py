from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gimnasio', '0008_franjahoraria_alter_machine_options_and_more'),
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
