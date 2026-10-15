"""
Script final: asignar fechas a partidos de Canada y mostrar cronograma
"""
import os
import django
import sys

sys.path.insert(0, r'c:\Users\varga\OneDrive\Desktop\Django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from interfichas.models import TorneoInterfichas, PartidoInterfichas
from datetime import date, timedelta

torneo = TorneoInterfichas.objects.get(pk=11)

# Partidos sin fecha asignada (los nuevos de Canada)
sin_fecha = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo', fecha_partido__isnull=True
).select_related('equipo_local', 'equipo_visitante', 'grupo').order_by('grupo__nombre_grupo', 'id')
print(f'Partidos sin fecha: {sin_fecha.count()}')

# Buscar la ultima fecha usada
ultima_fecha = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo', fecha_partido__isnull=False
).order_by('-fecha_partido').values_list('fecha_partido', flat=True).first()
print(f'Ultima fecha programada: {ultima_fecha}')

# Continuar desde el dia siguiente habil
def dias_habiles(desde):
    fecha = desde + timedelta(days=1)
    while True:
        if fecha.weekday() < 5:
            yield fecha
        fecha += timedelta(days=1)

DIAS = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom']

gen = dias_habiles(ultima_fecha)
for p in sin_fecha:
    f = next(gen)
    p.fecha_partido = f
    p.save()
    dia = DIAS[f.weekday()]
    print(f'  [{dia} {f.strftime("%d/%m/%Y")}] Grupo {p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} vs {p.equipo_visitante.nombre_equipo}')

print('\n=== CRONOGRAMA FINAL COMPLETO ===')
todos = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo'
).select_related('equipo_local', 'equipo_visitante', 'grupo').order_by('fecha_partido', 'id')

dia_actual = None
jornada = 0
for p in todos:
    if p.fecha_partido != dia_actual:
        dia_actual = p.fecha_partido
        jornada += 1
        dia_semana = DIAS[dia_actual.weekday()]
        print(f'\n  J{jornada} [{dia_semana} {dia_actual.strftime("%d/%m/%Y")}]')
    estado = f'RESULT {p.goles_local}-{p.goles_visitante}' if p.jugado else 'pendiente'
    print(f'     Grupo {p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} vs {p.equipo_visitante.nombre_equipo} [{estado}]')
print(f'\nTotal partidos: {todos.count()}')
