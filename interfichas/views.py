from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import date  # <--- Importación agregada
import random
from itertools import combinations
from .models import (
    TorneoInterfichas, EquipoInterfichas, Disciplina, 
    JugadorEquipo, GrupoInterfichas, PartidoInterfichas, ResultadoTorneo
)

PROGRAMAS_GLOBALES = [
    "Análisis y Desarrollo de Software (ADSO)",
    "Supervisión de Procesos Mineros",
    "Gestión de la Seguridad y Salud en el Trabajo",
    "Química Aplicada a la Industria",
    "Levantamientos Topográficos y Georreferenciación",
    "Construcción de Infraestructura Vial",
    "Sistemas de Agua y Saneamiento",
    "Operación de Maquinaria Pesada para Excavación",
    "Mantenimiento de Equipo Pesado para Infraestructura, Minería y Transporte",
]

# ================================================================
# VISTAS GENERALES (LISTADO Y CRUD BÁSICO)
# ================================================================

@login_required
def interfichas_list(request):
    # Traemos todos los torneos para la tabla de arriba
    torneos = TorneoInterfichas.objects.all().order_by('-fecha_torneo_fichas')

    # Traemos todos los equipos para la tabla de abajo
    equipos = EquipoInterfichas.objects.select_related('torneo', 'disciplina').all()

    # Traemos todas las disciplinas para los selects de los modales
    disciplinas = Disciplina.objects.all().order_by('nombre_disciplina')

    if request.method == 'POST':
        accion = request.POST.get('accion_tipo')

        # --- LÓGICA PARA CREAR SOLO DISCIPLINA ---
        if accion == 'crear_disciplina_unica':
            nombre_disc = request.POST.get('nombre_disciplina', '').strip()
            if nombre_disc:
                obj, created = Disciplina.objects.get_or_create(nombre_disciplina=nombre_disc)
                if created:
                    messages.success(request, f"Disciplina '{nombre_disc}' creada exitosamente.")
                else:
                    messages.info(request, f"La disciplina '{nombre_disc}' ya existe en el sistema.")
            return redirect('interfichas')

        # --- LÓGICA CREAR TORNEO ---
        elif accion == 'crear_torneo':
            id_disciplina = request.POST.get('disciplina_id')
            disciplina_obj = get_object_or_404(Disciplina, pk=id_disciplina)

            TorneoInterfichas.objects.create(
                nombre_torneo=request.POST.get('nombre'),
                fecha_torneo_fichas=request.POST.get('fecha'),
                lugar=request.POST.get('lugar'),
                disciplina=disciplina_obj
            )
            messages.success(request, "Torneo programado correctamente.")
            return redirect('interfichas')

        # --- LÓGICA INSCRIBIR EQUIPO ---
        elif accion == 'inscribir_equipo':
            torneo_id = request.POST.get('torneo_id')
            torneo_obj = get_object_or_404(TorneoInterfichas, pk=torneo_id)

            nuevo_equipo = EquipoInterfichas.objects.create(
                torneo=torneo_obj,
                nombre_equipo=request.POST.get('nombre_equipo'),
                capitan=request.POST.get('capitan'),
                ficha=request.POST.get('ficha'),
                programa=request.POST.get('programa'),
                disciplina=torneo_obj.disciplina,
                usuario_registra=request.user
            )

            jugadores_nombres = request.POST.getlist('jugadores[]')
            for nombre in jugadores_nombres:
                if nombre.strip():
                    JugadorEquipo.objects.create(nombre_completo=nombre, equipo=nuevo_equipo)

            messages.success(request, f"Equipo '{nuevo_equipo.nombre_equipo}' inscrito exitosamente.")
            return redirect('interfichas')

    return render(request, 'interfichas/interfichas.html', {
        'torneos': torneos,
        'equipos': equipos,
        'disciplinas': disciplinas,
        'PROGRAMAS_GLOBALES': PROGRAMAS_GLOBALES,
        'hoy': date.today().isoformat(),  # <--- Contexto agregado
    })


@login_required
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id)
    torneo.delete()
    messages.warning(request, "Torneo eliminado correctamente.")
    return redirect('interfichas')


@login_required
def editar_torneo(request):
    if request.method == 'POST':
        id_torneo = request.POST.get('id_editar')
        torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id_torneo)

        torneo.nombre_torneo = request.POST.get('nombre')
        id_disciplina = request.POST.get('disciplina_id')
        disciplina_obj = get_object_or_404(Disciplina, pk=id_disciplina)

        torneo.disciplina = disciplina_obj
        torneo.save()
        messages.info(request, "Torneo actualizado.")
    return redirect('interfichas')


# ================================================================
# HELPER: Calcula tabla de posiciones
# ================================================================

def _calcular_tabla(grupo):
    equipos = grupo.equipos.all()
    tabla = []
    for eq in equipos:
        partidos_local = PartidoInterfichas.objects.filter(grupo=grupo, jugado=True, equipo_local=eq)
        partidos_visitante = PartidoInterfichas.objects.filter(grupo=grupo, jugado=True, equipo_visitante=eq)

        pj = partidos_local.count() + partidos_visitante.count()
        pg = pe = pp = gf = gc = pts = 0

        for p in partidos_local:
            gf += p.goles_local
            gc += p.goles_visitante
            if p.goles_local > p.goles_visitante:
                pg += 1; pts += 3
            elif p.goles_local == p.goles_visitante:
                pe += 1; pts += 1
            else:
                pp += 1

        for p in partidos_visitante:
            gf += p.goles_visitante
            gc += p.goles_local
            if p.goles_visitante > p.goles_local:
                pg += 1; pts += 3
            elif p.goles_local == p.goles_visitante:
                pe += 1; pts += 1
            else:
                pp += 1

        tabla.append({
            'equipo': eq,
            'pj': pj, 'pg': pg, 'pe': pe, 'pp': pp,
            'gf': gf, 'gc': gc, 'dg': gf - gc, 'pts': pts,
        })

    tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))
    return tabla


# ================================================================
# GESTIÓN DE TORNEOS (FASES, GRUPOS, PARTIDOS)
# ================================================================

@login_required
def gestionar_torneo(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos = torneo.grupos.prefetch_related('equipos', 'partidos').all()
    equipos_total = torneo.equipos.all()

    grupos_con_tabla = []
    for g in grupos:
        tabla = _calcular_tabla(g)
        partidos_grupo = g.partidos.filter(fase='grupo').select_related(
            'equipo_local', 'equipo_visitante'
        ).order_by('fecha_partido', 'id')
        grupos_con_tabla.append({
            'grupo': g,
            'tabla': tabla,
            'partidos': partidos_grupo,
        })

    partidos_cuartos   = torneo.partidos.filter(fase='cuartos').select_related('equipo_local', 'equipo_visitante')
    partidos_semifinal = torneo.partidos.filter(fase='semifinal').select_related('equipo_local', 'equipo_visitante')
    partidos_final     = torneo.partidos.filter(fase='final').select_related('equipo_local', 'equipo_visitante')

    # Determinar fase actual
    fase_actual = 'inscripcion'
    if grupos.exists():
        fase_actual = 'grupos'
        partidos_grupo_total = PartidoInterfichas.objects.filter(torneo=torneo, fase='grupo')
        if partidos_grupo_total.exists() and not partidos_grupo_total.filter(jugado=False).exists():
            fase_actual = 'cuartos' if not partidos_cuartos.exists() else 'cuartos_activos'
    
    if partidos_cuartos.exists() and not partidos_cuartos.filter(jugado=False).exists():
        fase_actual = 'semifinal' if not partidos_semifinal.exists() else 'semifinal_activos'
    
    if partidos_semifinal.exists() and not partidos_semifinal.filter(jugado=False).exists():
        fase_actual = 'final' if not partidos_final.exists() else 'final_activa'
    
    if partidos_final.exists() and not partidos_final.filter(jugado=False).exists():
        fase_actual = 'terminado'

    return render(request, 'interfichas/gestion/gestionar_torneo.html', {
        'torneo': torneo,
        'equipos_total': equipos_total,
        'grupos_con_tabla': grupos_con_tabla,
        'partidos_cuartos': partidos_cuartos,
        'partidos_semifinal': partidos_semifinal,
        'partidos_final': partidos_final,
        'fase_actual': fase_actual,
        'num_equipos': equipos_total.count(),
    })


@login_required
@require_POST
def generar_grupos(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    torneo.grupos.all().delete()
    PartidoInterfichas.objects.filter(torneo=torneo).delete()

    equipos = list(torneo.equipos.all())
    random.shuffle(equipos)

    if len(equipos) < 4:
        messages.error(request, "Se necesitan al menos 4 equipos para generar grupos.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    letras = ['A', 'B', 'C', 'D']
    num_grupos = min(4, len(equipos) // 4)
    grupos_creados = []

    for i in range(num_grupos):
        g = GrupoInterfichas.objects.create(torneo=torneo, nombre_grupo=letras[i])
        equipos_grupo = equipos[i*4:(i+1)*4]
        g.equipos.set(equipos_grupo)
        grupos_creados.append((g, equipos_grupo))

    for g, eq_grupo in grupos_creados:
        for local, visitante in combinations(eq_grupo, 2):
            PartidoInterfichas.objects.create(
                torneo=torneo,
                grupo=g,
                fase='grupo',
                equipo_local=local,
                equipo_visitante=visitante,
            )

    messages.success(request, f"¡{num_grupos} grupos generados!")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@login_required
@require_POST
def registrar_resultado(request, partido_id):
    partido = get_object_or_404(PartidoInterfichas, pk=partido_id)
    torneo_id = partido.torneo.codigo_torneo_fichas

    goles_local = request.POST.get('goles_local')
    goles_visitante = request.POST.get('goles_visitante')
    fecha = request.POST.get('fecha_partido')
    hora = request.POST.get('hora_partido')

    if goles_local not in (None, '') and goles_visitante not in (None, ''):
        partido.goles_local = int(goles_local)
        partido.goles_visitante = int(goles_visitante)
        partido.jugado = True

    if fecha: partido.fecha_partido = fecha
    if hora: partido.hora_partido = hora

    partido.save()
    messages.success(request, "Resultado registrado correctamente.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@login_required
@require_POST
def generar_cuartos(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    PartidoInterfichas.objects.filter(torneo=torneo, fase='cuartos').delete()

    grupos = torneo.grupos.prefetch_related('equipos').all()
    clasificados = []

    for g in grupos:
        tabla = _calcular_tabla(g)
        if len(tabla) >= 2:
            clasificados.append([tabla[0]['equipo'], tabla[1]['equipo']])

    if len(clasificados) < 2:
        messages.error(request, "No hay suficientes clasificados.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    cruces = []
    if len(clasificados) == 4:
        cruces = [(clasificados[0][0], clasificados[1][1]), (clasificados[1][0], clasificados[0][1]),
                  (clasificados[2][0], clasificados[3][1]), (clasificados[3][0], clasificados[2][1])]
    elif len(clasificados) == 2:
        cruces = [(clasificados[0][0], clasificados[1][1]), (clasificados[1][0], clasificados[0][1])]
    else:
        todos = [eq for par in clasificados for eq in par]
        random.shuffle(todos)
        for i in range(0, len(todos) - 1, 2):
            cruces.append((todos[i], todos[i+1]))

    for local, visitante in cruces:
        PartidoInterfichas.objects.create(torneo=torneo, fase='cuartos', equipo_local=local, equipo_visitante=visitante)

    messages.success(request, "Cuartos de final generados.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@login_required
@require_POST
def generar_siguiente_fase(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    fase_origen = request.POST.get('fase_origen')
    fase_destino = 'semifinal' if fase_origen == 'cuartos' else 'final'

    PartidoInterfichas.objects.filter(torneo=torneo, fase=fase_destino).delete()
    partidos_origen = PartidoInterfichas.objects.filter(torneo=torneo, fase=fase_origen, jugado=True)

    ganadores = []
    for p in partidos_origen:
        if p.goles_local > p.goles_visitante: ganadores.append(p.equipo_local)
        elif p.goles_visitante > p.goles_local: ganadores.append(p.equipo_visitante)
        else: ganadores.append(random.choice([p.equipo_local, p.equipo_visitante]))

    if len(ganadores) < 2:
        messages.error(request, "No hay suficientes ganadores.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    random.shuffle(ganadores)
    for i in range(0, len(ganadores) - 1, 2):
        PartidoInterfichas.objects.create(torneo=torneo, fase=fase_destino, equipo_local=ganadores[i], equipo_visitante=ganadores[i+1])

    messages.success(request, f"{fase_destino.capitalize()} generada.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@login_required
@require_POST
def asignar_fecha_partido(request, partido_id):
    partido = get_object_or_404(PartidoInterfichas, pk=partido_id)
    partido.fecha_partido = request.POST.get('fecha_partido')
    partido.hora_partido = request.POST.get('hora_partido')
    partido.save()
    messages.success(request, "Fecha y hora actualizadas.")
    return redirect('gestionar_torneo', torneo_id=partido.torneo.pk)


# ================================================================
# CIERRE Y ARCHIVADO DE TORNEOS
# ================================================================

def cerrar_torneo(request, codigo_torneo):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=codigo_torneo)

    if torneo.estado == 'cerrado':
        messages.error(request, 'Este torneo ya está cerrado.')
        return redirect('interfichas')

    if request.method == 'POST':
        ganador_id = request.POST.get('ganador_id')
        accion = request.POST.get('accion')

        if not ganador_id:
            messages.error(request, 'Debes seleccionar un equipo ganador.')
            return redirect('interfichas')

        ganador = get_object_or_404(EquipoInterfichas, id=ganador_id, torneo=torneo)

        resultado, _ = ResultadoTorneo.objects.update_or_create(
            torneo=torneo,
            defaults={'ganador': ganador}
        )

        if accion == 'archivar':
            resultado.archivado = True
            resultado.save()
            torneo.estado = 'cerrado'
            torneo.save()
            messages.success(request, f'Torneo "{torneo.nombre_torneo}" cerrado y archivado correctamente.')
            return redirect('interfichas')

        messages.success(request, f'¡{ganador.nombre_equipo} declarado como ganador!')
        return redirect('interfichas')

    return redirect('interfichas')