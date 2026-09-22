import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.db import connection


TABLAS_OBJETIVO = {
    "interfichas_estadisticajugador",
    "gimnasio_rutinagimnasio",
    "historial_acciones",
    "habitos_saludables_recetasaludable",
    "habitos_saludables_registrohabitousuario",
    "habitos_saludables_registrosueno",
    "habitos_saludables_suscripcionpush",
    "habitos_saludables_registrosesionrutina",
}


print("=" * 80)
print("INSPECCIÓN DE TABLAS FALTANTES")
print("=" * 80)

for modelo in apps.get_models():

    if not modelo._meta.managed:
        continue

    tabla = modelo._meta.db_table

    if tabla not in TABLAS_OBJETIVO:
        continue

    print("\n" + "-" * 80)
    print(f"MODELO: {modelo.__name__}")
    print(f"TABLA : {tabla}")
    print("-" * 80)

    for campo in modelo._meta.local_fields:

        try:
            tipo = campo.db_type(connection)
        except Exception:
            tipo = "DESCONOCIDO"

        print(
            f"{campo.name:30} "
            f"| {campo.__class__.__name__:20} "
            f"| {tipo}"
        )

print("\n" + "=" * 80)
print("FIN")
print("=" * 80)