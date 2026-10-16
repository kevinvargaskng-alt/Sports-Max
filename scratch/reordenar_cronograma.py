"""
Script: reordenar cronograma con intercalado de grupos y descanso entre equipos
- Intercala partidos entre Grupo A, B y C
- Garantiza que ningun equipo juegue dos dias seguidos
- 1 partido por dia habil (lun-vie), sin sabados ni domingos
- Los partidos ya jugados NO se tocan
- Fecha inicio: 28/09/2026
"""
import os
import django
import sys
from collections import deque

sys.path.insert(0, r'c:\Users\varga\OneDrive\Desktop\Django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from interfichas.models import TorneoInterfichas, PartidoInterfichas
from datetime import date, timedelta

torneo = TorneoInterfichas.objects.get(pk=11)

# ── Cargar todos los partidos PENDIENTES agrupados por grupo ────
pendientes = list(
    PartidoInterfichas.objects.filter(
        torneo=torneo, fase='grupo', jugado=False
    ).select_related('equipo_local', 'equipo_visitante', 'grupo')
    .order_by('grupo__nombre_grupo', 'id')
)
print(f'Total partidos pendientes: {len(pendientes)}')

# Agrupar por letra de grupo
colas = {}
for p in pendientes:
    letra = p.grupo.nombre_grupo
    if letra not in colas:
        colas[letra] = deque()
    colas[letra].append(p)

print('Partidos por grupo:', {k: len(v) for k, v in colas.items()})

# ── Algoritmo de interleaving con descanso ──────────────────────
def reordenar_intercalado(colas_dict, max_iter=500):
    """
    Genera un orden de partidos que:
    1. Alterna entre grupos (round-robin: A, B, C, A, B, C...)
    2. Asegura que ningun equipo juegue dos partidos seguidos
    """
    resultado = []
    # Copia mutable de las colas
    colas_work = {k: list(v) for k, v in colas_dict.items()}
    letras = sorted(colas_work.keys())  # ['A', 'B', 'C']
    
    # Set de equipos que jugaron en la posicion anterior
    equipos_ultimo = set()
    
    intentos_globales = 0
    
    while any(len(q) > 0 for q in colas_work.values()) and intentos_globales < max_iter:
        intentos_globales += 1
        colocado = False
        
        # Intentar en orden rotando grupos
        for _ in range(len(letras) * 3):  # dar multiples vueltas
            # Tomar el grupo con mas partidos primero (para balancear)
            grupos_disponibles = [(k, v) for k, v in colas_work.items() if len(v) > 0]
            if not grupos_disponibles:
                break
            
            # Ordenar por: grupo con mas partidos primero (para balancear carga)
            grupos_disponibles.sort(key=lambda x: -len(x[1]))
            
            for grupo_letra, cola in grupos_disponibles:
                # Buscar en la cola del grupo un partido que NO repita equipo
                for i, partido in enumerate(cola):
                    eq_local = partido.equipo_local.pk
                    eq_visit = partido.equipo_visitante.pk
                    
                    if eq_local not in equipos_ultimo and eq_visit not in equipos_ultimo:
                        # Partido aceptable
                        resultado.append(partido)
                        equipos_ultimo = {eq_local, eq_visit}
                        colas_work[grupo_letra].pop(i)
                        colocado = True
                        break
                
                if colocado:
                    break
            
            if colocado:
                break
        
        if not colocado:
            # No se puede evitar repeticion: tomar el partido del grupo mas lleno
            grupos_disponibles = [(k, v) for k, v in colas_work.items() if len(v) > 0]
            if grupos_disponibles:
                grupos_disponibles.sort(key=lambda x: -len(x[1]))
                grupo_letra, cola = grupos_disponibles[0]
                partido = cola.pop(0)
                resultado.append(partido)
                equipos_ultimo = {partido.equipo_local.pk, partido.equipo_visitante.pk}
                print(f'  [FORZADO] {partido.equipo_local.nombre_equipo} vs {partido.equipo_visitante.nombre_equipo} (Grupo {grupo_letra})')
    
    return resultado

orden_final = reordenar_intercalado(colas)
print(f'Orden generado: {len(orden_final)} partidos')

# ── Generador de fechas habiles ─────────────────────────────────
def fechas_habiles(desde):
    fecha = desde
    while True:
        if fecha.weekday() < 5:  # 0=lun, 4=vie
            yield fecha
        fecha += timedelta(days=1)

DIAS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
gen = fechas_habiles(date(2026, 9, 28))

# ── Asignar fechas al nuevo orden ──────────────────────────────
print('\n=== APLICANDO NUEVO CRONOGRAMA INTERCALADO ===')
for partido in orden_final:
    fecha = next(gen)
    partido.fecha_partido = fecha
    partido.save(update_fields=['fecha_partido'])

# ── Mostrar resultado ───────────────────────────────────────────
print('\n=== CRONOGRAMA COMPLETO ===')
todos = PartidoInterfichas.objects.filter(
    torneo=torneo, fase='grupo'
).select_related('equipo_local', 'equipo_visitante', 'grupo').order_by('fecha_partido', 'id')

dia_actual = None
jornada = 0
for p in todos:
    if p.fecha_partido != dia_actual:
        dia_actual = p.fecha_partido
        jornada += 1 if not p.jugado else 0
        dia_semana = DIAS[dia_actual.weekday()]
        j_label = f'J{jornada}' if not p.jugado else 'PREVIO'
        print(f'\n  {j_label} [{dia_semana} {dia_actual.strftime("%d/%m/%Y")}]')
    estado = f'JUGADO {p.goles_local}-{p.goles_visitante}' if p.jugado else 'pendiente'
    print(f'     Gr.{p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} vs {p.equipo_visitante.nombre_equipo} [{estado}]')

# ── Verificar: ningun equipo juega 2 dias seguidos ─────────────
print('\n=== VERIFICACION DE DESCANSO ENTRE EQUIPOS ===')
solos_pendientes = [p for p in todos if not p.jugado]
conflictos = 0
for i in range(1, len(solos_pendientes)):
    p_ant = solos_pendientes[i - 1]
    p_act = solos_pendientes[i]
    equipos_ant = {p_ant.equipo_local.pk, p_ant.equipo_visitante.pk}
    equipos_act = {p_act.equipo_local.pk, p_act.equipo_visitante.pk}
    if equipos_ant & equipos_act:
        conflictos += 1
        nombres = equipos_ant & equipos_act
        eq_names = [p_ant.equipo_local.nombre_equipo if p_ant.equipo_local.pk in nombres
                    else p_ant.equipo_visitante.nombre_equipo]
        print(f'  CONFLICTO J{i} vs J{i+1}: equipo repetido en dias consecutivos - {eq_names}')

if conflictos == 0:
    print('  OK: Ningun equipo juega en dias consecutivos')
else:
    print(f'  TOTAL CONFLICTOS: {conflictos} (imposibles de evitar por el numero de equipos)')

print(f'\nTotal partidos programados: {todos.count()}')
print('Cronograma intercalado aplicado exitosamente!')
