import os
import django
import sqlite3

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.db import connection


print("=" * 80)
print("AUDITORÍA COMPLETA DEL ESQUEMA")
print("=" * 80)

db_path = connection.settings_dict["NAME"]

conexion = sqlite3.connect(db_path)
cursor = conexion.cursor()


# ---------------------------------------------------------
# OBTENER TABLAS EXISTENTES EN SQLITE
# ---------------------------------------------------------

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
""")

tablas_bd = {fila[0] for fila in cursor.fetchall()}


print(f"\n📦 Tablas encontradas en SQLite: {len(tablas_bd)}")


# ---------------------------------------------------------
# VARIABLES PARA EL INFORME
# ---------------------------------------------------------

tablas_faltantes = []
columnas_faltantes = []
indices_faltantes = []

modelos_revisados = 0


# ---------------------------------------------------------
# REVISAR TODOS LOS MODELOS DE DJANGO
# ---------------------------------------------------------

for modelo in apps.get_models():

    # Ignorar modelos que no administran tabla propia
    if not modelo._meta.managed:
        continue

    # Ignorar modelos automáticos/intermedios
    if modelo._meta.auto_created:
        continue

    modelos_revisados += 1

    tabla = modelo._meta.db_table

    print("\n" + "-" * 80)
    print(f"MODELO : {modelo.__name__}")
    print(f"TABLA  : {tabla}")

    # -----------------------------------------------------
    # TABLA
    # -----------------------------------------------------

    if tabla not in tablas_bd:

        print("❌ TABLA FALTANTE")

        tablas_faltantes.append({
            "modelo": modelo.__name__,
            "tabla": tabla,
        })

        continue

    print("✅ Tabla existe")

    # -----------------------------------------------------
    # COLUMNAS
    # -----------------------------------------------------

    cursor.execute(f'PRAGMA table_info("{tabla}")')

    columnas_bd = {fila[1] for fila in cursor.fetchall()}

    columnas_modelo = {
        campo.column
        for campo in modelo._meta.local_fields
    }

    faltantes = columnas_modelo - columnas_bd

    if faltantes:

        print("❌ COLUMNAS FALTANTES:")

        for columna in sorted(faltantes):
            print(f"   - {columna}")

            columnas_faltantes.append({
                "modelo": modelo.__name__,
                "tabla": tabla,
                "columna": columna,
            })

    else:

        print("✅ Todas las columnas existen")

    # -----------------------------------------------------
    # ÍNDICES public_id
    # -----------------------------------------------------

    tiene_public_id = any(
        campo.name == "public_id"
        for campo in modelo._meta.local_fields
    )

    if tiene_public_id:

        cursor.execute(f'PRAGMA index_list("{tabla}")')

        indices = cursor.fetchall()

        nombres_indices = {
            fila[1]
            for fila in indices
        }

        indice_public_id = any(
            "public_id" in nombre
            for nombre in nombres_indices
        )

        if indice_public_id:
            print("✅ Índice public_id existe")
        else:
            print("⚠️ Índice public_id NO encontrado")

            indices_faltantes.append({
                "modelo": modelo.__name__,
                "tabla": tabla,
            })


# ---------------------------------------------------------
# RESUMEN
# ---------------------------------------------------------

print("\n")
print("=" * 80)
print("RESUMEN DE LA AUDITORÍA")
print("=" * 80)

print(f"\nModelos revisados: {modelos_revisados}")
print(f"Tablas existentes: {len(tablas_bd)}")


print("\n🗂️ TABLAS FALTANTES")
print("-" * 80)

if tablas_faltantes:

    for item in tablas_faltantes:
        print(
            f"❌ {item['tabla']} "
            f"(modelo: {item['modelo']})"
        )

else:

    print("✅ No hay tablas faltantes")


print("\n📋 COLUMNAS FALTANTES")
print("-" * 80)

if columnas_faltantes:

    for item in columnas_faltantes:
        print(
            f"❌ {item['tabla']}.{item['columna']} "
            f"(modelo: {item['modelo']})"
        )

else:

    print("✅ No hay columnas faltantes")


print("\n🔎 ÍNDICES public_id FALTANTES")
print("-" * 80)

if indices_faltantes:

    for item in indices_faltantes:
        print(
            f"⚠️ {item['tabla']} "
            f"(modelo: {item['modelo']})"
        )

else:

    print("✅ No hay índices public_id faltantes")


print("\n")
print("=" * 80)
print("FIN DE LA AUDITORÍA")
print("=" * 80)


conexion.close()