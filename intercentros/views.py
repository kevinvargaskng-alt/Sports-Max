from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    TorneoIntercentros, EquipoIntercentros,
    Postulacion, Entrenamiento, Aviso, AsistenciaEntrenamiento,
    SeleccionadoSena, MiembroSeleccionado,
)

DISCIPLINAS = ['Fútbol', 'Fútbol Sala', 'Voleibol', 'Tenis de Mesa', 'Baloncesto']


# ── Helpers ───────────────────────────────────────────────────────────────────

def es_administrador(user):
    return getattr(user, 'rol', None) == 'administrador' or user.is_staff


def _get_nombres(user):
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


# ── Vista principal Intercentros ──────────────────────────────────────────────

@login_required
def intercentros_list(request):
    torneos        = TorneoIntercentros.objects.filter(estado='Activo').order_by('-fecha_torneo')
    entrenamientos = Entrenamiento.objects.all().order_by('-fecha', '-hora')
    avisos         = Aviso.objects.all().order_by('-creado_en')

    es_admin = es_administrador(request.user)

    mis_postulaciones = Postulacion.objects.filter(
        numero_documento=_get_documento(request.user)
    ).select_related('torneo').order_by('-fecha_postulacion')

    # ── NUEVO: lista plana de TODOS los postulados (solo admin) ──
    todas_postulaciones = []
    if es_admin:
        todas_postulaciones = (
            Postulacion.objects
            .select_related('torneo')
            .order_by('torneo__nombre_torneo', 'apellidos', 'nombres')
        )

    ids_confirmados = set()
    if not es_admin:
        ids_confirmados = set(
            AsistenciaEntrenamiento.objects.filter(
                numero_documento=_get_documento(request.user)
            ).values_list('entrenamiento_id', flat=True)
        )

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


# ── Eliminar torneo / aviso ───────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════
#  VISTAS DE SELECCIONADOS SENA
# ══════════════════════════════════════════════════════

@login_required
def seleccionados_list(request):
    es_admin   = es_administrador(request.user)
    documento  = _get_documento(request.user)
    torneos    = TorneoIntercentros.objects.filter(estado='Activo').order_by('-fecha_torneo')
    selecciones = SeleccionadoSena.objects.filter(estado='Activo').select_related('torneo').order_by('-creado_en')

    selecciones_con_miembros = []
    for sel in selecciones:
        miembros = sel.miembros.all()
        selecciones_con_miembros.append({
            'seleccion': sel,
            'miembros' : miembros,
            'cupos'    : sel.cupos_disponibles,
            'llena'    : sel.esta_llena,
        })

    mis_selecciones = []
    if not es_admin:
        mis_selecciones = MiembroSeleccionado.objects.filter(
            numero_documento=documento
        ).select_related('seleccion', 'seleccion__torneo').order_by('-seleccionado_en')

    filtro_torneo = request.GET.get('torneo', '')
    if filtro_torneo:
        selecciones_con_miembros = [
            s for s in selecciones_con_miembros
            if s['seleccion'].torneo and str(s['seleccion'].torneo.pk) == filtro_torneo
        ]

    postulados_por_torneo = {}
    if es_admin:
        for t in torneos:
            postulados_por_torneo[t.pk] = list(
                Postulacion.objects.filter(torneo=t).order_by('apellidos', 'nombres')
            )

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear_seleccion':
            if not es_admin:
                messages.error(request, 'Sin permisos.')
                return redirect('seleccionados')

            torneo_id  = request.POST.get('torneo_id') or None
            torneo_obj = TorneoIntercentros.objects.filter(pk=torneo_id).first() if torneo_id else None

            SeleccionadoSena.objects.create(
                torneo           = torneo_obj,
                disciplina       = request.POST.get('disciplina', ''),
                fecha_seleccion  = request.POST.get('fecha_seleccion'),
                capacidad        = int(request.POST.get('capacidad', 10)),
                estado_seleccion = request.POST.get('estado_seleccion', 'en_proceso'),
                fecha_torneo     = request.POST.get('fecha_torneo') or None,
                sede             = request.POST.get('sede', ''),
                hora_torneo      = request.POST.get('hora_torneo') or None,
            )
            messages.success(request, 'Lista de seleccionados creada correctamente.')
            return redirect('seleccionados')

        elif accion == 'agregar_miembro':
            if not es_admin:
                messages.error(request, 'Sin permisos.')
                return redirect('seleccionados')

            seleccion_id   = request.POST.get('seleccion_id')
            postulacion_id = request.POST.get('postulacion_id')

            seleccion   = get_object_or_404(SeleccionadoSena, pk=seleccion_id)
            postulacion = get_object_or_404(Postulacion, pk=postulacion_id)

            if seleccion.esta_llena:
                messages.warning(request, f'La selección ya alcanzó su capacidad máxima ({seleccion.capacidad}).')
                return redirect('seleccionados')

            ya_en_seleccion = MiembroSeleccionado.objects.filter(
                seleccion=seleccion,
                numero_documento=postulacion.numero_documento
            ).exists()

            if ya_en_seleccion:
                messages.warning(request, f'{postulacion.nombres} {postulacion.apellidos} ya está en esta selección.')
            else:
                MiembroSeleccionado.objects.create(
                    seleccion          = seleccion,
                    postulacion        = postulacion,
                    numero_documento   = postulacion.numero_documento,
                    nombres            = postulacion.nombres,
                    apellidos          = postulacion.apellidos,
                    ficha              = postulacion.ficha,
                    programa_formacion = postulacion.programa_formacion,
                    disciplina         = postulacion.disciplina,
                )
                messages.success(
                    request,
                    f'✓ {postulacion.nombres} {postulacion.apellidos} agregado a la selección.'
                )
            return redirect('seleccionados')

        elif accion == 'cambiar_estado_seleccion':
            if not es_admin:
                messages.error(request, 'Sin permisos.')
                return redirect('seleccionados')

            seleccion_id = request.POST.get('seleccion_id')
            nuevo_estado = request.POST.get('estado_seleccion')
            seleccion    = get_object_or_404(SeleccionadoSena, pk=seleccion_id)
            seleccion.estado_seleccion = nuevo_estado
            seleccion.save()
            messages.success(request, f'Estado actualizado a: {seleccion.get_estado_seleccion_display()}')
            return redirect('seleccionados')

        elif accion == 'quitar_miembro':
            if not es_admin:
                messages.error(request, 'Sin permisos.')
                return redirect('seleccionados')

            miembro_id = request.POST.get('miembro_id')
            miembro    = get_object_or_404(MiembroSeleccionado, pk=miembro_id)
            nombre     = f"{miembro.nombres} {miembro.apellidos}"
            miembro.delete()
            messages.warning(request, f'{nombre} fue removido de la selección.')
            return redirect('seleccionados')

        elif accion == 'eliminar_seleccion':
            if not es_admin:
                messages.error(request, 'Sin permisos.')
                return redirect('seleccionados')

            seleccion_id = request.POST.get('seleccion_id')
            seleccion    = get_object_or_404(SeleccionadoSena, pk=seleccion_id)
            seleccion.delete()
            messages.warning(request, 'Lista de seleccionados eliminada.')
            return redirect('seleccionados')

    return render(request, 'intercentros/seleccionados.html', {
        'selecciones_con_miembros' : selecciones_con_miembros,
        'mis_selecciones'          : mis_selecciones,
        'torneos'                  : torneos,
        'disciplinas'              : DISCIPLINAS,
        'es_admin'                 : es_admin,
        'postulados_por_torneo'    : postulados_por_torneo,
        'filtro_torneo'            : filtro_torneo,
        'ahora'                    : timezone.localtime(timezone.now()),
    })


@login_required
def detalle_seleccion(request, pk):
    es_admin  = es_administrador(request.user)
    seleccion = get_object_or_404(SeleccionadoSena, pk=pk)
    miembros  = seleccion.miembros.all()
    torneos   = TorneoIntercentros.objects.filter(estado='Activo')

    postulados_disponibles = []
    if seleccion.torneo and es_admin:
        ids_ya_en_seleccion = miembros.values_list('numero_documento', flat=True)
        postulados_disponibles = Postulacion.objects.filter(
            torneo=seleccion.torneo
        ).exclude(numero_documento__in=ids_ya_en_seleccion).order_by('apellidos')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'agregar_miembro' and es_admin:
            postulacion_id = request.POST.get('postulacion_id')
            postulacion    = get_object_or_404(Postulacion, pk=postulacion_id)

            if seleccion.esta_llena:
                messages.warning(request, 'La selección ya alcanzó su capacidad máxima.')
            else:
                ya_existe = MiembroSeleccionado.objects.filter(
                    seleccion=seleccion,
                    numero_documento=postulacion.numero_documento
                ).exists()
                if ya_existe:
                    messages.warning(request, 'Este aprendiz ya está en la selección.')
                else:
                    MiembroSeleccionado.objects.create(
                        seleccion          = seleccion,
                        postulacion        = postulacion,
                        numero_documento   = postulacion.numero_documento,
                        nombres            = postulacion.nombres,
                        apellidos          = postulacion.apellidos,
                        ficha              = postulacion.ficha,
                        programa_formacion = postulacion.programa_formacion,
                        disciplina         = postulacion.disciplina,
                    )
                    messages.success(
                        request,
                        f'✓ {postulacion.nombres} {postulacion.apellidos} agregado.'
                    )
            return redirect('detalle_seleccion', pk=pk)

        elif accion == 'quitar_miembro' and es_admin:
            miembro_id = request.POST.get('miembro_id')
            miembro    = get_object_or_404(MiembroSeleccionado, pk=miembro_id, seleccion=seleccion)
            nombre     = f"{miembro.nombres} {miembro.apellidos}"
            miembro.delete()
            messages.warning(request, f'{nombre} fue removido.')
            return redirect('detalle_seleccion', pk=pk)

        elif accion == 'cambiar_estado' and es_admin:
            seleccion.estado_seleccion = request.POST.get('estado_seleccion', seleccion.estado_seleccion)
            seleccion.save()
            messages.success(request, 'Estado actualizado.')
            return redirect('detalle_seleccion', pk=pk)

    return render(request, 'intercentros/detalle_seleccion.html', {
        'seleccion'              : seleccion,
        'miembros'               : miembros,
        'postulados_disponibles' : postulados_disponibles,
        'es_admin'               : es_admin,
    })