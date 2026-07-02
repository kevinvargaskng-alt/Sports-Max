from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .models import Reserva, GimnasioConfig, FechaIngreso, Maquina
import json


def es_admin(user):
    return user.is_staff or user.is_superuser


@login_required
def gimnasio_list(request):
    mis_reservas = Reserva.objects.filter(
        usuario_solicitante=request.user
    ).order_by('-fecha_entrada', '-hora_entrada')

    ahora = timezone.localtime(timezone.now())
    horario_ok = 7 <= ahora.hour < 17
    dia_semana = ahora.weekday()
    es_fin_de_semana = dia_semana in [5, 6]

    festivos_2026 = [
        "01-01", "01-06", "03-23", "04-02", "04-03", "05-01",
        "05-18", "06-08", "06-15", "06-29", "07-20", "08-07",
        "08-17", "10-12", "11-02", "11-16", "12-08", "12-25"
    ]
    es_festivo = ahora.strftime("%m-%d") in festivos_2026

    config = GimnasioConfig.get_config()
    estado_manual = config.estado == 'abierta'

    esta_abierto = (
        horario_ok
        and not es_fin_de_semana
        and not es_festivo
        and estado_manual
    )

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear_reserva':
            if not esta_abierto:
                messages.error(
                    request, "Acceso denegado: El sistema está bloqueado.")
                return redirect('gimnasio')

            try:
                from datetime import timedelta as _td
                _hora_salida = (ahora + _td(hours=1)).time()
                Reserva.objects.create(
                    usuario_solicitante=request.user,
                    fecha_entrada=ahora.date(),
                    hora_entrada=ahora.time(),
                    tiempo_permanencia=60,
                    hora_salida=_hora_salida,
                    fecha_salida=ahora.date(),
                    estado='Activa'
                )
                messages.success(request, f"¡Entrada registrada! Bienvenido(a), {request.user.first_name}.")
            except Exception as e:
                messages.error(request, f"Error técnico al registrar asistencia: {e}")

            return redirect('gimnasio')

    # Pre-poblar máquinas por defecto si no existen
    if Maquina.objects.count() == 0:
        Maquina.objects.bulk_create([
            Maquina(nombre='Caminadora', categoria='cardio', descripcion='Ideal para calentar, caminar o correr controlando velocidad e inclinación.', musculos=['Piernas', 'Cardiovascular']),
            Maquina(nombre='Bicicleta Estática', categoria='cardio', descripcion='Bajo impacto para las articulaciones, mejora resistencia y capacidad aeróbica.', musculos=['Cuádriceps', 'Pantorrillas']),
            Maquina(nombre='Elíptica', categoria='cardio', descripcion='Combina tren superior e inferior en un movimiento fluido y de bajo impacto.', musculos=['Piernas', 'Brazos']),
            Maquina(nombre='Press de Banca', categoria='fuerza', descripcion='Ejercicio base para desarrollar fuerza y volumen en el pecho y tríceps.', musculos=['Pecho', 'Tríceps']),
            Maquina(nombre='Multiestación', categoria='fuerza', descripcion='Varios ejercicios guiados en un solo equipo: jalones, extensiones y poleas.', musculos=['Espalda', 'Brazos']),
            Maquina(nombre='Rack de Sentadillas', categoria='fuerza', descripcion='Estructura fija para realizar sentadillas y press militar con seguridad.', musculos=['Piernas', 'Glúteos']),
            Maquina(nombre='Remo', categoria='funcional', descripcion='Trabajo completo de tren superior e inferior con enfoque cardiovascular.', musculos=['Espalda', 'Piernas']),
            Maquina(nombre='Zona TRX / Colchonetas', categoria='funcional', descripcion='Espacio libre para entrenamiento en suspensión, core y estiramientos.', musculos=['Core', 'Cuerpo completo']),
        ])

    maquinas = Maquina.objects.all().order_by('categoria', 'nombre')
    # El aprendiz solo debe ver equipos que no estén fuera de servicio
    maquinas_aprendiz = maquinas.exclude(estado='inactivo')

    todas_reservas = Reserva.objects.all().order_by('-fecha_entrada', '-hora_entrada')
    fechas = FechaIngreso.objects.filter(config=config).order_by('fecha')
    dias_semana = [
        {'codigo': 'lun', 'label': 'LUN'},
        {'codigo': 'mar', 'label': 'MAR'},
        {'codigo': 'mie', 'label': 'MIÉ'},
        {'codigo': 'jue', 'label': 'JUE'},
        {'codigo': 'vie', 'label': 'VIE'},
        {'codigo': 'sab', 'label': 'SÁB'},
        {'codigo': 'dom', 'label': 'DOM'},
    ]
    from usuarios.models import Usuario
    total_aprendices = Usuario.objects.filter(rol='aprendiz').count()

    # Recupera la pestaña admin activa (seteada por las vistas de acción) y la limpia
    seccion_activa = request.session.pop('seccion_admin', '')
    request.session.pop('abrir_admin', None)

    context = {
        'reservas': mis_reservas,
        'esta_abierto': esta_abierto,
        'ahora': ahora,
        'es_fin_de_semana': es_fin_de_semana,
        'es_festivo': es_festivo,
        'config': config,
        'maquinas': maquinas if (request.user.is_staff or request.user.is_superuser) else maquinas_aprendiz,
        'fechas': fechas,
        'todas_reservas': todas_reservas,
        'dias_semana': dias_semana,
        'dias_activos': config.dias_habilitados,
        'total_reservas': todas_reservas.count(),
        'reservas_hoy': todas_reservas.filter(fecha_entrada=ahora.date()).count(),
        'total_aprendices': total_aprendices,
        'total_maquinas': maquinas.count(),
        'seccion_activa': seccion_activa,
    }
    return render(request, 'gimnasio/gimnasio.html', context)


# --- ELIMINAR REGISTRO ---
@login_required
@require_POST
def eliminar_reserva(request, id):
    reserva = get_object_or_404(Reserva, codigo_registro=id)
    reserva.delete()
    messages.warning(request, "El registro de asistencia ha sido eliminado.")
    return redirect('gimnasio')


# --- EDITAR REGISTRO ---
@login_required
def editar_reserva(request, id):
    reserva = get_object_or_404(Reserva, codigo_registro=id)
    if request.method == 'POST':
        reserva.save()
        messages.info(request, "Información actualizada.")
        return redirect('gimnasio')
    context = {'reserva': reserva}
    return render(request, 'gimnasio/editar.html', context)


# ── DISPONIBILIDAD ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_disponibilidad(request):
    config = GimnasioConfig.get_config()

    if request.method == 'POST':
        estado = request.POST.get('estado', config.estado)
        dias_json = request.POST.get('dias_json', '[]')
        try:
            dias = json.loads(dias_json)
        except (ValueError, TypeError):
            dias = []

        horario_apertura = request.POST.get('horario_apertura', '07:00')
        horario_cierre = request.POST.get('horario_cierre',   '17:00')
        capacidad = request.POST.get('capacidad_maxima', 40)

        if horario_apertura >= horario_cierre:
            messages.error(request, 'El horario de apertura debe ser anterior al horario de cierre.')
            return redirect('gimnasio')

        config.estado = estado
        config.dias_habilitados = dias
        config.horario_apertura = horario_apertura
        config.horario_cierre = horario_cierre
        config.capacidad_maxima = int(capacidad)
        config.actualizado_por = request.user
        config.save()

        messages.success(request, 'Configuración actualizada correctamente.')
        request.session['seccion_admin'] = 'disponibilidad'

    return redirect('gimnasio')


# ── HORARIOS ────────────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_horarios(request):
    request.session['seccion_admin'] = 'horarios'
    return redirect('gimnasio')


# ── FECHAS DE INGRESO ───────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_fechas_ingreso(request):
    config = GimnasioConfig.get_config()

    if request.method == 'POST':
        fecha_str = request.POST.get('fecha', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        habilitada = request.POST.get('habilitada') == 'on'

        if fecha_str:
            from datetime import datetime as _dt
            try:
                parsed_date = _dt.strptime(fecha_str, '%Y-%m-%d').date()
                if parsed_date < timezone.localtime(timezone.now()).date():
                    messages.error(request, 'No puedes agregar una fecha en el pasado.')
                    request.session['seccion_admin'] = 'fechas'
                    return redirect('gimnasio')
            except ValueError:
                pass

            FechaIngreso.objects.create(
                config=config,
                fecha=fecha_str,
                descripcion=descripcion,
                habilitada=habilitada,
            )
            messages.success(request, 'Fecha de ingreso agregada.')
        else:
            messages.error(request, 'Debes ingresar una fecha válida.')

        request.session['seccion_admin'] = 'fechas'

    return redirect('gimnasio')


# ── ELIMINAR FECHA ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_eliminar_fecha(request, pk):
    get_object_or_404(FechaIngreso, pk=pk).delete()
    messages.success(request, 'Fecha eliminada.')
    request.session['seccion_admin'] = 'fechas'
    return redirect('gimnasio')


# ── CONFIGURACIÓN ───────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_configuracion(request):
    request.session['seccion_admin'] = 'configuracion'
    return redirect('gimnasio')


# ── NUEVO REGISTRO ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_nuevo_registro(request):
    request.session['seccion_admin'] = 'registros'
    return redirect('gimnasio')


# ── VER TODAS LAS RESERVAS ──────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_reservas(request):
    request.session['seccion_admin'] = 'registros'
    return redirect('gimnasio')


# ── CANCELAR RESERVA ────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def cancelar_reserva_admin(request, id):
    reserva = get_object_or_404(Reserva, codigo_registro=id)
    reserva.estado = 'Cancelada'
    reserva.save()
    messages.warning(request, 'La reservación fue cancelada correctamente.')
    request.session['seccion_admin'] = 'registros'
    return redirect('gimnasio')


# ── CERRAR / ABRIR GIMNASIO ─────────────────────────────────
@login_required
@user_passes_test(es_admin)
def cerrar_gimnasio(request):
    config = GimnasioConfig.get_config()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'cerrar':
            config.estado = 'cerrada'
            messages.error(request, 'El gimnasio fue cerrado.')
        elif accion == 'abrir':
            config.estado = 'abierta'
            messages.success(request, 'El gimnasio fue abierto.')

        config.actualizado_por = request.user
        config.save()

    request.session['seccion_admin'] = 'disponibilidad'
    return redirect('gimnasio')


# ── LISTA ANAMNESIS (FICHAS DE SALUD) ───────────────────────
@login_required
@user_passes_test(es_admin)
def admin_lista_anamnesis(request):
    # Reemplaza Anamnesis con tu modelo real cuando lo tengas
    context = {'seccion_activa': 'anamnesis'}
    return render(request, 'gimnasio/admin_lista_anamnesis.html', context)


# ═══════════════════════════════════════════════════════════
#  MÁQUINAS Y EQUIPOS — CRUD COMPLETO
# ═══════════════════════════════════════════════════════════

@login_required
@user_passes_test(es_admin)
@require_POST
def crear_maquina(request):
    nombre = request.POST.get('nombre', '').strip()
    categoria = request.POST.get('categoria', 'fuerza')
    descripcion = request.POST.get('descripcion', '').strip()
    musculos_raw = request.POST.get('musculos', '')
    musculos = [m.strip() for m in musculos_raw.split(',') if m.strip()]
    imagen = request.FILES.get('imagen')

    if not nombre:
        messages.error(request, 'El nombre de la máquina es obligatorio.')
        request.session['seccion_admin'] = 'maquinas'
        return redirect('gimnasio')

    Maquina.objects.create(
        nombre=nombre,
        categoria=categoria,
        descripcion=descripcion,
        musculos=musculos,
        imagen=imagen,
    )
    messages.success(request, f'Máquina "{nombre}" agregada correctamente.')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')


@login_required
@user_passes_test(es_admin)
@require_POST
def editar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)

    nombre = request.POST.get('nombre', '').strip()
    if not nombre:
        messages.error(request, 'El nombre de la máquina es obligatorio.')
        request.session['seccion_admin'] = 'maquinas'
        return redirect('gimnasio')

    maquina.nombre = nombre
    maquina.categoria = request.POST.get('categoria', maquina.categoria)
    maquina.descripcion = request.POST.get('descripcion', '').strip()
    musculos_raw = request.POST.get('musculos', '')
    maquina.musculos = [m.strip() for m in musculos_raw.split(',') if m.strip()]
    maquina.estado = request.POST.get('estado', maquina.estado)

    if request.FILES.get('imagen'):
        maquina.imagen = request.FILES.get('imagen')

    maquina.save()
    messages.success(request, f'Máquina "{maquina.nombre}" actualizada correctamente.')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')


@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    nombre = maquina.nombre
    maquina.delete()
    messages.warning(request, f'Máquina "{nombre}" eliminada.')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')


@login_required
@user_passes_test(es_admin)
@require_POST
def toggle_estado_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    orden = ['disponible', 'mantenimiento', 'inactivo']
    try:
        idx = orden.index(maquina.estado)
    except ValueError:
        idx = 0
    maquina.estado = orden[(idx + 1) % len(orden)]
    maquina.save()
    messages.info(request, f'"{maquina.nombre}" ahora está en estado: {maquina.get_estado_display()}.')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')