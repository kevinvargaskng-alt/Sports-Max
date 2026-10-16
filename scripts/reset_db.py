import os

# --- CONFIGURACIÓN ---
# ¡ATENCIÓN APRENDIZ! Verifica que el nombre de tu entorno virtual sea exactamente este.
# Si le pusiste otro nombre (ej. 'env', 'entorno'), cámbialo en la variable de abajo.
VENV_DIRS = {'.venv', 'venv', 'env', '.env', 'virtualenv', '__pycache__'}
DB_FILE = 'db.sqlite3'
archivos_a_borrar = []

print("\n=== HERRAMIENTA DE RESETEO DE MIGRACIONES Y BASE DE DATOS ===")
print("Nota: Se ignorarán entornos virtuales y paquetes instalados.")

# 1. Buscar archivos de migración recursivamente
for root, dirs, files in os.walk('.'):
    # Ignorar carpetas de entornos virtuales y caches para no dañarlos
    dirs[:] = [d for d in dirs if d not in VENV_DIRS and not d.startswith('.')]

    # Nunca entrar ni tocar site-packages
    if 'site-packages' in root:
        continue

    # Buscar solo dentro de carpetas llamadas 'migrations'
    if os.path.basename(root) == 'migrations':
        for file in files:
            # Seleccionar archivos .py que no sean __init__.py
            if file.endswith('.py') and file != '__init__.py':
                archivos_a_borrar.append(os.path.join(root, file))

# 2. Verificar si existe la base de datos
db_existe = os.path.exists(DB_FILE)

# 3. Mostrar resumen al usuario
print(f"\nSe encontraron {len(archivos_a_borrar)} archivos de migración:")
for archivo in archivos_a_borrar:
    print(f" - {archivo}")

if db_existe:
    print(f"\nTambién se encontró la base de datos: {DB_FILE}")
else:
    print(
        f"\nNo se encontró la base de datos '{DB_FILE}' (ya fue borrada o no existe).")

if len(archivos_a_borrar) == 0 and not db_existe:
    print("\nNo hay nada que borrar. ¡El proyecto ya está limpio!")
    exit()

# 4. Pedir confirmación por seguridad
respuesta = input(
    "\n¿Estás seguro de que deseas ELIMINAR estos archivos? Esta acción NO se puede deshacer. (s/n): ")

if respuesta.lower() == 's':
    # Borrar migraciones
    for archivo in archivos_a_borrar:
        os.remove(archivo)
        print(f"Borrado: {archivo}")

    # Borrar base de datos
    if db_existe:
        os.remove(DB_FILE)
        print(f"Borrado: {DB_FILE}")

    print("\n✅ ¡Limpieza completada exitosamente! Tu proyecto está listo para el nuevo AbstractUser.")
else:
    print("\n🚫 Operación cancelada. No se borró ningún archivo.")
