import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.db import connection
from django.db import models


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
print("REPARACIÓN CONTROLADA DE TABLAS FALTANTES")
print("=" * 80)

# Obtener tablas actuales
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)
    tablas_existentes = {fila[0] for fila in cursor.fetchall()}


# Buscar modelos correspondientes
modelos = []

for modelo in apps.get_models():

    if not modelo._meta.managed:
        continue

    if modelo._meta.auto_created:
        continue

    if modelo._meta.db_table in TABLAS_OBJETIVO:
        modelos.append(modelo)


# Orden importante: RutinaGimnasio antes de RegistroSesionRutina
modelos.sort(
    key=lambda modelo: (
        modelo._meta.db_table
        == "habitos_saludables_registrosesionrutina",
    )
)


print("\nTablas que se revisarán:")

for modelo in modelos:
    tabla = modelo._meta.db_table

    if tabla in tablas_existentes:
        print(f"⚠️ YA EXISTE: {tabla}")
    else:
        print(f"❌ FALTA:    {tabla}")


print("\n" + "-" * 80)
print("CREANDO TABLAS")
print("-" * 80)

creadas = 0

with connection.schema_editor() as schema_editor:

    for modelo in modelos:

        tabla = modelo._meta.db_table

        # Comprobar nuevamente dentro de la operación
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                AND name = %s
            """, [tabla])

            existe = cursor.fetchone() is not None

        if existe:
            print(f"⏭️  Omitida: {tabla}")
            continue

        print(f"🔧 Creando: {tabla}")

        schema_editor.create_model(modelo)

        print(f"✅ Creada:  {tabla}")

        creadas += 1


print("\n" + "-" * 80)
print("REVISANDO ÍNDICE usuarios_usuario.public_id")
print("-" * 80)

with connection.cursor() as cursor:

    cursor.execute("""
        PRAGMA index_list("usuarios_usuario")
    """)

    indices = cursor.fetchall()

    indice_public_id = None

    for indice in indices:

        nombre_indice = indice[1]

        cursor.execute(
            f'PRAGMA index_info("{nombre_indice}")'
        )

        columnas = cursor.fetchall()

        nombres_columnas = {
            fila[2]
            for fila in columnas
        }

        if nombres_columnas == {"public_id"}:
            indice_public_id = nombre_indice
            break


if indice_public_id:

    print(
        f"✅ El índice de public_id ya existe: "
        f"{indice_public_id}"
    )

else:

    print("🔧 Creando índice para usuarios_usuario.public_id")

    with connection.schema_editor() as schema_editor:

        indice = models.Index(
            fields=["public_id"],
            name="usuarios_usuario_public_id_idx",
        )

        schema_editor.add_index(
            apps.get_model("usuarios", "Usuario"),
            indice,
        )

    print("✅ Índice public_id creado.")


print("\n" + "=" * 80)
print("REPARACIÓN TERMINADA")
print("=" * 80)
print(f"Tablas creadas: {creadas}")
print("=" * 80)