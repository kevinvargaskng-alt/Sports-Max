"""
Aplica todos los cambios necesarios a views.py en un solo script:
1. Reemplaza PAISES_TORNEO (quita Croacia duplicada, agrega Canada)
2. Agrega _reordenar_intercalado + generar_cronograma al final
3. Actualiza reporte_torneo con cronograma_grupo y equipos_con_grupo
"""
import re, ast

filepath = r'c:\Users\varga\OneDrive\Desktop\Django\interfichas\views.py'
with open(filepath, encoding='utf-8') as f:
    content = f.read()

print(f'Lineas originales: {len(content.splitlines())}')

# ── 1. Reemplazar PAISES_TORNEO ───────────────────────────────────
old_paises = '''PAISES_TORNEO = [
    "Argentina", "Brasil", "Francia", "Espa\u00f1a", "Inglaterra",
    "Alemania", "Portugal", "Pa\u00edses Bajos", "Colombia", "Uruguay",
    "Croacia", "B\u00e9lgica", "Noruega", "Jap\u00f3n", "Estados Unidos",
    "M\u00e9xico", "Croacia"
]'''
new_paises = '''PAISES_TORNEO = [
    "Argentina", "Brasil", "Francia", "Espa\u00f1a", "Inglaterra",
    "Alemania", "Portugal", "Pa\u00edses Bajos", "Colombia", "Uruguay",
    "Canad\u00e1", "B\u00e9lgica", "Noruega", "Jap\u00f3n", "Estados Unidos",
    "M\u00e9xico",
]'''
if old_paises in content:
    content = content.replace(old_paises, new_paises)
    print('1. PAISES_TORNEO actualizado')
else:
    print('1. PAISES_TORNEO no encontrado (puede ya estar correcto)')

# ── 2. Actualizar reporte_torneo ───────────────────────────────────
old_reporte = '''@solo_admin
def reporte_torneo(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos = torneo.grupos.prefetch_related('equipos').all()

    grupos_con_tabla = [
        {
            'grupo': g,
            'tabla': _calcular_tabla(g),
            'partidos': g.partidos.select_related('equipo_local', 'equipo_visitante').order_by('fecha_partido', 'hora_partido', 'id')
        }
        for g in grupos
    ]

    equipos = torneo.equipos.prefetch_related('jugadores').all().order_by('nombre_equipo')
    partidos_todos = torneo.partidos.select_related('equipo_local', 'equipo_visitante').all()
    partidos_jugados = [p for p in partidos_todos if p.jugado]

    campeon = None
    try:
        if hasattr(torneo, 'resultado') and torneo.resultado.ganador:
            campeon = torneo.resultado.ganador
    except Exception:
        pass

    if not campeon:
        final_p = torneo.partidos.filter(fase='final', jugado=True).select_related('equipo_local', 'equipo_visitante').first()
        if final_p and final_p.goles_local is not None and final_p.goles_visitante is not None:
            if final_p.goles_local > final_p.goles_visitante:
                campeon = final_p.equipo_local
            elif final_p.goles_visitante > final_p.goles_local:
                campeon = final_p.equipo_visitante

    from django.utils import timezone
    context = {
        'torneo':             torneo,
        'grupos_con_tabla':   grupos_con_tabla,
        'equipos':            equipos,
        'total_equipos':      equipos.count(),
        'total_partidos':     len(partidos_todos),
        'partidos_jugados':   len(partidos_jugados),
        'partidos_cuartos':   torneo.partidos.filter(fase='cuartos').select_related('equipo_local', 'equipo_visitante'),
        'partidos_semifinal': torneo.partidos.filter(fase='semifinal').select_related('equipo_local', 'equipo_visitante'),
        'partidos_final':     torneo.partidos.filter(fase='final').select_related('equipo_local', 'equipo_visitante'),
        'campeon':            campeon,
        'tipo_marcador':      torneo.disciplina.tipo_marcador if torneo.disciplina else 'goles',
        'ahora':              timezone.now(),
    }
    return render(request, 'interfichas/reporte_torneo.html', context)'''

new_reporte = '''@solo_admin
def reporte_torneo(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos = torneo.grupos.prefetch_related('equipos').all()

    grupos_con_tabla = [
        {
            'grupo': g,
            'tabla': _calcular_tabla(g),
            'partidos': g.partidos.select_related('equipo_local', 'equipo_visitante').order_by('fecha_partido', 'hora_partido', 'id')
        }
        for g in grupos
    ]

    equipos = torneo.equipos.prefetch_related('jugadores').all().order_by('nombre_equipo')
    partidos_todos = torneo.partidos.select_related('equipo_local', 'equipo_visitante').all()
    partidos_jugados_count = sum(1 for p in partidos_todos if p.jugado)

    # Cronograma fase de grupos: jugados primero, pendientes luego ordenados por fecha
    partidos_grupo_qs = list(
        PartidoInterfichas.objects
        .filter(torneo=torneo, fase='grupo')
        .select_related('equipo_local', 'equipo_visitante', 'grupo')
        .order_by('fecha_partido', 'id')
    )
    cronograma_grupo = [p for p in partidos_grupo_qs if p.jugado] + \\
                       [p for p in partidos_grupo_qs if not p.jugado]

    # Equipos con nombre de grupo anotado
    equipo_grupo_map = {}
    for g in grupos:
        for eq in g.equipos.all():
            equipo_grupo_map[eq.pk] = g.nombre_grupo
    equipos_con_grupo = []
    for eq in equipos:
        eq.nombre_grupo = equipo_grupo_map.get(eq.pk, '')
        equipos_con_grupo.append(eq)

    campeon = None
    try:
        if hasattr(torneo, 'resultado') and torneo.resultado.ganador:
            campeon = torneo.resultado.ganador
    except Exception:
        pass

    if not campeon:
        final_p = torneo.partidos.filter(fase='final', jugado=True).select_related('equipo_local', 'equipo_visitante').first()
        if final_p and final_p.goles_local is not None and final_p.goles_visitante is not None:
            if final_p.goles_local > final_p.goles_visitante:
                campeon = final_p.equipo_local
            elif final_p.goles_visitante > final_p.goles_local:
                campeon = final_p.equipo_visitante

    from django.utils import timezone
    context = {
        'torneo':             torneo,
        'grupos_con_tabla':   grupos_con_tabla,
        'equipos':            equipos,
        'equipos_con_grupo':  equipos_con_grupo,
        'cronograma_grupo':   cronograma_grupo,
        'total_equipos':      equipos.count(),
        'total_partidos':     partidos_todos.count(),
        'partidos_jugados':   partidos_jugados_count,
        'partidos_cuartos':   torneo.partidos.filter(fase='cuartos').select_related('equipo_local', 'equipo_visitante'),
        'partidos_semifinal': torneo.partidos.filter(fase='semifinal').select_related('equipo_local', 'equipo_visitante'),
        'partidos_final':     torneo.partidos.filter(fase='final').select_related('equipo_local', 'equipo_visitante'),
        'campeon':            campeon,
        'tipo_marcador':      torneo.disciplina.tipo_marcador if torneo.disciplina else 'goles',
        'ahora':              timezone.now(),
    }
    return render(request, 'interfichas/reporte_torneo.html', context)'''

if old_reporte in content:
    content = content.replace(old_reporte, new_reporte)
    print('2. reporte_torneo actualizado')
else:
    print('2. ERROR: old_reporte no encontrado exactamente')
    # Buscar parcialmente
    if 'def reporte_torneo' in content:
        print('   (la funcion existe pero el cuerpo no coincide exactamente)')

# ── 3. Agregar al final: interleaving + generar_cronograma ─────────
NUEVO_BLOQUE = '''

# ============================================================
#  GENERAR CRONOGRAMA AUTOMATICO - intercalado entre grupos,
#  sin repeticion de equipos en dias consecutivos, lun-vie
# ============================================================
from datetime import date as _date_cls, timedelta as _timedelta_cls


def _reordenar_intercalado(partidos_lista):
    """
    Ordena los partidos con dos criterios:
      1. Alterna entre grupos (el de mayor cola primero)
      2. Ningun equipo juega dos dias seguidos
    """
    colas = {}
    for p in partidos_lista:
        letra = p.grupo.nombre_grupo
        if letra not in colas:
            colas[letra] = []
        colas[letra].append(p)

    resultado = []
    equipos_ultimo = set()

    while any(len(q) > 0 for q in colas.values()):
        colocado = False
        grupos_disp = [(k, v) for k, v in colas.items() if len(v) > 0]
        grupos_disp.sort(key=lambda x: -len(x[1]))

        for grupo_letra, cola in grupos_disp:
            for i, partido in enumerate(cola):
                eq_l = partido.equipo_local_id
                eq_v = partido.equipo_visitante_id
                if eq_l not in equipos_ultimo and eq_v not in equipos_ultimo:
                    resultado.append(partido)
                    equipos_ultimo = {eq_l, eq_v}
                    colas[grupo_letra].pop(i)
                    colocado = True
                    break
            if colocado:
                break

        if not colocado:
            grupos_disp = [(k, v) for k, v in colas.items() if len(v) > 0]
            grupos_disp.sort(key=lambda x: -len(x[1]))
            grupo_letra, cola = grupos_disp[0]
            partido = cola.pop(0)
            resultado.append(partido)
            equipos_ultimo = {partido.equipo_local_id, partido.equipo_visitante_id}

    return resultado


@solo_admin
@require_POST
def generar_cronograma(request, torneo_id):
    """
    Asigna fechas a los partidos de grupo con interleaving inteligente:
    - Intercala partidos entre grupos A, B, C
    - Ningun equipo juega en dias consecutivos
    - 1 partido por dia habil (lunes a viernes)
    - Los partidos ya jugados conservan su fecha
    """
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)

    fecha_str = request.POST.get('fecha_inicio', '').strip()
    try:
        from datetime import datetime as _dt
        fecha_inicio = _dt.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_inicio = _date_cls.today()

    partidos_pendientes = list(
        PartidoInterfichas.objects
        .filter(torneo=torneo, fase='grupo', jugado=False)
        .select_related('equipo_local', 'equipo_visitante', 'grupo')
        .order_by('grupo__nombre_grupo', 'id')
    )

    partidos_ordenados = _reordenar_intercalado(partidos_pendientes)

    def _dias_habiles(desde):
        fecha = desde
        while True:
            if fecha.weekday() < 5:
                yield fecha
            fecha += _timedelta_cls(days=1)

    generador = _dias_habiles(fecha_inicio)
    count = 0
    for partido in partidos_ordenados:
        partido.fecha_partido = next(generador)
        partido.save(update_fields=['fecha_partido'])
        count += 1

    messages.success(
        request,
        f"Cronograma intercalado generado: {count} partido(s) programado(s) "
        f"a partir del {fecha_inicio.strftime('%d/%m/%Y')}, "
        f"de lunes a viernes (1 por dia, grupos alternados)."
    )
    return redirect('gestionar_torneo', torneo_id=torneo_id)
'''

if 'def generar_cronograma' not in content:
    content = content.rstrip() + '\n' + NUEVO_BLOQUE
    print('3. generar_cronograma agregado al final')
else:
    print('3. generar_cronograma ya existe')

# ── Guardar ───────────────────────────────────────────────────────
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# ── Verificar sintaxis ────────────────────────────────────────────
try:
    ast.parse(content)
    print('\nSintaxis Python: OK')
except SyntaxError as e:
    print(f'\nERROR de sintaxis: {e}')
    import sys; sys.exit(1)

print(f'Lineas finales: {len(content.splitlines())}')
print('Script completado!')
