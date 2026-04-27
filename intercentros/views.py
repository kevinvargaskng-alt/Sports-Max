from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    TorneoIntercentros, EquipoIntercentros,
    Postulacion, Entrenamiento, Aviso
)

DISCIPLINAS = ['Fútbol', 'Fútbol Sala', 'Voleibol', 'Tenis de Mesa', 'Baloncesto']


@login_required
def intercentros_list(request):
    torneos        = TorneoIntercentros.objects.filter(estado='Activo').order_by('-fecha_torneo')
    entrenamientos = Entrenamiento.objects.all().order_by('-fecha', '-hora')
    avisos         = Aviso.objects.all()
    mis_postulaciones = Postulacion.objects.filter(
        numero_documento=str(request.user.numero_documento)
    ).select_related('torneo').order_by('-fecha_postulacion')

    # Filtros de vista (GET params)
    filtro_disc_ent  = request.GET.get('disc_ent', '')
    filtro_torneo_ent = request.GET.get('torneo_ent', '')
    filtro_disc_av   = request.GET.get('disc_av', '')
    filtro_torneo_av = request.GET.get('torneo_av', '')

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

        # ── 1. POSTULARSE ────────────────────────────────────────
        if accion == 'inscribir_aprendiz':
            torneo_id  = request.POST.get('torneo_id')
            disciplina = request.POST.get('disciplina')

            if not torneo_id:
                messages.error(request, 'Debes seleccionar una convocatoria.')
                return redirect('intercentros')

            torneo = get_object_or_404(TorneoIntercentros, pk=torneo_id)

            # Verificar si ya se postuló
            ya_existe = Postulacion.objects.filter(
                torneo=torneo,
                numero_documento=str(request.user.numero_documento)
            ).exists()

            if ya_existe:
                messages.warning(request, f'Ya estás postulado a "{torneo.nombre_torneo}".')
            else:
                Postulacion.objects.create(
                    torneo             = torneo,
                    numero_documento   = str(request.user.numero_documento),
                    nombres            = request.user.first_name,
                    apellidos          = request.user.last_name,
                    ficha              = getattr(request.user, 'ficha', ''),
                    programa_formacion = getattr(request.user, 'programa_formacion', ''),
                    disciplina         = disciplina or torneo.disciplina,
                )
                messages.success(request, f'¡Postulación a "{torneo.nombre_torneo}" enviada!')
            return redirect('intercentros')

        # ── 2. CREAR TORNEO ──────────────────────────────────────
        elif accion == 'crear_torneo':
            TorneoIntercentros.objects.create(
                nombre_torneo = request.POST.get('nombre'),
                fecha_torneo  = request.POST.get('fecha'),
                lugar         = request.POST.get('lugar'),
                disciplina    = request.POST.get('disciplina'),
            )
            messages.success(request, 'Nueva convocatoria Intercentros publicada.')
            return redirect('intercentros')

        # ── 3. CREAR ENTRENAMIENTO ───────────────────────────────
        elif accion == 'crear_entrenamiento':
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

        # ── 4. CREAR AVISO ───────────────────────────────────────
        elif accion == 'crear_aviso':
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

    return render(request, 'intercentros/intercentros.html', {
        'torneos'          : torneos,
        'entrenamientos'   : entrenamientos,
        'avisos'           : avisos,
        'mis_postulaciones': mis_postulaciones,
        'disciplinas'      : DISCIPLINAS,
        'ahora'          : timezone.localtime(timezone.now()),
        # para repoblar filtros activos
        'filtro_disc_ent'  : filtro_disc_ent,
        'filtro_torneo_ent': filtro_torneo_ent,
        'filtro_disc_av'   : filtro_disc_av,
        'filtro_torneo_av' : filtro_torneo_av,
    })


@login_required
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoIntercentros, codigo_torneo_centro=id)
    torneo.delete()
    messages.warning(request, 'Convocatoria eliminada correctamente.')
    return redirect('intercentros')