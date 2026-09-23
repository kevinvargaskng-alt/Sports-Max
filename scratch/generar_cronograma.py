"""
Script para generar cronograma del Mundialito Futbol 8
Torneo ID=11 - Los grupos ya fueron reorganizados en la ejecucion anterior
"""
import os
import django
import sys

sys.path.insert(0, r'c:\Users\varga\OneDrive\Desktop\Django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from interfichas.models import TorneoInterfichas, GrupoInterfichas, PartidoInterfichas, EquipoInterfichas
from django.db.models import Q
from datetime import date, timedelta

torneo = TorneoInterfichas.objects.get(pk=11)
grupo_b = torneo.grupos.get(nombre_grupo='B')
grupo_c = torneo.grupos.get(nombre_grupo='C')

print('=== ESTADO ACTUAL DE GRUPOS ===')
print('  Grupo A:', [e.nombre_equipo for e in torneo.grupos.get(nombre_grupo='A').equipos.all()])
print('  Grupo B:', [e.nombre_equipo for e in grupo_b.equipos.all()])
print('  Grupo C:', [e.nombre_equipo for e in grupo_c.equipos.all()])

total_a = PartidoInterfichas.objects.filter(torneo=torneo, grupo__nombre_grupo='A', fase='grupo').count()
total_b = PartidoInterfichas.objects.filter(torneo=torneo, grupo=grupo_b, fase='grupo').count()
total_c = PartidoInterfichas.objects.filter(torneo=torneo, grupo=grupo_c, fase='grupo').count()
total = total_a + total_b + total_c
print(f'\nPartidos: Grupo A={total_a} | Grupo B={total_b} | Grupo C={total_c} | TOTAL={total}')

# ============================================================
# PASO 6: MARCAR LOS 3 PARTIDOS YA JUGADOS
# ============================================================
print('\n=== MARCANDO PARTIDOS JUGADOS ===')

# Uruguay vs Estados Unidos -> Gano Estados Unidos 3-1
p_uru_usa = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo',
    equipo_local__nombre_equipo='Uruguay',
    equipo_visitante__nombre_equipo='Estados Unidos'
).first()
if not p_uru_usa:
    p_uru_usa = PartidoInterfichas.objects.filter(
        torneo=torneo, fase='grupo',
        equipo_local__nombre_equipo='Estados Unidos',
        equipo_visitante__nombre_equipo='Uruguay'
    ).first()
    if p_uru_usa:
        p_uru_usa.goles_local = 3; p_uru_usa.goles_visitante = 1
    else:
        print('  AVISO: No encontrado: Uruguay vs Estados Unidos')
else:
    p_uru_usa.goles_local = 1; p_uru_usa.goles_visitante = 3

if p_uru_usa:
    p_uru_usa.jugado = True
    p_uru_usa.fecha_partido = date(2026, 9, 24)
    p_uru_usa.save()
    print(f'  OK {p_uru_usa.equipo_local.nombre_equipo} {p_uru_usa.goles_local}-{p_uru_usa.goles_visitante} {p_uru_usa.equipo_visitante.nombre_equipo} (ID={p_uru_usa.pk})')

# Colombia vs Japon -> Gano Japon 3-2
p_col_jap = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo',
    equipo_local__nombre_equipo='Colombia',
    equipo_visitante__nombre_equipo='Jap\u00f3n'
).first()
if not p_col_jap:
    p_col_jap = PartidoInterfichas.objects.filter(
        torneo=torneo, fase='grupo',
        equipo_local__nombre_equipo='Jap\u00f3n',
        equipo_visitante__nombre_equipo='Colombia'
    ).first()
    if p_col_jap:
        p_col_jap.goles_local = 3; p_col_jap.goles_visitante = 2
    else:
        print('  AVISO: No encontrado: Colombia vs Japon')
else:
    p_col_jap.goles_local = 2; p_col_jap.goles_visitante = 3

if p_col_jap:
    p_col_jap.jugado = True
    p_col_jap.fecha_partido = date(2026, 9, 25)
    p_col_jap.save()
    print(f'  OK {p_col_jap.equipo_local.nombre_equipo} {p_col_jap.goles_local}-{p_col_jap.goles_visitante} {p_col_jap.equipo_visitante.nombre_equipo} (ID={p_col_jap.pk})')

# Alemania vs Portugal -> Empate 1-1
p_ale_por = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo',
    equipo_local__nombre_equipo='Alemania',
    equipo_visitante__nombre_equipo='Portugal'
).first()
if not p_ale_por:
    p_ale_por = PartidoInterfichas.objects.filter(
        torneo=torneo, fase='grupo',
        equipo_local__nombre_equipo='Portugal',
        equipo_visitante__nombre_equipo='Alemania'
    ).first()

if p_ale_por:
    p_ale_por.goles_local = 1; p_ale_por.goles_visitante = 1
    p_ale_por.jugado = True
    p_ale_por.fecha_partido = date(2026, 9, 26)
    p_ale_por.save()
    print(f'  OK {p_ale_por.equipo_local.nombre_equipo} {p_ale_por.goles_local}-{p_ale_por.goles_visitante} {p_ale_por.equipo_visitante.nombre_equipo} (ID={p_ale_por.pk})')
else:
    print('  AVISO: No encontrado: Alemania vs Portugal')

# ============================================================
# PASO 7: ASIGNAR FECHAS A LOS PARTIDOS PENDIENTES
# Desde el 28 de septiembre de 2026, 1 partido/dia, sin sabado/domingo
# ============================================================
print('\n=== ASIGNANDO CRONOGRAMA DE FECHAS ===')

partidos_pendientes = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo', jugado=False
).select_related('equipo_local', 'equipo_visitante', 'grupo').order_by('grupo__nombre_grupo', 'id')

print(f'Partidos pendientes por programar: {partidos_pendientes.count()}')

def proxima_fecha_habil(fecha_inicio):
    fecha = fecha_inicio
    while True:
        if fecha.weekday() < 5:  # 0=lun, 4=vie
            yield fecha
        fecha += timedelta(days=1)

generador = proxima_fecha_habil(date(2026, 9, 28))
count_programados = 0

for partido in partidos_pendientes:
    fecha_asignada = next(generador)
    partido.fecha_partido = fecha_asignada
    partido.save()
    count_programados += 1

print(f'OK Programados {count_programados} partidos')

# ── Mostrar cronograma completo ─────────────────────────────────
print('\n=== CRONOGRAMA COMPLETO ===')
todos = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo'
).select_related('equipo_local', 'equipo_visitante', 'grupo').order_by('fecha_partido', 'id')

DIAS = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom']
dia_actual = None
for p in todos:
    if p.fecha_partido != dia_actual:
        dia_actual = p.fecha_partido
        dia_semana = DIAS[dia_actual.weekday()]
        print(f'\n  [{dia_semana} {dia_actual.strftime("%d/%m/%Y")}]')
    estado = f'JUGADO {p.goles_local}-{p.goles_visitante}' if p.jugado else 'pendiente'
    print(f'     Grupo {p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} vs {p.equipo_visitante.nombre_equipo} [{estado}]')

print('\nScript completado exitosamente!')
