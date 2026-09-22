import os
import uuid
import shutil
import sqlite3
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.conf import settings


# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_PATH = settings.DATABASES["default"]["NAME"]

print("=" * 70)
print("REPARACIÓN GENERAL DE BASE DE DATOS")
print("=" * 70)
print("BD:", DB_PATH)


# ============================================================
# COLUMNAS A REPARAR
# ============================================================

reparaciones = {
    "interfichas_torneointerfichas": {
        "public_id": "public_id",
    },

    "interfichas_equipointerfichas": {
        "public_id": "public_id",
        "foto_equipo": "foto_equipo",
    },

    "interfichas_partidointerfichas": {
        "public_id": "public_id",
    },

    "interfichas_resultadotorneo": {
        "public_id": "public_id",
    },

    "gimnasio_reserva": {
        "public_id": "public_id",
    },

    "gimnasio_gimnasioconfig": {
        "public_id": "public_id",
    },

    "gimnasio_maquina": {
        "public_id": "public_id",
        "fecha_adquisicion": "fecha_adquisicion",
    },

    "inventario_elementodeportivo": {
        "public_id": "public_id",
        "categoria": "categoria",
        "ubicacion": "ubicacion",
    },

    "inventario_reserva": {
        "public_id": "public_id",
    },

    "inventario_prestamo": {
        "public_id": "public_id",
        "fecha_vencimiento": "fecha_vencimiento",
    },

    "inventario_detalleprestamo": {
        "public_id": "public_id",
    },

    "inventario_devolucion": {
        "public_id": "public_id",
    },

    "inventario_sancion": {
        "public_id": "public_id",
    },

    "usuarios_sugerencia": {
        "public_id": "public_id",
    },

    "habitos_saludables_habeasdataconsent": {
        "public_id": "public_id",
    },

    "habitos_saludables_habitosaludable": {
        "public_id": "public_id",
    },

    "habitos_saludables_rutinafisica": {
        "public_id": "public_id",
    },

    "habitos_saludables_piramidenutricional": {
        "public_id": "public_id",
    },

    "habitos_saludables_materialapoyo": {
        "public_id": "public_id",
    },

    "habitos_saludables_seguimientosalud": {
        "public_id": "public_id",
    },
}


# ============================================================
# CONEXIÓN
# ============================================================

conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()


# ============================================================
# FUNCIÓN PARA SABER SI EXISTE UNA COLUMNA
# ============================================================

def columnas(tabla):
    cursor.execute(f'PRAGMA table_info("{tabla}")')
    return {fila[1] for fila in cursor.fetchall()}


# ============================================================
# REPARACIÓN
# ============================================================

total_columnas = 0
total_registros_uuid = 0

for tabla, campos in reparaciones.items():

    existentes = columnas(tabla)

    print("\n" + "-" * 70)
    print("TABLA:", tabla)

    # --------------------------------------------------------
    # PUBLIC_ID
    # --------------------------------------------------------

    if "public_id" in campos and "public_id" not in existentes:

        print("➕ Agregando public_id...")

        cursor.execute(
            f'ALTER TABLE "{tabla}" ADD COLUMN "public_id" char(32)'
        )

        cursor.execute(
            f'SELECT rowid FROM "{tabla}" WHERE public_id IS NULL'
        )

        filas = cursor.fetchall()

        for (rowid,) in filas:
            nuevo_id = uuid.uuid4().hex

            cursor.execute(
                f'''
                UPDATE "{tabla}"
                SET public_id = ?
                WHERE rowid = ?
                ''',
                (nuevo_id, rowid)
            )

            total_registros_uuid += 1

        print(f"   ✅ public_id agregado y {len(filas)} registros actualizados.")

        total_columnas += 1

    elif "public_id" in campos:
        print("✔ public_id ya existe.")

    # --------------------------------------------------------
    # FOTO_EQUIPO
    # --------------------------------------------------------

    if "foto_equipo" in campos and "foto_equipo" not in existentes:

        print("➕ Agregando foto_equipo...")

        cursor.execute(
            f'''
            ALTER TABLE "{tabla}"
            ADD COLUMN "foto_equipo" varchar(100)
            '''
        )

        print("   ✅ foto_equipo agregado.")
        total_columnas += 1

    elif "foto_equipo" in campos:
        print("✔ foto_equipo ya existe.")

    # --------------------------------------------------------
    # FECHA_ADQUISICION
    # --------------------------------------------------------

    if "fecha_adquisicion" in campos and "fecha_adquisicion" not in existentes:

        print("➕ Agregando fecha_adquisicion...")

        cursor.execute(
            f'''
            ALTER TABLE "{tabla}"
            ADD COLUMN "fecha_adquisicion" date
            '''
        )

        print("   ✅ fecha_adquisicion agregado.")
        total_columnas += 1

    elif "fecha_adquisicion" in campos:
        print("✔ fecha_adquisicion ya existe.")

    # --------------------------------------------------------
    # CATEGORIA
    # --------------------------------------------------------

    if "categoria" in campos and "categoria" not in existentes:

        print("➕ Agregando categoria...")

        cursor.execute(
            f'''
            ALTER TABLE "{tabla}"
            ADD COLUMN "categoria" varchar(20)
            DEFAULT 'otro'
            '''
        )

        print("   ✅ categoria agregado con valor predeterminado 'otro'.")
        total_columnas += 1

    elif "categoria" in campos:
        print("✔ categoria ya existe.")

    # --------------------------------------------------------
    # UBICACION
    # --------------------------------------------------------

    if "ubicacion" in campos and "ubicacion" not in existentes:

        print("➕ Agregando ubicacion...")

        cursor.execute(
            f'''
            ALTER TABLE "{tabla}"
            ADD COLUMN "ubicacion" varchar(100)
            DEFAULT 'Bodega principal'
            '''
        )

        print("   ✅ ubicacion agregado con valor predeterminado.")
        total_columnas += 1

    elif "ubicacion" in campos:
        print("✔ ubicacion ya existe.")

    # --------------------------------------------------------
    # FECHA_VENCIMIENTO
    # --------------------------------------------------------

    if "fecha_vencimiento" in campos and "fecha_vencimiento" not in existentes:

        print("➕ Agregando fecha_vencimiento...")

        cursor.execute(
            f'''
            ALTER TABLE "{tabla}"
            ADD COLUMN "fecha_vencimiento" date
            '''
        )

        print("   ✅ fecha_vencimiento agregado.")
        total_columnas += 1

    elif "fecha_vencimiento" in campos:
        print("✔ fecha_vencimiento ya existe.")


# ============================================================
# ÍNDICES PARA PUBLIC_ID
# ============================================================

print("\n" + "=" * 70)
print("CREANDO ÍNDICES DE public_id")
print("=" * 70)

for tabla, campos in reparaciones.items():

    if "public_id" not in campos:
        continue

    existentes = columnas(tabla)

    if "public_id" not in existentes:
        continue

    nombre_indice = f"{tabla}_public_id_idx"

    cursor.execute(
        f'''
        CREATE INDEX IF NOT EXISTS "{nombre_indice}"
        ON "{tabla}" ("public_id")
        '''
    )

    print(f"✔ Índice: {nombre_indice}")


# ============================================================
# GUARDAR CAMBIOS
# ============================================================

conexion.commit()

print("\n" + "=" * 70)
print("REPARACIÓN TERMINADA")
print("=" * 70)
print("Columnas agregadas:", total_columnas)
print("public_id generados:", total_registros_uuid)

conexion.close()

print("\n✅ Base de datos guardada correctamente.")