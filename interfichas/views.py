
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from django.core.files.base import ContentFile
from django.contrib.staticfiles import finders
import random
from itertools import combinations
from .models import (
    TorneoInterfichas, EquipoInterfichas, Disciplina,
    JugadorEquipo, GrupoInterfichas, PartidoInterfichas, ResultadoTorneo
)


PAISES_TORNEO = [
    "Argentina", "Brasil", "Francia", "España", "Inglaterra",
    "Alemania", "Portugal", "Países Bajos", "Colombia", "Uruguay",
    "Croacia", "Bélgica", "Noruega", "Japón", "Estados Unidos",
    "México", "Croacia"
]

PROGRAMAS_GLOBALES = [
    "Tecnología en Sistemas",
    "Administración de Empresas",
    "Contabilidad y Finanzas",
    "Diseño Gráfico",
    "Mecatrónica",
    "Salud Ocupacional",
    "Otro",
]

# ================================================================
# BANDERAS DEL MUNDIAL
# ================================================================
# IMPORTANTE: estas rutas son relativas a cualquier carpeta 'static/'
# de tus apps (o STATICFILES_DIRS). Debes colocar los archivos de
# imagen en: static/interfichas/banderas/<archivo>
# Ajusta los nombres de archivo si los tuyos son distintos.
BANDERAS_MUNDIAL = {
    "Argentina":      "interfichas/static/img/banderas/argentina.png",
    "Brasil":         "interfichas/static/img/banderas/brasil.png",
    "Francia":        "interfichas/static/img/banderas/francia.png",
    "España":         "interfichas/static/img/banderas/espana.png",
    "Inglaterra":     "interfichas/static/img/banderas/inglaterra.png",
    "Alemania":       "interfichas/static/img/banderas/alemania.png",
    "Portugal":       "interfichas/static/img/banderas/portugal.png",
    "Países Bajos":   "interfichas/static/img/banderas/paises_bajos.png",
    "Colombia":       "interfichas/static/img/banderas/colombia.png",
    "Uruguay":        "interfichas/static/img/banderas/uruguay.png",
    "Croacia":        "interfichas/static/img/banderas/croacia.png",
    "Bélgica":        "interfichas/static/img/banderas/belgica.png",
    "Noruega":        "interfichas/static/img/banderas/noruega.png",
    "Japón":          "interfichas/static/img/banderas/japon.png",
    "Estados Unidos": "interfichas/static/img/banderas/estados_unidos.png",
    "México":         "interfichas/static/img/banderas/mexico.png",
}


def asignar_escudo_por_pais(equipo, nombre_pais, forzar=False):
    """
    Busca la imagen de bandera correspondiente al país (usando los
    archivos estáticos del proyecto) y la guarda en el campo `escudo`
    del equipo.
    """
    if equipo.escudo and not forzar:
        return False

    ruta_relativa = BANDERAS_MUNDIAL.get(nombre_pais)
    if not ruta_relativa:
        return False

    # Probamos varias variantes de la ruta, porque finders.find() busca
    # DENTRO de la carpeta static/ de cada app (no incluye "static/" en
    # el argumento). Así evitamos que un typo en la ruta rompa todo en
    # silencio.
    candidatos = [
        ruta_relativa,
        ruta_relativa.replace('interfichas/static/', ''),
        ruta_relativa.replace('interfichas/', ''),
        ruta_relativa.split('/')[-1] and f"img/banderas/{os.path.basename(ruta_relativa)}",
    ]

    ruta_absoluta = None
    ruta_encontrada = ruta_relativa
    for candidato in candidatos:
        if not candidato:
            continue
        ruta_absoluta = finders.find(candidato)
        if ruta_absoluta:
            ruta_encontrada = candidato
            break

    if not ruta_absoluta:
        return False

    with open(ruta_absoluta, 'rb') as f:
        contenido = f.read()

    nombre_archivo = os.path.basename(ruta_encontrada)
    equipo.escudo.save(nombre_archivo, ContentFile(contenido), save=True)
    return True



from functools import wraps
from django.core.exceptions import PermissionDenied
import threading


def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'rol', '') in ['admin', 'instructor'])


def solo_admin(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_authenticated and (request.user.is_staff or user.is_superuser or getattr(request.user, 'rol', '') in ['admin', 'instructor'])):
            raise PermissionDenied("Acceso denegado. Se requieren permisos de administración o instructor.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def _calcular_tabla(grupo):
    equipos = grupo.equipos.all()

    # Partidos jugados del grupo
    partidos_jugados = grupo.partidos.filter(
        jugado=True
    ).select_related(
        'equipo_local',
        'equipo_visitante'
    )

    stats_map = {
        eq.pk: {
            'equipo': eq,
            'pj': 0,
            'pg': 0,
            'pe': 0,
            'pp': 0,
            'gf': 0,
            'gc': 0,
            'dg': 0,
            'pts': 0,

            # CP-24: acumulación de tarjetas
            'amarillas': 0,
            'rojas': 0,
            'azules': 0,
        }
        for eq in equipos
    }

    for p in partidos_jugados:
        local_id = p.equipo_local_id
        visit_id = p.equipo_visitante_id

        # ============================================================
        # EQUIPO LOCAL
        # ============================================================
        if local_id in stats_map:
            st = stats_map[local_id]

            st['pj'] += 1
            st['gf'] += p.goles_local
            st['gc'] += p.goles_visitante

            if p.goles_local > p.goles_visitante:
                st['pg'] += 1
                st['pts'] += 3
            elif p.goles_local == p.goles_visitante:
                st['pe'] += 1
                st['pts'] += 1
            else:
                st['pp'] += 1

            # CP-24: tarjetas recibidas como local
            st['amarillas'] += p.tarjetas_amarillas_local or 0
            st['rojas'] += p.tarjetas_rojas_local or 0
            st['azules'] += p.tarjetas_azules_local or 0

        # ============================================================
        # EQUIPO VISITANTE
        # ============================================================
        if visit_id in stats_map:
            st = stats_map[visit_id]

            st['pj'] += 1
            st['gf'] += p.goles_visitante
            st['gc'] += p.goles_local

            if p.goles_visitante > p.goles_local:
                st['pg'] += 1
                st['pts'] += 3
            elif p.goles_local == p.goles_visitante:
                st['pe'] += 1
                st['pts'] += 1
            else:
                st['pp'] += 1

            # CP-24: tarjetas recibidas como visitante
            st['amarillas'] += p.tarjetas_amarillas_visitante or 0
            st['rojas'] += p.tarjetas_rojas_visitante or 0
            st['azules'] += p.tarjetas_azules_visitante or 0

    # Diferencia de goles
    for st in stats_map.values():
        st['dg'] = st['gf'] - st['gc']

    tabla = list(stats_map.values())

    tabla.sort(
        key=lambda x: (
            -x['pts'],
            -x['dg'],
            -x['gf']
        )
    )

    return tabla


def _ficha_duplicada(torneo, ficha, excluir_equipo_id=None):
    qs = EquipoInterfichas.objects.filter(torneo=torneo, ficha=ficha.strip())
    if excluir_equipo_id:
        qs = qs.exclude(pk=excluir_equipo_id)
    return qs.exists()


def _reordenar_partidos_con_descanso(partidos_lista):
    """
    Algoritmo para ordenar partidos evitando que un equipo juegue de forma consecutiva.
    """
    if not partidos_lista:
        return []

    resultado = []
    # Mezclamos inicialmente para que no tengan siempre un patrón fijo de combinaciones
    random.shuffle(partidos_lista)

    partidos_restantes = partidos_lista.copy()

    # Insertar el primer partido de manera segura
    resultado.append(partidos_restantes.pop(0))

    intentos_fallidos = 0
    max_intentos = len(partidos_lista) * 2

    while partidos_restantes and intentos_fallidos < max_intentos:
        ultimo_partido = resultado[-1]
        equipos_ultimo_partido = {
            ultimo_partido['local'].pk, ultimo_partido['visitante'].pk}

        encontrado = False
        for i, partido in enumerate(partidos_restantes):
            # Comprobamos si el partido no comparte equipos con el último que se jugó
            if partido['local'].pk not in equipos_ultimo_partido and partido['visitante'].pk not in equipos_ultimo_partido:
                resultado.append(partidos_restantes.pop(i))
                encontrado = True
                break


        if not encontrado:
            # Si no hay ningún partido ideal disponible, sacamos uno de los restantes al azar
            # para evitar bucles infinitos en grupos muy pequeños
            resultado.append(partidos_restantes.pop(0))
            intentos_fallidos += 1

    return resultado


from django.core.mail import send_mail
from django.conf import settings


def enviar_notificacion_partido(partido, tipo_evento='programacion'):
    """
    Envía notificaciones por correo electrónico en un hilo en segundo plano (daemon thread)
    para evitar cualquier bloqueo en la respuesta de la solicitud HTTP.
    """
    def _envio_background():
        try:
            destinatarios = set()

            if partido.equipo_local and partido.equipo_local.usuario_registra and partido.equipo_local.usuario_registra.email:
                destinatarios.add(partido.equipo_local.usuario_registra.email)

            if partido.equipo_visitante and partido.equipo_visitante.usuario_registra and partido.equipo_visitante.usuario_registra.email:
                destinatarios.add(partido.equipo_visitante.usuario_registra.email)

            if not destinatarios:
                return

            disciplina_nombre = partido.torneo.disciplina.nombre_disciplina if (partido.torneo and partido.torneo.disciplina) else "Deporte"
            fase_label = partido.get_fase_display() if hasattr(partido, 'get_fase_display') else partido.fase
            fecha_str = partido.fecha_partido.strftime('%d/%m/%Y') if partido.fecha_partido else "Por confirmar"
            hora_str = partido.hora_partido.strftime('%H:%M') if partido.hora_partido else "Por confirmar"
            lugar_str = partido.torneo.lugar if partido.torneo else "Sede SENA"

            if tipo_evento == 'resultado':
                asunto = f"⚽ Resultado del Partido: {partido.equipo_local.nombre_equipo} ({partido.goles_local}) vs ({partido.goles_visitante}) {partido.equipo_visitante.nombre_equipo}"
                mensaje = (
                    f"¡Hola! Se ha registrado el resultado de tu partido en el SENA:\n\n"
                    f"🏆 Torneo: {partido.torneo.nombre_torneo} ({disciplina_nombre})\n"
                    f"⚔️ Encuentro: {partido.equipo_local.nombre_equipo} {partido.goles_local} - {partido.goles_visitante} {partido.equipo_visitante.nombre_equipo}\n"
                    f"📌 Fase: {fase_label}\n\n"
                    f"Ingresa a la plataforma para consultar la tabla de posiciones actualizada."
                )
            else:
                asunto = f"🏆 Próximo Partido: {partido.equipo_local.nombre_equipo} vs {partido.equipo_visitante.nombre_equipo}"
                mensaje = (
                    f"¡Hola! Te informamos que tu equipo tiene un partido programado en el SENA:\n\n"
                    f"🏆 Torneo: {partido.torneo.nombre_torneo} ({disciplina_nombre})\n"
                    f"⚔️ Encuentro: {partido.equipo_local.nombre_equipo} VS {partido.equipo_visitante.nombre_equipo}\n"
                    f"📌 Fase: {fase_label}\n"
                    f"📅 Fecha: {fecha_str}\n"
                    f"⏰ Hora: {hora_str}\n"
                    f"📍 Lugar: {lugar_str}\n\n"
                    f"Por favor preséntate con tu plantilla de jugadores. ¡Muchos éxitos!"
                )

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kevinvargaskng@gmail.com')
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=from_email,
                recipient_list=list(destinatarios),
                fail_silently=True
            )
        except Exception:
            pass

    threading.Thread(target=_envio_background, daemon=True).start()


@login_required
def interfichas_list(request):
    admin = es_admin(request.user)

    todos_equipos_qs = EquipoInterfichas.objects.select_related(
        'torneo', 'disciplina'
    ).prefetch_related('jugadores').all()

    grupos_rel = GrupoInterfichas.objects.prefetch_related('equipos').all()
    equipo_grupo_map = {}
    for g in grupos_rel:
        for eq in g.equipos.all():
            equipo_grupo_map[eq.pk] = g.nombre_grupo

    todos_equipos_list = list(todos_equipos_qs)
    for eq in todos_equipos_list:
        eq.nombre_grupo = equipo_grupo_map.get(eq.pk, '')

    # Reparación automática: si un equipo representa un país mundial y
    # todavía no tiene escudo (por ejemplo, quedó inscrito antes de
    # arreglar la ruta de banderas), se le asigna aquí mismo al cargar
    # el panel — sin necesidad de acción manual.
    for eq in todos_equipos_list:
        if not eq.escudo and eq.nombre_equipo in BANDERAS_MUNDIAL:
            asignar_escudo_por_pais(eq, eq.nombre_equipo)
        

    # Agrupar los equipos por Grupo para la visualización en bloques
    grupos_dict = {}
    for eq in todos_equipos_list:
        g_nombre = f"Grupo {eq.nombre_grupo}" if eq.nombre_grupo else "Sin Grupo Asignado"
        if g_nombre not in grupos_dict:
            grupos_dict[g_nombre] = []
        grupos_dict[g_nombre].append(eq)

    grupos_ordenados = []
    for g_nombre in sorted(grupos_dict.keys(), key=lambda x: (x == "Sin Grupo Asignado", x)):
        grupos_ordenados.append({
            'nombre_grupo': g_nombre,
            'equipos': grupos_dict[g_nombre],
            'total': len(grupos_dict[g_nombre])
        })

    if admin:
        torneos = TorneoInterfichas.objects.all().order_by('-fecha_torneo_fichas')
        equipos = todos_equipos_list
        disciplinas = Disciplina.objects.all().order_by('nombre_disciplina')
    else:
        torneos = TorneoInterfichas.objects.exclude(
            estado='cerrado').order_by('-fecha_torneo_fichas')
        equipos = todos_equipos_list
        disciplinas = Disciplina.objects.none()

    if request.method == 'POST':
        accion = request.POST.get('accion_tipo', '').strip()

        if not admin and accion in ('crear_disciplina_unica', 'crear_torneo'):
            messages.error(
                request, 'No tienes permisos para realizar esta acción.')
            return redirect('interfichas')

        if accion == 'crear_disciplina_unica':
            nombre_disc = request.POST.get('nombre_disciplina', '').strip()
            tipo_marcador = request.POST.get('tipo_marcador', 'goles').strip()
            if nombre_disc:
                obj, created = Disciplina.objects.get_or_create(
                    nombre_disciplina=nombre_disc,
                    defaults={'tipo_marcador': tipo_marcador}
                )
                if created:
                    messages.success(
                        request, f"Disciplina '{nombre_disc}' creada.")
                else:
                    messages.info(
                        request, f"La disciplina '{nombre_disc}' ya existe.")
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

            fecha_str = request.POST.get('fecha')
            if fecha_str:
                from datetime import datetime as dt_class
                from django.utils import timezone as django_timezone
                try:
                    fecha_val = dt_class.strptime(fecha_str, '%Y-%m-%d').date()
                    if fecha_val < django_timezone.localdate():
                        messages.error(request, "La fecha del torneo no puede ser de días anteriores.")
                        return redirect('interfichas')
                except Exception:
                    messages.error(request, "Fecha de torneo inválida.")
                    return redirect('interfichas')
            else:
                messages.error(request, "La fecha del torneo es obligatoria.")
                return redirect('interfichas')

            estado_torneo = request.POST.get('estado', 'activo').strip() or 'activo'
            horario_torneo = request.POST.get('horario', '08:00').strip() or '08:00'
            torneo_nuevo = TorneoInterfichas.objects.create(
                nombre_torneo=request.POST.get('nombre'),
                fecha_torneo_fichas=fecha_val,
                horario_torneo_fichas=horario_torneo,
                lugar=request.POST.get('lugar'),
                disciplina=disc_obj,
                estado=estado_torneo
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Torneo programado correctamente.',
                    'torneo_id': torneo_nuevo.pk,
                    'nombre': torneo_nuevo.nombre_torneo,
                    'fecha': str(torneo_nuevo.fecha_torneo_fichas),
                    'horario': str(torneo_nuevo.horario_torneo_fichas),
                    'estado': torneo_nuevo.estado
                }, status=201)
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
                torneo_obj = get_object_or_404(
                    TorneoInterfichas, pk=int(torneo_id))
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

            # Determinar si la disciplina es Fútbol o Fútsal (formato mundial)
            disc_nombre = torneo_obj.disciplina.nombre_disciplina.lower() if torneo_obj.disciplina else ""
            es_mundial = "fútbol" in disc_nombre or "futbol" in disc_nombre or "futsal" in disc_nombre

            if es_mundial:
                nombres_existentes = set(
                    torneo_obj.equipos.values_list('nombre_equipo', flat=True))
                nombre_equipo = ""
                for pais in PAISES_TORNEO:
                    if pais not in nombres_existentes:
                        nombre_equipo = pais
                        break
                if not nombre_equipo:
                    nombre_equipo = f"Equipo {torneo_obj.equipos.count() + 1}"
            else:
                nombre_equipo = request.POST.get('nombre_equipo', '').strip()
                if not nombre_equipo:
                    nombre_equipo = f"Equipo {torneo_obj.equipos.count() + 1}"

            nuevo_equipo = EquipoInterfichas.objects.create (
                torneo=torneo_obj,
                nombre_equipo=nombre_equipo,
                capitan=request.POST.get('capitan', '').strip(),
                ficha=ficha,
                programa=request.POST.get('programa', '').strip(),
                disciplina=torneo_obj.disciplina,
                usuario_registra=request.user,
            )

            # Guardar planilla de inscripción (archivo)
            planilla_file = request.FILES.get('planilla_inscripcion')
            if planilla_file:
                nuevo_equipo.planilla_inscripcion = planilla_file
                nuevo_equipo.save()

            # Asignación automática del escudo (bandera del país) para
            # torneos temática mundial. Ya no se sube manualmente.
            if es_mundial:
                asignar_escudo_por_pais(nuevo_equipo, nombre_equipo)

            # Guardar jugadores con documento y consentimiento
            nombres_jugadores = request.POST.getlist('jugadores[]')
            documentos_jugadores = request.POST.getlist('documentos[]')

            for idx, nombre in enumerate(nombres_jugadores):
                if nombre.strip():
                    doc = ''
                    if idx < len(documentos_jugadores):
                        doc = documentos_jugadores[idx].strip()

                    jugador = JugadorEquipo.objects.create(
                        nombre_completo=nombre.strip(),
                        numero_documento=doc,
                        equipo=nuevo_equipo
                    )

                    # Consentimiento informado individual
                    consent_key = f'consentimiento_{idx}'
                    consent_file = request.FILES.get(consent_key)
                    if consent_file:
                        jugador.consentimiento_informado = consent_file
                        jugador.save()

            messages.success(
                request,
                f"✅ Equipo '{nuevo_equipo.nombre_equipo}' inscrito exitosamente "
                f"en '{torneo_obj.nombre_torneo}'."
            )
            return redirect('interfichas')

    mis_equipos = []
    mis_partidos = PartidoInterfichas.objects.none()
    torneos_disponibles = torneos
    total_equipos_inscritos = sum(t.equipos.count() for t in torneos)

    if not admin:
        mis_equipos_qs = (
            EquipoInterfichas.objects
            .filter(usuario_registra=request.user)
            .select_related('torneo', 'torneo__disciplina')
            .prefetch_related('jugadores')
        )
        mis_equipos = list(mis_equipos_qs)
        for eq in mis_equipos:
            eq.mi_grupo = equipo_grupo_map.get(eq.pk, '')

        mis_partidos = (
            PartidoInterfichas.objects
            .filter(
                Q(equipo_local__in=mis_equipos_qs) | Q(
                    equipo_visitante__in=mis_equipos_qs)
            )
            .select_related('equipo_local', 'equipo_visitante', 'torneo')
            .order_by('fecha_partido', 'id')
        )

        torneos_con_equipo = mis_equipos_qs.values_list('torneo_id', flat=True)
        torneos_disponibles = torneos.exclude(pk__in=torneos_con_equipo)
        

    context = {
        'torneos':             torneos,
        'equipos':             equipos,
        'todos_equipos':       todos_equipos_list,
        'grupos_ordenados':    grupos_ordenados,
        'disciplinas':         disciplinas,
        'es_admin':            admin,
        'mis_equipos':         mis_equipos,
        'mis_partidos':        mis_partidos,
        'torneos_disponibles': torneos_disponibles,
        'total_equipos_inscritos': total_equipos_inscritos,
    }
    return render(request, 'interfichas/interfichas.html', context)


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
        torneo.nombre_torneo = request.POST.get(
            'nombre', torneo.nombre_torneo).strip()
        torneo.lugar = request.POST.get('lugar',  torneo.lugar).strip()
        
        fecha_str = request.POST.get('fecha')
        if fecha_str:
            from datetime import datetime as dt_class
            from django.utils import timezone as django_timezone
            try:
                fecha_val = dt_class.strptime(fecha_str, '%Y-%m-%d').date()
                if fecha_val < django_timezone.localdate():
                    messages.error(request, "La fecha del torneo no puede ser de días anteriores.")
                    return redirect('interfichas')
                torneo.fecha_torneo_fichas = fecha_val
            except Exception:
                messages.error(request, "Fecha de torneo inválida.")
                return redirect('interfichas')

        id_disc = request.POST.get('disciplina_id', '').strip()
        if id_disc:
            try:
                torneo.disciplina = get_object_or_404(
                    Disciplina, pk=int(id_disc))
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
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    grupos = torneo.grupos.prefetch_related('equipos', 'partidos').all()
    equipos_total = torneo.equipos.all()

    grupos_con_tabla = []
    for g in grupos:
        tabla = _calcular_tabla(g)
        partidos = g.partidos.filter(fase='grupo').select_related(
            'equipo_local', 'equipo_visitante'
        ).order_by('fecha_partido', 'id')
        grupos_con_tabla.append(
            {'grupo': g, 'tabla': tabla, 'partidos': partidos})

    partidos_cuartos = torneo.partidos.filter(
        fase='cuartos').select_related('equipo_local', 'equipo_visitante')
    partidos_semifinal = torneo.partidos.filter(
        fase='semifinal').select_related('equipo_local', 'equipo_visitante')
    partidos_final = torneo.partidos.filter(
        fase='final').select_related('equipo_local', 'equipo_visitante')

    fase_actual = 'inscripcion'
    if grupos.exists():
        fase_actual = 'grupos'
        pg_total = PartidoInterfichas.objects.filter(
            torneo=torneo, fase='grupo')
        if pg_total.exists() and not pg_total.filter(jugado=False).exists():
            fase_actual = 'cuartos' if not partidos_cuartos.exists() else 'cuartos_activos'

    if partidos_cuartos.exists() and not partidos_cuartos.filter(jugado=False).exists():
        fase_actual = 'semifinal' if not partidos_semifinal.exists() else 'semifinal_activos'

    if partidos_semifinal.exists() and not partidos_semifinal.filter(jugado=False).exists():
        fase_actual = 'final' if not partidos_final.exists() else 'final_activa'

    if partidos_final.exists() and not partidos_final.filter(jugado=False).exists():
        fase_actual = 'terminado'

    tipo_marcador = torneo.disciplina.tipo_marcador if torneo.disciplina else 'goles'

    num_eq = equipos_total.count()

    # Opciones de número de grupos: de 1 hasta min(8, num_eq // 2)
    max_grupos_posibles = min(8, num_eq // 2) if num_eq >= 2 else 1
    num_grupos_opciones = list(range(1, max_grupos_posibles + 1))

    # Para re-sorteo manual: usar grupos actuales o máximo posible
    letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    num_grupos_actuales = grupos.count() if grupos.exists() else min(4, num_eq // 4)
    grupos_manual_range = [{'letra': letras[i]}
                           for i in range(min(8, max_grupos_posibles))]

    context = {
        'torneo':              torneo,
        'equipos_total':       equipos_total,
        'grupos_con_tabla':    grupos_con_tabla,
        'partidos_cuartos':    partidos_cuartos,
        'partidos_semifinal':  partidos_semifinal,
        'partidos_final':      partidos_final,
        'fase_actual':         fase_actual,
        'num_equipos':         num_eq,
        'tipo_marcador':       tipo_marcador,
        'PAISES_TORNEO':       PAISES_TORNEO,
        'PROGRAMAS_GLOBALES':  PROGRAMAS_GLOBALES,
        # Configurador de grupos
        'num_grupos_opciones': num_grupos_opciones,
        'grupos_manual_range': grupos_manual_range,
    }
    return render(request, 'interfichas/gestion/gestionar_torneo.html', context)


@solo_admin
@require_POST
def generar_grupos(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    torneo.grupos.all().delete()
    PartidoInterfichas.objects.filter(torneo=torneo).delete()

    equipos = list(torneo.equipos.all())
    random.shuffle(equipos)

    # Leer configuración del POST
    try:
        num_grupos = int(request.POST.get('num_grupos', 0))
        eq_por_grupo = int(request.POST.get('equipos_por_grupo', 0))
    except ValueError:
        num_grupos = eq_por_grupo = 0

    # Fallback automático si los parámetros no son válidos
    if num_grupos < 1 or eq_por_grupo < 2:
        eq_por_grupo = 4
        num_grupos = min(4, len(equipos) // 4)

    necesarios = num_grupos * eq_por_grupo
    if len(equipos) < necesarios:
        messages.error(
            request,
            f"Se necesitan al menos {necesarios} equipos para {num_grupos} grupo(s) "
            f"de {eq_por_grupo} equipos. Actualmente hay {len(equipos)}."
        )
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    grupos_list = []

    for i in range(num_grupos):
        g = GrupoInterfichas.objects.create(
            torneo=torneo, nombre_grupo=letras[i])
        eq_grupo = equipos[i * eq_por_grupo:(i + 1) * eq_por_grupo]
        g.equipos.set(eq_grupo)
        grupos_list.append((g, eq_grupo))

    # Recopilar todos los partidos generados en los grupos
    partidos_temporales = []
    for g, eq_grupo in grupos_list:
        for local, visitante in combinations(eq_grupo, 2):
            partidos_temporales.append({
                'grupo': g,
                'local': local,
                'visitante': visitante
            })

    # Aplicamos el filtro de descanso inteligente
    partidos_ordenados = _reordenar_partidos_con_descanso(partidos_temporales)

    # Guardamos en la base de datos con el nuevo orden distribuido
    for p in partidos_ordenados:
        PartidoInterfichas.objects.create(
            torneo=torneo, grupo=p['grupo'], fase='grupo',
            equipo_local=p['local'], equipo_visitante=p['visitante']
        )

    messages.success(
        request,
        f"¡{num_grupos} grupo(s) de {eq_por_grupo} equipos generados con partidos alternados correctamente!"
    )
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def generar_grupos_manual(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    torneo.grupos.all().delete()
    PartidoInterfichas.objects.filter(torneo=torneo).delete()

    try:
        eq_por_grupo = int(request.POST.get('equipos_por_grupo', 4))
    except ValueError:
        eq_por_grupo = 4

    letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    grupos_creados = []
    equipos_usados = set()

    for letra in letras:
        ids = [v for v in request.POST.getlist(
            f'grupo_{letra}[]') if v.strip()]
        if not ids:
            continue

        if len(ids) != eq_por_grupo:
            messages.error(
                request,
                f"El Grupo {letra} necesita exactamente {eq_por_grupo} equipo(s). "
                f"Tiene {len(ids)}."
            )
            return redirect('gestionar_torneo', torneo_id=torneo_id)

        for eid in ids:
            if eid in equipos_usados:
                messages.error(
                    request, "Un equipo aparece en más de un grupo. Corrige la asignación.")
                return redirect('gestionar_torneo', torneo_id=torneo_id)
            equipos_usados.add(eid)

        try:
            equipos_grupo = [
                get_object_or_404(EquipoInterfichas,
                                  pk=int(eid), torneo=torneo)
                for eid in ids
            ]
        except (ValueError, EquipoInterfichas.DoesNotExist):
            messages.error(request, f"Equipo inválido en Grupo {letra}.")
            return redirect('gestionar_torneo', torneo_id=torneo_id)

        g = GrupoInterfichas.objects.create(torneo=torneo, nombre_grupo=letra)
        g.equipos.set(equipos_grupo)
        grupos_creados.append((g, equipos_grupo))

    if not grupos_creados:
        messages.error(
            request, "No se asignó ningún equipo. Completa la asignación manual.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    # Recopilar partidos de la asignación manual
    partidos_temporales = []
    for g, eq_grupo in grupos_creados:
        for local, visitante in combinations(eq_grupo, 2):
            partidos_temporales.append({
                'grupo': g,
                'local': local,
                'visitante': visitante
            })

    # Aplicamos el filtro de descanso inteligente
    partidos_ordenados = _reordenar_partidos_con_descanso(partidos_temporales)

    # Guardamos en la base de datos
    for p in partidos_ordenados:
        PartidoInterfichas.objects.create(
            torneo=torneo, grupo=p['grupo'], fase='grupo',
            equipo_local=p['local'], equipo_visitante=p['visitante']
        )

    messages.success(
        request,
        f"¡{len(grupos_creados)} grupo(s) de {eq_por_grupo} equipos creados manualmente con partidos alternados!"
    )
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def registrar_resultado(request, partido_id):
    partido = get_object_or_404(PartidoInterfichas, pk=partido_id)
    torneo_id = partido.torneo.codigo_torneo_fichas
    tipo = partido.tipo_marcador
    print("TIPO MARCADOR:", repr(tipo))

    fecha = request.POST.get('fecha_partido')
    hora = request.POST.get('hora_partido')
    if fecha:
        partido.fecha_partido = fecha
    if hora:
        partido.hora_partido = hora

    # ── Regla de integridad: "No aplica" es EXCLUSIVO para Ajedrez ──
    es_ajedrez = (tipo == 'no_aplica')
    intento_no_aplica = request.POST.get('no_aplica') == 'on'

    if intento_no_aplica and not es_ajedrez:
        messages.error(
            request,
            "⛔ La opción 'No aplica' es exclusiva para Ajedrez. "
            "Debes registrar el puntaje numérico correspondiente para esta disciplina."
        )
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    if es_ajedrez:
        # Ajedrez: el resultado se marca indicando quién ganó (local/visitante/empate)
        ganador = request.POST.get('ganador_ajedrez', '').strip()
        partido.no_aplica = True
        if ganador == 'local':
            partido.goles_local = 1
            partido.goles_visitante = 0
            partido.jugado = True
        elif ganador == 'visitante':
            partido.goles_local = 0
            partido.goles_visitante = 1
            partido.jugado = True
        elif ganador == 'empate':
            partido.goles_local = 0
            partido.goles_visitante = 0
            partido.jugado = True
        # Si no eligió ganador, solo guarda fecha/hora

    elif tipo == 'sets':
        sl_raw = request.POST.getlist('sets_local[]')
        sv_raw = request.POST.getlist('sets_visitante[]')
        try:
            sl = [int(x) for x in sl_raw if x.strip()]
            sv = [int(x) for x in sv_raw if x.strip()]
        except ValueError:
            messages.error(request, "Valores de sets inválidos.")
            return redirect('gestionar_torneo', torneo_id=torneo_id)

        if sl and sv and len(sl) == len(sv):
            # CP-27.2: Validar exigencia de diferencia mínima de dos puntos en cierre de cada set
            for i, (a, b) in enumerate(zip(sl, sv)):
                if abs(a - b) < 2:
                    messages.error(request, f"Error en el Set {i+1}: Debe haber una diferencia mínima de 2 puntos para cerrar el set ({a}-{b}).")
                    return redirect('gestionar_torneo', torneo_id=torneo_id)

            partido.sets_local = sl
            partido.sets_visitante = sv
            # CP-27.1: Cálculo automático de ganador por mayoría de sets
            partido.goles_local = sum(1 for a, b in zip(sl, sv) if a > b)
            partido.goles_visitante = sum(1 for a, b in zip(sl, sv) if b > a)
            partido.jugado = True
    else:
        # Goles / Puntos — requiere puntaje numérico obligatorio
        gl = request.POST.get('goles_local', '').strip()
        gv = request.POST.get('goles_visitante', '').strip()
        if gl != '' and gv != '':
            try:
                partido.goles_local = int(gl)
                partido.goles_visitante = int(gv)
                partido.jugado = True
            except ValueError:
                messages.error(request, "Resultado inválido. Ingresa valores numéricos.")
                return redirect('gestionar_torneo', torneo_id=torneo_id)

    # Tarjetas y sanciones solo para disciplinas con goles (fútbol, fútsal)
    if tipo == 'goles':
        try:
            partido.tarjetas_amarillas_local = int(
                request.POST.get('amarillas_local', 0) or 0)
            partido.tarjetas_amarillas_visitante = int(
                request.POST.get('amarillas_visitante', 0) or 0)
            partido.tarjetas_rojas_local = int(
                request.POST.get('rojas_local', 0) or 0)
            partido.tarjetas_rojas_visitante = int(
                request.POST.get('rojas_visitante', 0) or 0)
            partido.tarjetas_azules_local = int(
                request.POST.get('azules_local', 0) or 0)
            partido.tarjetas_azules_visitante = int(
                request.POST.get('azules_visitante', 0) or 0)
        except ValueError:
            pass
        partido.detalles_sanciones = request.POST.get(
            'detalles_sanciones', '').strip()

    partido.save()
    messages.success(request, "Resultado guardado correctamente.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
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
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    fase_origen = request.POST.get('fase_origen')
    fase_destino = 'semifinal' if fase_origen == 'cuartos' else 'final'

    PartidoInterfichas.objects.filter(
        torneo=torneo, fase=fase_destino).delete()
    partidos_origen = PartidoInterfichas.objects.filter(
        torneo=torneo, fase=fase_origen, jugado=True)

    ganadores = []
    for p in partidos_origen:
        if p.goles_local > p.goles_visitante:
            ganadores.append(p.equipo_local)
        elif p.goles_visitante > p.goles_local:
            ganadores.append(p.equipo_visitante)
        else:
            ganadores.append(random.choice(
                [p.equipo_local, p.equipo_visitante]))

    if len(ganadores) < 2:
        messages.error(
            request, "No hay suficientes ganadores para la siguiente fase.")
        return redirect('gestionar_torneo', torneo_id=torneo_id)

    random.shuffle(ganadores)
    for i in range(0, len(ganadores) - 1, 2):
        PartidoInterfichas.objects.create(
            torneo=torneo, fase=fase_destino,
            equipo_local=ganadores[i], equipo_visitante=ganadores[i + 1]
        )

    messages.success(
        request, f"{fase_destino.capitalize()} generada correctamente.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def asignar_fecha_partido(request, partido_id):
    partido = get_object_or_404(PartidoInterfichas, pk=partido_id)
    fecha_str = request.POST.get('fecha_partido')
    if fecha_str:
        from datetime import datetime as dt_class
        from django.utils import timezone as django_timezone
        try:
            fecha_val = dt_class.strptime(fecha_str, '%Y-%m-%d').date()
            if fecha_val < django_timezone.localdate():
                messages.error(request, "La fecha del partido no puede ser de días anteriores.")
                return redirect('gestionar_torneo', torneo_id=partido.torneo.pk)
            partido.fecha_partido = fecha_val
        except Exception:
            messages.error(request, "Fecha de partido inválida.")
            return redirect('gestionar_torneo', torneo_id=partido.torneo.pk)
    partido.hora_partido = request.POST.get('hora_partido')
    partido.save()

    # Notificar a los equipos por correo electrónico
    enviar_notificacion_partido(partido, 'programacion')

    messages.success(request, "Fecha y hora actualizadas y notificación enviada por correo.")
    return redirect('gestionar_torneo', torneo_id=partido.torneo.pk)


@solo_admin
def cerrar_torneo(request, codigo_torneo):
    torneo = get_object_or_404(
        TorneoInterfichas, codigo_torneo_fichas=codigo_torneo)

    if torneo.estado == 'cerrado':
        messages.error(request, 'Este torneo ya está cerrado.')
        return redirect('interfichas')

    if request.method == 'POST':
        ganador_id = request.POST.get('ganador_id')
        subcampeon_id = request.POST.get('subcampeon_id')
        valla_id = request.POST.get('valla_menos_vencida_id')
        juego_limpio_id = request.POST.get('balance_juego_limpio_id')
        accion = request.POST.get('accion')

        if not ganador_id:
            messages.error(request, 'Debes seleccionar un equipo ganador.')
            return redirect('interfichas')

        try:
            ganador = get_object_or_404(EquipoInterfichas, id=int(ganador_id), torneo=torneo)
            subcampeon = EquipoInterfichas.objects.filter(id=int(subcampeon_id), torneo=torneo).first() if subcampeon_id else None
            valla = EquipoInterfichas.objects.filter(id=int(valla_id), torneo=torneo).first() if valla_id else None
            juego_limpio = EquipoInterfichas.objects.filter(id=int(juego_limpio_id), torneo=torneo).first() if juego_limpio_id else None
        except (ValueError, EquipoInterfichas.DoesNotExist):
            messages.error(request, "Datos de equipos inválidos.")
            return redirect('interfichas')

        defaults = {
            'ganador': ganador,
            'subcampeon': subcampeon,
            'valla_menos_vencida': valla,
            'balance_juego_limpio': juego_limpio
        }

        resultado, _ = ResultadoTorneo.objects.update_or_create(
            torneo=torneo, defaults=defaults
        )

        if accion == 'archivar':
            resultado.archivado = True
            resultado.save()
            torneo.estado = 'cerrado'
            torneo.save()
            messages.success(
                request, f'Torneo "{torneo.nombre_torneo}" cerrado y archivado.')
        else:
            messages.success(
                request, f'¡{ganador.nombre_equipo} declarado ganador!')

    return redirect('interfichas')


@solo_admin
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
    return render(request, 'interfichas/reporte_torneo.html', context)


@solo_admin
def editar_equipo(request, equipo_id):
    equipo = get_object_or_404(EquipoInterfichas, pk=equipo_id)
    
    if request.method == 'POST':
        equipo.nombre_equipo = request.POST.get('nombre_equipo', equipo.nombre_equipo).strip()
        equipo.capitan = request.POST.get('capitan', equipo.capitan).strip()
        
        ficha_val = request.POST.get('ficha')
        if ficha_val is not None:
            equipo.ficha = ficha_val.strip() if isinstance(ficha_val, str) else ficha_val
            
        equipo.programa = request.POST.get('programa', equipo.programa).strip()
        
        # Guardar / actualizar archivos si vienen en la petición
        if 'planilla_inscripcion' in request.FILES:
            equipo.planilla_inscripcion = request.FILES['planilla_inscripcion']

        if 'escudo' in request.FILES:
            equipo.escudo = request.FILES['escudo']

        # ¡CRÍTICO: Faltaba persistir los cambios!
        equipo.save()
        messages.success(
            request, f"Equipo '{equipo.nombre_equipo}' actualizado correctamente.")
        return redirect('gestionar_torneo', torneo_id=equipo.torneo.pk)

    return JsonResponse({
        'id': equipo.pk,
        'nombre_equipo': equipo.nombre_equipo,
        'capitan': equipo.capitan,
        'ficha': equipo.ficha,
        'programa': equipo.programa,
        'escudo': equipo.escudo.url if equipo.escudo else None,
        'planilla_inscripcion': equipo.planilla_inscripcion.url if equipo.planilla_inscripcion else None,
    })

@solo_admin
@require_POST
def eliminar_equipo(request, equipo_id):
    equipo = get_object_or_404(EquipoInterfichas, pk=equipo_id)
    torneo_id = equipo.torneo.pk
    nombre = equipo.nombre_equipo
    equipo.delete()
    messages.warning(request, f"Equipo '{nombre}' eliminado del torneo.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def asignar_paises_torneo(request, torneo_id):
    torneo = get_object_or_404(TorneoInterfichas, pk=torneo_id)
    equipos = list(torneo.equipos.all().order_by(
        'fecha_inscripcion', 'codigo_equipo_interfichas'))
    for i, eq in enumerate(equipos):
        eq.nombre_equipo = PAISES_TORNEO[i] if i < len(
            PAISES_TORNEO) else f"Equipo {i + 1}"
        eq.save()
        # Mantener el escudo sincronizado con el nuevo nombre de país asignado
        asignar_escudo_por_pais(eq, eq.nombre_equipo, forzar=True)
    messages.success(
        request, "Nombres de países asignados a los equipos en orden.")
    return redirect('gestionar_torneo', torneo_id=torneo_id)


@solo_admin
@require_POST
def asignar_escudos_faltantes(request, torneo_id=None):
    """
    Recorre los equipos (opcionalmente filtrados por torneo) cuyo
    nombre coincide con un país mapeado en BANDERAS_MUNDIAL y que
    todavía no tienen escudo, y les asigna la bandera correspondiente.
    Útil para "reparar" equipos inscritos antes de esta funcionalidad.
    """
    equipos_qs = EquipoInterfichas.objects.filter(
        nombre_equipo__in=BANDERAS_MUNDIAL.keys()
    ).filter(Q(escudo='') | Q(escudo__isnull=True))

    if torneo_id:
        equipos_qs = equipos_qs.filter(torneo_id=torneo_id)

    total = 0
    for eq in equipos_qs:
        if asignar_escudo_por_pais(eq, eq.nombre_equipo):
            total += 1

    messages.success(request, f"Se asignaron {total} escudo(s) automáticamente.")
    if torneo_id:
        return redirect('gestionar_torneo', torneo_id=torneo_id)
    return redirect('interfichas')


# ============================================================
#  API: OCR DE PLANILLA DE INSCRIPCIÓN (Gemini Vision)
# ============================================================
import json as json_stdlib
import base64
import requests as http_requests


@login_required
@require_POST
def ocr_planilla_api(request):
    """
    Recibe una imagen o PDF de planilla de inscripción y usa Gemini 2.5 Flash
    para extraer nombres y documentos de los jugadores vía OCR multimodal.
    Retorna JSON: { "jugadores": [ { "nombre": "...", "documento": "..." }, ... ] }
    """
    archivo = request.FILES.get('planilla')
    if not archivo:
        return JsonResponse({'error': 'No se recibió ningún archivo.'}, status=400)

    # Validar tipo de archivo
    tipos_permitidos = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
    if archivo.content_type not in tipos_permitidos:
        return JsonResponse({
            'error': 'Formato no soportado. Sube una imagen (JPG, PNG, WEBP) o PDF.'
        }, status=400)

    # Validar tamaño (máx. 10MB)
    if archivo.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'El archivo supera el límite de 10MB.'}, status=400)

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'API Key de Gemini no configurada en el servidor.'}, status=500)

    try:
        # Leer y codificar en base64
        contenido = archivo.read()
        b64_data = base64.b64encode(contenido).decode('utf-8')

        # Determinar MIME type
        mime_type = archivo.content_type

        # Construir prompt estructurado para Gemini
        prompt_ocr = """Eres un sistema OCR especializado. Analiza esta imagen/documento de planilla de inscripción deportiva.

EXTRAE todos los nombres de jugadores y sus números de documento de identidad que aparezcan.

REGLAS:
- Si un campo está ilegible, coloca "ILEGIBLE" como valor.
- Si no hay número de documento visible para un jugador, coloca cadena vacía "".
- Devuelve ÚNICAMENTE un JSON válido, sin texto adicional, sin markdown.

FORMATO DE RESPUESTA (JSON estricto):
{
  "jugadores": [
    {"nombre": "Nombre Completo del Jugador", "documento": "1234567890"},
    {"nombre": "Otro Jugador", "documento": ""}
  ]
}

Si no puedes identificar ningún jugador, devuelve: {"jugadores": []}"""

        # Llamada a Gemini 2.5 Flash con contenido multimodal
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_ocr},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            }
        }

        resp = http_requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Extraer texto de respuesta
        texto_respuesta = ''
        try:
            texto_respuesta = data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return JsonResponse({'error': 'Gemini no devolvió una respuesta válida.'}, status=500)

        # Limpiar posibles bloques markdown
        texto_limpio = texto_respuesta.strip()
        if texto_limpio.startswith('```'):
            lineas = texto_limpio.split('\n')
            # Remover primera y última línea (```json y ```)
            lineas = [l for l in lineas if not l.strip().startswith('```')]
            texto_limpio = '\n'.join(lineas)

        resultado = json_stdlib.loads(texto_limpio)

        # Validar estructura
        if 'jugadores' not in resultado:
            resultado = {'jugadores': []}

        return JsonResponse(resultado)

    except json_stdlib.JSONDecodeError:
        return JsonResponse({
            'error': 'No se pudo interpretar la respuesta del OCR. Intenta con una imagen más clara.'
        }, status=500)
    except http_requests.RequestException as e:
        return JsonResponse({
            'error': f'Error al comunicarse con el servicio OCR: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': f'Error inesperado al procesar la planilla: {str(e)}'
        }, status=500)