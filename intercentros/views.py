from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    TorneoIntercentros, EquipoIntercentros,
    Postulacion, Entrenamiento, Aviso, AsistenciaEntrenamiento
)

DISCIPLINAS = ['Fútbol', 'Fútbol Sala', 'Voleibol', 'Tenis de Mesa', 'Baloncesto']


def es_administrador(user):
    """Retorna True si el usuario tiene rol de administrador."""
    return getattr(user, 'rol', None) == 'administrador' or user.is_staff


def _get_nombres(user):
    """
    Intenta obtener el nombre completo del usuario probando los campos
    más comunes en CustomUser de proyectos SENA.
    Ajusta aquí si tu modelo usa otro nombre de campo.
    """
    for campo in ('nombres', 'nombre', 'first_name'):
        val = getattr(user, campo, None)
        if val:
            return str(val)
    return ''


def _get_apellidos(user):
    for campo in ('apellidos', 'apellido', 'last_name'):
        val = getattr(user, campo, None)
        if val:
            return str(val)
    return ''


def _get_ficha(user):
    for campo in ('ficha', 'numero_ficha', 'cod_ficha'):
        val = getattr(user, campo, None)
        if val:
            return str(val)
    return ''


def _get_programa(user):
    for campo in ('programa_formacion', 'programa', 'nombre_programa'):
        val = getattr(user, campo, None)
        if val:
            return str(val)
    return ''


def _get_documento(user):
    for campo in ('numero_documento', 'cedula', 'documento', 'username'):
        val = getattr(user, campo, None)
        if val:
            return str(val)
    return ''


@login_required
def intercentros_list(request):
    torneos        = TorneoIntercentros.objects.filter(estado='Activo').order_by('-fecha_torneo')
    entrenamientos = Entrenamiento.objects.all().order_by('-fecha', '-hora')
    avisos         = Aviso.objects.all().order_by('-creado_en')

    es_admin = es_administrador(request.user)

    # Postulaciones del aprendiz logueado
    mis_postulaciones = Postulacion.objects.filter(
        numero_documento=_get_documento(request.user)
    ).select_related('torneo').order_by('-fecha_postulacion')

    # Admin: todas las postulaciones agrupadas por torneo
    todas_postulaciones = []
    if es_admin:
        todas_postulaciones = (
            Postulacion.objects
            .select_related('torneo')
            .order_by('torneo__nombre_torneo', 'apellidos', 'nombres')
        )

    # IDs de entrenamientos ya confirmados (aprendiz)
    ids_confirmados = set()
    if not es_admin:
        ids_confirmados = set(
            AsistenciaEntrenamiento.objects.filter(
                numero_documento=_get_documento(request.user)
            ).values_list('entrenamiento_id', flat=True)
        )

    # Asistentes por entrenamiento (admin)
    asistencias_por_entrenamiento = {}
    if es_admin:
        for ent in entrenamientos:
            asistencias_por_entrenamiento[ent.pk] = list(
                AsistenciaEntrenamiento.objects.filter(entrenamiento=ent).order_by('nombres')
            )

    # Filtros GET
    filtro_disc_ent   = request.GET.get('disc_ent', '')
    filtro_torneo_ent = request.GET.get('torneo_ent', '')
    filtro_disc_av    = request.GET.get('disc_av', '')
    filtro_torneo_av  = request.GET.get('torneo_av', '')

    if filtro_disc_ent:
        entrenamientos = entrenamientos.filter(disciplina=filtro_disc_ent)
    if filtro_torneo_ent:
        entrenamientos = entrenamientos.filter(torneo_id=filtro_torneo_ent)
    if filtro_disc_av:
        avisos = avisos.filter(disciplina=filtro_disc_av)
    if filtro_torneo_av:
        avisos = avisos.filter(torneo_id=filtro_torneo_av)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # ── 1. POSTULARSE (solo aprendiz) ────────────────────────
        if accion == 'inscribir_aprendiz':
            if es_admin:
                messages.error(request, 'Los administradores no pueden postularse a convocatorias.')
                return redirect('intercentros')

            torneo_id  = request.POST.get('torneo_id')
            disciplina = request.POST.get('disciplina')

            if not torneo_id:
                messages.error(request, 'Debes seleccionar una convocatoria.')
                return redirect('intercentros')

            torneo = get_object_or_404(TorneoIntercentros, pk=torneo_id)

            ya_existe = Postulacion.objects.filter(
                torneo=torneo,
                numero_documento=_get_documento(request.user)
            ).exists()

            if ya_existe:
                messages.warning(request, f'Ya estás postulado a "{torneo.nombre_torneo}".')
            else:
                Postulacion.objects.create(
                    torneo             = torneo,
                    numero_documento   = _get_documento(request.user),
                    nombres            = _get_nombres(request.user),
                    apellidos          = _get_apellidos(request.user),
                    ficha              = _get_ficha(request.user),
                    programa_formacion = _get_programa(request.user),
                    disciplina         = disciplina or torneo.disciplina,
                )
                messages.success(request, f'¡Postulación a "{torneo.nombre_torneo}" enviada!')
            return redirect('intercentros')

        # ── 2. CREAR TORNEO (solo admin) ─────────────────────────
        elif accion == 'crear_torneo':
            if not es_admin:
                messages.error(request, 'No tienes permisos para crear convocatorias.')
                return redirect('intercentros')

            TorneoIntercentros.objects.create(
                nombre_torneo = request.POST.get('nombre'),
                fecha_torneo  = request.POST.get('fecha'),
                lugar         = request.POST.get('lugar'),
                disciplina    = request.POST.get('disciplina'),
            )
            messages.success(request, 'Nueva convocatoria Intercentros publicada.')
            return redirect('intercentros')

        # ── 3. CREAR ENTRENAMIENTO (solo admin) ──────────────────
        elif accion == 'crear_entrenamiento':
            if not es_admin:
                messages.error(request, 'No tienes permisos para programar entrenamientos.')
                return redirect('intercentros')

            torneo_id = request.POST.get('torneo_id') or None
            Entrenamiento.objects.create(
                torneo      = TorneoIntercentros.objects.filter(pk=torneo_id).first() if torneo_id else None,
                disciplina  = request.POST.get('disciplina'),
                fecha       = request.POST.get('fecha'),
                hora        = request.POST.get('hora'),
                lugar       = request.POST.get('lugar_ent', ''),
                observacion = request.POST.get('observacion', ''),
            )
            messages.success(request, 'Entrenamiento programado correctamente.')
            return redirect('intercentros')

        # ── 4. CREAR AVISO (solo admin) ──────────────────────────
        elif accion == 'crear_aviso':
            if not es_admin:
                messages.error(request, 'No tienes permisos para publicar avisos.')
                return redirect('intercentros')

            torneo_id = request.POST.get('torneo_id') or None
            Aviso.objects.create(
                titulo     = request.POST.get('titulo'),
                cuerpo     = request.POST.get('cuerpo'),
                tipo       = request.POST.get('tipo', 'info'),
                disciplina = request.POST.get('disciplina', ''),
                torneo     = TorneoIntercentros.objects.filter(pk=torneo_id).first() if torneo_id else None,
            )
            messages.success(request, 'Aviso publicado correctamente.')
            return redirect('intercentros')

        # ── 5. CONFIRMAR ASISTENCIA (solo aprendiz) ──────────────
        elif accion == 'confirmar_asistencia':
            if es_admin:
                messages.error(request, 'Los administradores no confirman asistencia.')
                return redirect('intercentros')

            entrenamiento_id = request.POST.get('entrenamiento_id')
            entrenamiento = get_object_or_404(Entrenamiento, pk=entrenamiento_id)

            ya_confirmo = AsistenciaEntrenamiento.objects.filter(
                entrenamiento=entrenamiento,
                numero_documento=_get_documento(request.user)
            ).exists()

            if ya_confirmo:
                messages.warning(request, 'Ya confirmaste tu asistencia a este entrenamiento.')
            else:
                AsistenciaEntrenamiento.objects.create(
                    entrenamiento    = entrenamiento,
                    numero_documento = _get_documento(request.user),
                    nombres          = _get_nombres(request.user),
                    apellidos        = _get_apellidos(request.user),
                    ficha            = _get_ficha(request.user),
                )
                messages.success(
                    request,
                    f'¡Asistencia confirmada para el {entrenamiento.fecha.strftime("%d/%m/%Y")}!'
                )
            return redirect('intercentros')

    return render(request, 'intercentros/intercentros.html', {
        'torneos'                       : torneos,
        'entrenamientos'                : entrenamientos,
        'avisos'                        : avisos,
        'mis_postulaciones'             : mis_postulaciones,
        'todas_postulaciones'           : todas_postulaciones,
        'disciplinas'                   : DISCIPLINAS,
        'ahora'                         : timezone.localtime(timezone.now()),
        'es_admin'                      : es_admin,
        'ids_confirmados'               : ids_confirmados,
        'asistencias_por_entrenamiento' : asistencias_por_entrenamiento,
        'filtro_disc_ent'               : filtro_disc_ent,
        'filtro_torneo_ent'             : filtro_torneo_ent,
        'filtro_disc_av'                : filtro_disc_av,
        'filtro_torneo_av'              : filtro_torneo_av,
    })


@login_required
def eliminar_torneo(request, id):
    if not es_administrador(request.user):
        messages.error(request, 'No tienes permisos para eliminar convocatorias.')
        return redirect('intercentros')

    torneo = get_object_or_404(TorneoIntercentros, codigo_torneo_centro=id)
    torneo.delete()
    messages.warning(request, 'Convocatoria eliminada correctamente.')
    return redirect('intercentros')


@login_required
def eliminar_aviso(request, id):
    if not es_administrador(request.user):
        messages.error(request, 'No tienes permisos para eliminar avisos.')
        return redirect('intercentros')

    aviso = get_object_or_404(Aviso, pk=id)
    aviso.delete()
    messages.warning(request, 'Aviso eliminado correctamente.')
    return redirect('intercentros')