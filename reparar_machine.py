import os
import django
import sqlite3

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings

DB_PATH = settings.DATABASES["default"]["NAME"]

conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()

print("=" * 70)
print("REPARANDO TABLA gimnasio_machine")
print("=" * 70)

# Verificar si ya existe
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='gimnasio_machine'
""")

if cursor.fetchone():
    print("⚠️ La tabla gimnasio_machine ya existe.")
else:

    cursor.execute("""
        CREATE TABLE "gimnasio_machine" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "public_id" char(32) NOT NULL,
            "nombre" varchar(100) NOT NULL,
            "tipo" varchar(50) NOT NULL,
            "estado" varchar(50) NOT NULL,
            "imagen" varchar(100) NULL,
            "descripcion" text NOT NULL,
            "fecha_adquisicion" date NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX "gimnasio_machine_public_id_5c11e92e"
        ON "gimnasio_machine" ("public_id")
    """)

    print("✅ Tabla gimnasio_machine creada.")
    print("✅ Índice public_id creado.")

conexion.commit()
conexion.close()

print("=" * 70)
print("REPARACIÓN TERMINADA")
print("=" * 70)