"""
Repara el views.py: identifica la ubicacion de cerrar_torneo y inserta
reporte_torneo correctamente antes de editar_equipo
"""
import sys, re

filepath = r'c:\Users\varga\OneDrive\Desktop\Django\interfichas\views.py'

with open(filepath, encoding='utf-8') as f:
    content = f.read()

# Verificar si reporte_torneo ya existe
if 'def reporte_torneo(' in content:
    print('reporte_torneo YA EXISTE en el archivo')
    # Verificar si cronograma_grupo esta en el contexto
    if 'cronograma_grupo' in content:
        print('cronograma_grupo YA ESTA en el contexto - OK')
    else:
        print('cronograma_grupo NO ESTA - hay que actualizar')
else:
    print('reporte_torneo NO EXISTE - hay que insertarlo')

# Mostrar lineas cerca de editar_equipo
lines = content.splitlines()
for i, line in enumerate(lines):
    if 'def editar_equipo' in line or 'def reporte_torneo' in line or 'def cerrar_torneo' in line:
        print(f'  L{i+1}: {line.strip()}')
