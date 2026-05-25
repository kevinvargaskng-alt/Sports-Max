from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
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


def es_admin(user):
    return user.is_authenticated and user.is_staff

def solo_admin(view_func):
    decorated = user_passes_test(es_admin, login_url='interfichas')(view_func)
    return decorated


def _calcular_tabla(grupo):
    equipos = grupo.equipos.all()
    tabla = []
    for eq in equipos:
        partidos_local     = PartidoInterfichas.objects.filter(grupo=grupo, jugado=True, equipo_local=eq)
        partidos_visitante = PartidoInterfichas.objects.filter(grupo=grupo, jugado=True, equipo_visitante=eq)

        pj = pg = pe = pp = gf = gc = pts = 0

        for p in partidos_local:
            gf += p.goles_local
            gc += p.goles_visitante
            if p.goles_local > p.goles_visitante:    pg += 1; pts += 3
            elif p.goles_local == p.goles_visitante: pe += 1; pts += 1
            else:                                    pp += 1
            pj += 1

        for p in partidos_visitante:
            gf += p.goles_visitante
            gc += p.goles_local
            if p.goles_visitante > p.goles_local:    pg += 1; pts += 3
            elif p.goles_local == p.goles_visitante: pe += 1; pts += 1
            else:                                    pp += 1
            pj += 1

        tabla.append({
            'equipo': eq,
            'pj': pj, 'pg': pg, 'pe': pe, 'pp': pp,
            'gf': gf, 'gc': gc, 'dg': gf - gc, 'pts': pts,
        })

    tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))
    return tabla


def _ficha_duplicada(torneo, ficha, excluir_equipo_id=None):
    qs = EquipoInterfichas.objects.filter(torneo=torneo, ficha=ficha.strip())
    if excluir_equipo_id:
        qs = qs.exclude(pk=excluir_equipo_id)
    return qs.exists()


@login_required
def interfichas_list(request):
    admin = es_admin(request.user)

    if admin:
        torneos     = TorneoInterfichas.objects.all().order_by('-fecha_torneo_fichas')
        equipos     = EquipoInterfichas.objects.select_related('torneo', 'disciplina').all()
        disciplinas = Disciplina.objects.all().order_by('nombre_disciplina')
    else:
        torneos     = TorneoInterfichas.objects.exclude(estado='cerrado').order_by('-fecha_torneo_fichas')
        equipos     = EquipoInterfichas.objects.none()
        disciplinas = Disciplina.objects.none()

    if request.method == 'POST':
        accion = request.POST.get('accion_tipo', '').strip()

        if not admin and accion in ('crear_disciplina_unica', 'crear_torneo'):
            messages.error(request, 'No tienes permisos para realizar esta acción.')
            return redirect('interfichas')

        if accion == 'crear_disciplina_unica':
            nombre_disc   = request.POST.get('nombre_disciplina', '').strip()
            tipo_marcador = request.POST.get('tipo_marcador', 'goles').strip()
            if nombre_disc:
                obj, created = Disciplina.objects.get_or_create(
                    nombre_disciplina=nombre_disc,
                    defaults={'tipo_marcador': tipo_marcador}
                )
                if created:
                    messages.success(request, f"Disciplina '{nombre_disc}' creada.")
                else:
                    messages.info(request, f"La disciplina '{nombre_disc}' ya existe.")
            return redirect('interfichas')

        elif accion == 'crear_torneo':
            id_disc = request.POST.get('disciplina_id', '').strip()
            if not id_disc:
                messages.error(request, "Debes seleccionar una disciplina.")
                return redirect('interfichas')
            try:
                disc_obj = get_object_or_404(Disciplina, pk=int(id_disc))
            except (ValueError, Disciplina.DoesNotExist):
                messages.error(request, "Disciplina inválida.")
                return redirect('interfichas')

            TorneoInterfichas.objects.create(
                nombre_torneo=request.POST.get('nombre'),
                fecha_torneo_fichas=request.POST.get('fecha'),
                lugar=request.POST.get('lugar'),
                disciplina=disc_obj
            )
            messages.success(request, "Torneo programado correctamente.")
            return redirect('interfichas')

        elif accion == 'inscribir_equipo':
            torneo_id = (
                request.POST.get('torneo_id', '').strip()
                or request.POST.get('torneo_id_sel', '').strip()
            )
            if not torneo_id:
                messages.error(request, "Debes seleccionar un torneo.")
                return redirect('interfichas')
            try:
                torneo_obj = get_object_or_404(TorneoInterfichas, pk=int(torneo_id))
            except (ValueError, TorneoInterfichas.DoesNotExist):
                messages.error(request, "Torneo no encontrado.")
                return redirect('interfichas')

            if torneo_obj.estado == 'cerrado' and not admin:
                messages.error(request, "Este torneo ya está cerrado.")
                return redirect('interfichas')

            ficha = request.POST.get('ficha', '').strip()
            if not ficha:
                messages.error(request, "La ficha del capitán es obligatoria.")
                return redirect('interfichas')

            if _ficha_duplicada(torneo_obj, ficha):
                messages.error(
                    request,
                    f"La ficha '{ficha}' ya está inscrita en el torneo "
                    f"'{torneo_obj.nombre_torneo}'. Cada capitán solo puede "
                    f"inscribir un equipo por torneo."
                )
                return redirect('interfichas')

            nuevo_equipo = EquipoInterfichas.objects.create(
                torneo=torneo_obj,
                nombre_equipo=request.POST.get('nombre_equipo', '').strip(),
                capitan=request.POST.get('capitan', '').strip(),
                ficha=ficha,
                programa=request.POST.get('programa', '').strip(),
                disciplina=torneo_obj.disciplina,
                usuario_registra=request.user
            )
            for nombre in request.POST.getlist('jugadores[]'):
                if nombre.strip():
                    JugadorEquipo.objects.create(
                        nombre_completo=nombre.strip(),
                        equipo=nuevo_equipo
                    )

            messages.success(
                request,
                f"✅ Equipo '{nuevo_equipo.nombre_equipo}' inscrito exitosamente "
                f"en '{torneo_obj.nombre_torneo}'."
            )
            return redirect('interfichas')

    # ── Contexto extra para aprendiz ─────────────────────────────
    mis_equipos        = []
    mis_partidos       = PartidoInterfichas.objects.none()
    torneos_disponibles = torneos  # fallback: todos los abiertos

    if not admin:
        # 1. Obtenemos los equipos (como QuerySet para luego filtrar los partidos)
        mis_equipos_qs = (
            EquipoInterfichas.objects
            .filter(usuario_registra=request.user)
            .select_related('torneo', 'torneo__disciplina')
            .prefetch_related('jugadores')
        )
        
        # Convertimos a lista para poder inyectarle el grupo a cada equipo
        mis_equipos = list(mis_equipos_qs)
        
        # Buscamos en la base de datos a qué grupo pertenece cada equipo y se lo asignamos
        for eq in mis_equipos:
            grupo_asignado = GrupoInterfichas.objects.filter(torneo=eq.torneo, equipos=eq).first()
            eq.mi_grupo = grupo_asignado  # Creamos un atributo dinámico llamado 'mi_grupo'

        # 2. Obtenemos los partidos usando el QuerySet original
        mis_partidos = (
            PartidoInterfichas.objects
            .filter(
                Q(equipo_local__in=mis_equipos_qs) | Q(equipo_visitante__in=mis_equipos_qs)
            )
            .select_related('equipo_local', 'equipo_visitante', 'torneo')
            .order_by('fecha_partido', 'id')
        )

        # Torneos donde el usuario aún NO tiene equipo inscrito
        torneos_con_equipo = mis_equipos_qs.values_list('torneo_id', flat=True)
        torneos_disponibles = torneos.exclude(pk__in=torneos_con_equipo)

    return render(request, 'interfichas/interfichas.html', {
        'torneos':             torneos,
        'equipos':             equipos,
        'disciplinas':         disciplinas,
        'PROGRAMAS_GLOBALES':  PROGRAMAS_GLOBALES,
        'es_admin':            admin,
        # Aprendiz
        'mis_equipos':         mis_equipos,
        'mis_partidos':        mis_partidos,
        'torneos_disponibles': torneos_disponibles,
    })


@solo_admin
@require_POST
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id)
    nombre = torneo.nombre_torneo
    torneo.delete()
    messages.warning(request, f"Torneo '{nombre}' eliminado.")
    return redirect('interfichas')


@solo_admin
def editar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id)

    if request.method == 'POST':
        torneo.nombre_torneo       = request.POST.get('nombre', torneo.nombre_torneo).strip()
        torneo.lugar               = request.POST.get('lugar',  torneo.lugar).strip()
        torneo.fecha_torneo_fichas = request.POST.get('fecha',  torneo.fecha_torneo_fichas)
        id_disc = request.POST.get('disciplina_id', '').strip()
        if id_disc:
            try:
                torneo.disciplina = get_object_or_404(Disciplina, pk=int(id_disc))
            except (ValueError, Disciplina.DoesNotExist):
                messages.error(request, "Disciplina inválida.")
                return redirect('interfichas')
        torneo.save()
        messages.success(request, "Torneo actualizado correctamente.")
        return redirect('interfichas')

    return JsonResponse({
        'nombre':        torneo.nombre_torneo,
        'lugar':         torneo.lugar,
        'fecha':         torneo.fecha_torneo_fichas.strftime('%Y-%m-%d'),
        'disciplina_id': torneo.disciplina_id or '',
    })


@solo_admin
def gestionar_torneo(request, torneo_id):
    torneo        = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos        = torneo.grupos.prefetch_related('equipos', 'partidos').all()
    equipos_total = torneo.equipos.all()

    grupos_con_tabla = []
    for g in grupos:
        tabla    = _calcular_tabla(g)
        partidos = g.partidos.filter(fase='grupo').select_related(
            'equipo_local', 'equipo_visitante'
        ).order_by('fecha_partido', 'id')
        grupos_con_tabla.append({'grupo': g, 'tabla': tabla, 'partidos': partidos})

    partidos_cuartos   = torneo.partidos.filter(fase='cuartos').select_related('equipo_local', 'equipo_visitante')
    partidos_semifinal = torneo.partidos.filter(fase='semifinal').select_related('equipo_local', 'equipo_visitante')
    partidos_final     = torneo.partidos.filter(fase='final').select_related('equipo_local', 'equipo_visitante')

    fase_actual = 'inscripcion'
    if grupos.exists():
        fase_actual = 'grupos'
        pg_total = PartidoInterfichas.objects.filter(torneo=torneo, fase='grupo')
        if pg_total.exists() and not pg_total.filter(jugado=False).exists():
            fase_actual = 'cuartos' if not partidos_cuartos.exists() else 'cuartos_activos'

    if partidos_cuartos.exists() and not partidos_cuartos.filter(jugado=False).exists():
        fase_actual = 'semifinal' if not partidos_semifinal.exists() else 'semifinal_activos'

    if partidos_semifinal.exists() and not partidos_semifinal.filter(jugado=False).exists():
        fase_actual = 'final' if not partidos_final.exists() else 'final_activa'

    if partidos_final.exists() and not partidos_final.filter(jugado=False).exists():
        fase_actual = 'terminado'

    tipo_marcador = torneo.disciplina.tipo_marcador if torneo.disciplina else 'goles'

    return render(request, 'interfichas/gestion/gestionar_torneo.html', {
        'torneo':             torneo,
        'equipos_total':      equipos_total,
        'grupos_con_tabla':   grupos_con_tabla,
        'partidos_cuartos':   partidos_cuartos,
        'partidos_semifinal': partidos_semifinal,
        'partidos_final':     partidos_final,
        'fase_actual':        fase_actual,
        'num_equipos':        equipos_total.count(),
        'tipo_marcador':      tipo_marcador,
    })


@solo_admin
@require_POST
def generar_grupos(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    torneo.grupos.all().delete()
    PartidoInterfichas.objects.filter(torneo=torneo).delete()

    equipos = list(torneo.equipos.all())
    random.shuffle(equipos)

    if len(equipos) < 4:
        messages.error(request, "Se necesitan al menos 4 equipos.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    letras     = ['A', 'B', 'C', 'D']
    num_grupos = min(4, len(equipos) // 4)
    grupos_list = []

    for i in range(num_grupos):
        g = GrupoInterfichas.objects.create(torneo=torneo, nombre_grupo=letras[i])
        eq_grupo = equipos[i*4:(i+1)*4]
        g.equipos.set(eq_grupo)
        grupos_list.append((g, eq_grupo))

    for g, eq_grupo in grupos_list:
        for local, visitante in combinations(eq_grupo, 2):
            PartidoInterfichas.objects.create(
                torneo=torneo, grupo=g, fase='grupo',
                equipo_local=local, equipo_visitante=visitante
            )

    messages.success(request, f"¡{num_grupos} grupos generados con sus partidos!")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def registrar_resultado(request, partido_id):
    partido   = get_object_or_404(PartidoInterfichas, pk=partido_id)
    torneo_id = partido.torneo.codigo_torneo_fichas
    tipo      = partido.tipo_marcador

    fecha = request.POST.get('fecha_partido')
    hora  = request.POST.get('hora_partido')
    if fecha: partido.fecha_partido = fecha
    if hora:  partido.hora_partido  = hora

    if tipo == 'sets':
        sl_raw = request.POST.getlist('sets_local[]')
        sv_raw = request.POST.getlist('sets_visitante[]')
        try:
            sl = [int(x) for x in sl_raw if x.strip()]
            sv = [int(x) for x in sv_raw if x.strip()]
        except ValueError:
            messages.error(request, "Valores de sets inválidos.")
            return redirect('gestionar_torneo', torneo_id=torneo_id)

        if sl and sv and len(sl) == len(sv):
            partido.sets_local      = sl
            partido.sets_visitante  = sv
            partido.goles_local     = sum(1 for a, b in zip(sl, sv) if a > b)
            partido.goles_visitante = sum(1 for a, b in zip(sl, sv) if b > a)
            partido.jugado          = True
    else:
        gl = request.POST.get('goles_local', '').strip()
        gv = request.POST.get('goles_visitante', '').strip()
        if gl != '' and gv != '':
            try:
                partido.goles_local     = int(gl)
                partido.goles_visitante = int(gv)
                partido.jugado          = True
            except ValueError:
                messages.error(request, "Resultado inválido.")
                return redirect('gestionar_torneo', torneo_id=torneo_id)

    partido.save()
    messages.success(request, "Resultado guardado correctamente.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def generar_cuartos(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    PartidoInterfichas.objects.filter(torneo=torneo, fase='cuartos').delete()

    grupos       = torneo.grupos.prefetch_related('equipos').all()
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
        cruces = [
            (clasificados[0][0], clasificados[1][1]),
            (clasificados[1][0], clasificados[0][1]),
            (clasificados[2][0], clasificados[3][1]),
            (clasificados[3][0], clasificados[2][1]),
        ]
    elif len(clasificados) == 2:
        cruces = [
            (clasificados[0][0], clasificados[1][1]),
            (clasificados[1][0], clasificados[0][1]),
        ]
    else:
        todos = [eq for par in clasificados for eq in par]
        random.shuffle(todos)
        for i in range(0, len(todos) - 1, 2):
            cruces.append((todos[i], todos[i + 1]))

    for local, visitante in cruces:
        PartidoInterfichas.objects.create(
            torneo=torneo, fase='cuartos',
            equipo_local=local, equipo_visitante=visitante
        )

    messages.success(request, "Cuartos de final generados.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def generar_siguiente_fase(request, torneo_id):
    torneo       = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    fase_origen  = request.POST.get('fase_origen')
    fase_destino = 'semifinal' if fase_origen == 'cuartos' else 'final'

    PartidoInterfichas.objects.filter(torneo=torneo, fase=fase_destino).delete()
    partidos_origen = PartidoInterfichas.objects.filter(torneo=torneo, fase=fase_origen, jugado=True)

    ganadores = []
    for p in partidos_origen:
        if p.goles_local > p.goles_visitante:
            ganadores.append(p.equipo_local)
        elif p.goles_visitante > p.goles_local:
            ganadores.append(p.equipo_visitante)
        else:
            ganadores.append(random.choice([p.equipo_local, p.equipo_visitante]))

    if len(ganadores) < 2:
        messages.error(request, "No hay suficientes ganadores para la siguiente fase.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    random.shuffle(ganadores)
    for i in range(0, len(ganadores) - 1, 2):
        PartidoInterfichas.objects.create(
            torneo=torneo, fase=fase_destino,
            equipo_local=ganadores[i], equipo_visitante=ganadores[i + 1]
        )

    messages.success(request, f"{fase_destino.capitalize()} generada correctamente.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def asignar_fecha_partido(request, partido_id):
    partido = get_object_or_404(PartidoInterfichas, pk=partido_id)
    partido.fecha_partido = request.POST.get('fecha_partido')
    partido.hora_partido  = request.POST.get('hora_partido')
    partido.save()
    messages.success(request, "Fecha y hora actualizadas.")
    return redirect('gestionar_torneo', torneo_id=partido.torneo.pk)


@solo_admin
def cerrar_torneo(request, codigo_torneo):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=codigo_torneo)

    if torneo.estado == 'cerrado':
        messages.error(request, 'Este torneo ya está cerrado.')
        return redirect('interfichas')

    if request.method == 'POST':
        ganador_id = request.POST.get('ganador_id')
        accion     = request.POST.get('accion')

        if not ganador_id:
            messages.error(request, 'Debes seleccionar un equipo ganador.')
            return redirect('interfichas')

        try:
            ganador = get_object_or_404(EquipoInterfichas, id=int(ganador_id), torneo=torneo)
        except (ValueError, EquipoInterfichas.DoesNotExist):
            messages.error(request, "Equipo ganador inválido.")
            return redirect('interfichas')

        resultado, _ = ResultadoTorneo.objects.update_or_create(
            torneo=torneo, defaults={'ganador': ganador}
        )

        if accion == 'archivar':
            resultado.archivado = True
            resultado.save()
            torneo.estado = 'cerrado'
            torneo.save()
            messages.success(request, f'Torneo "{torneo.nombre_torneo}" cerrado y archivado.')
        else:
            messages.success(request, f'¡{ganador.nombre_equipo} declarado ganador!')

    return redirect('interfichas')


@solo_admin
def reporte_torneo(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos = torneo.grupos.prefetch_related('equipos').all()

    grupos_con_tabla = [
        {'grupo': g, 'tabla': _calcular_tabla(g)}
        for g in grupos
    ]

    return render(request, 'interfichas/reporte_torneo.html', {
        'torneo':             torneo,
        'grupos_con_tabla':   grupos_con_tabla,
        'partidos_cuartos':   torneo.partidos.filter(fase='cuartos').select_related('equipo_local', 'equipo_visitante'),
        'partidos_semifinal': torneo.partidos.filter(fase='semifinal').select_related('equipo_local', 'equipo_visitante'),
        'partidos_final':     torneo.partidos.filter(fase='final').select_related('equipo_local', 'equipo_visitante'),
    })