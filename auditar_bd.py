import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.db import connection

print("\n" + "=" * 70)
print("AUDITORÍA DE MODELOS VS BASE DE DATOS")
print("=" * 70)

with connection.cursor() as cursor:
    tablas_bd = {
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

problemas = []

for modelo in apps.get_models():
    tabla = modelo._meta.db_table

    if tabla not in tablas_bd:
        continue

    with connection.cursor() as cursor:
        cursor.execute(f'PRAGMA table_info("{tabla}")')
        columnas_bd = {row[1] for row in cursor.fetchall()}

    columnas_modelo = {
        campo.column
        for campo in modelo._meta.local_fields
    }

    faltantes = columnas_modelo - columnas_bd

    if faltantes:
        problemas.append(
            (modelo.__name__, tabla, sorted(faltantes))
        )

if not problemas:
    print("\n✅ No se encontraron columnas faltantes.")
else:
    print("\n❌ COLUMNAS FALTANTES:\n")

    for modelo, tabla, faltantes in problemas:
        print(f"Modelo: {modelo}")
        print(f"Tabla:  {tabla}")
        print(f"Faltan: {faltantes}")
        print("-" * 70)

print("\n" + "=" * 70)
print("FIN DE LA AUDITORÍA")
print("=" * 70)