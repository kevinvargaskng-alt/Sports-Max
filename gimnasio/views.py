from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from core.security.file_upload import validate_uploaded_file
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
                from django.db import transaction
                from datetime import timedelta as _td

                with transaction.atomic():
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
    # Pre-poblar máquinas por defecto si no existen
    if Maquina.objects.count() == 0:
        Maquina.objects.bulk_create([
            Maquina(nombre='Caminadora Pro X', categoria='cardio', descripcion='Ideal para calentar, caminar o correr controlando velocidad e inclinación.', musculos=['Piernas', 'Cardiovascular']),
            Maquina(nombre='Bicicleta Estática', categoria='cardio', descripcion='Bajo impacto para las articulaciones, mejora resistencia y capacidad aeróbica.', musculos=['Cuádriceps', 'Pantorrillas']),
            Maquina(nombre='Elíptica Cross Trainer', categoria='cardio', descripcion='Combina tren superior e inferior en un movimiento fluido y de bajo impacto.', musculos=['Piernas', 'Brazos']),
            Maquina(nombre='Press de Banca Olímpico', categoria='fuerza', descripcion='Ejercicio base para desarrollar fuerza y volumen en el pecho y tríceps.', musculos=['Pecho', 'Tríceps']),
            Maquina(nombre='Multiestación Multifuerza', categoria='fuerza', descripcion='Varios ejercicios guiados en un solo equipo: jalones, extensiones y poleas.', musculos=['Espalda', 'Brazos']),
            Maquina(nombre='Rack de Sentadillas', categoria='fuerza', descripcion='Estructura fija para realizar sentadillas y press militar con seguridad.', musculos=['Piernas', 'Glúteos']),
            Maquina(nombre='Remo de Resistencia', categoria='funcional', descripcion='Trabajo completo de tren superior e inferior con enfoque cardiovascular.', musculos=['Espalda', 'Piernas']),
            Maquina(nombre='Zona TRX / Colchonetas', categoria='funcional', descripcion='Espacio libre para entrenamiento en suspensión, core y estiramientos.', musculos=['Core', 'Cuerpo completo']),
        ])

    from .models import Machine
    if Machine.objects.count() == 0:
        Machine.objects.bulk_create([
            Machine(nombre='Caminadora Pro X', tipo='Cardio', estado='Disponible', descripcion='Ideal para calentar, caminar o correr controlando velocidad e inclinación.'),
            Machine(nombre='Bicicleta Ergométrica', tipo='Cardio', estado='Disponible', descripcion='Bajo impacto para las articulaciones, mejora resistencia y capacidad aeróbica.'),
            Machine(nombre='Elíptica Cross Trainer', tipo='Cardio', estado='En Mantenimiento', descripcion='Combina tren superior e inferior en un movimiento fluido y de bajo impacto.'),
            Machine(nombre='Press de Banca Olímpico', tipo='Fuerza', estado='Disponible', descripcion='Ejercicio base para desarrollar fuerza y volumen en el pecho y tríceps.'),
            Machine(nombre='Multiestación Multifuerza', tipo='Fuerza', estado='Disponible', descripcion='Varios ejercicios guiados en un solo equipo: jalones, extensiones y poleas.'),
            Machine(nombre='Rack de Sentadillas', tipo='Fuerza', estado='Disponible', descripcion='Estructura fija para realizar sentadillas y press militar con seguridad.'),
            Machine(nombre='Remo de Resistencia', tipo='Funcional', estado='Disponible', descripcion='Trabajo completo de tren superior e inferior con enfoque cardiovascular.'),
            Machine(nombre='Estación TRX / Suspension', tipo='Flexibilidad', estado='Disponible', descripcion='Espacio libre para entrenamiento en suspensión, core y estiramientos.'),
        ])

    maquinas = Maquina.objects.all().order_by('categoria', 'nombre')
    if maquinas.count() == 0:
        maquinas = Machine.objects.all().order_by('tipo', 'nombre')

    # El aprendiz solo debe ver equipos que no estén fuera de servicio
    maquinas_aprendiz = maquinas.exclude(estado='inactivo') if hasattr(maquinas, 'exclude') else maquinas

    todas_reservas_qs = Reserva.objects.select_related('usuario_solicitante').order_by('-fecha_entrada', '-hora_entrada')
    todas_reservas_10 = list(todas_reservas_qs[:10])
    mis_reservas_10 = list(mis_reservas[:10])

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

    try:
        from habitos_saludables.models import SeguimientoSalud
        seguimientos_salud = SeguimientoSalud.objects.all().order_by('-fecha_evaluacion')
    except Exception:
        seguimientos_salud = []

    # Recupera la pestaña admin activa (seteada por las vistas de acción) y la limpia
    seccion_activa = request.session.pop('seccion_admin', '')
    request.session.pop('abrir_admin', None)

    context = {
        'reservas': mis_reservas_10,
        'esta_abierto': esta_abierto,
        'ahora': ahora,
        'es_fin_de_semana': es_fin_de_semana,
        'es_festivo': es_festivo,
        'config': config,
        'maquinas': maquinas if (request.user.is_staff or request.user.is_superuser) else maquinas_aprendiz,
        'fechas': fechas,
        'todas_reservas': todas_reservas_10,
        'dias_semana': dias_semana,
        'dias_activos': config.dias_habilitados,
        'total_reservas': todas_reservas_qs.count(),
        'reservas_hoy': todas_reservas_qs.filter(fecha_entrada=ahora.date()).count(),
        'total_aprendices': total_aprendices,
        'total_maquinas': len(maquinas),
        'seguimientos_salud': seguimientos_salud,
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
    """Muestra la lista de fichas de salud / anamnesis de todos los aprendices para administradores."""
    try:
        from habitos_saludables.models import SeguimientoSalud
        seguimientos = SeguimientoSalud.objects.all().order_by('-fecha_evaluacion')
    except Exception:
        seguimientos = []

    context = {
        'seccion_activa': 'anamnesis',
        'seguimientos': seguimientos,
        'total_fichas': len(seguimientos),
    }
    return render(request, 'gimnasio/admin_lista_anamnesis.html', context)


# ═══════════════════════════════════════════════════════════
#  MÁQUINAS Y EQUIPOS — CRUD COMPLETO
# ═══════════════════════════════════════════════════════════

@login_required
@user_passes_test(es_admin)
@require_POST
def crear_maquina(request):
    nombre = request.POST.get('nombre', '').strip()
    categoria = request.POST.get('categoria', 'Cardio')
    estado = request.POST.get('estado', 'Disponible')
    descripcion = request.POST.get('descripcion', '').strip()
    imagen = request.FILES.get('imagen')
    if imagen:
        try:
            imagen = validate_uploaded_file(imagen, allowed_types='image')
        except ValidationError as e:
            messages.error(request, f"Error en la imagen: {e.message}")
            if next_param == 'machine_list':
                return redirect('machine_list')
            request.session['seccion_admin'] = 'maquinas'
            return redirect('gimnasio')
    next_param = request.POST.get('next')

    if not nombre:
        messages.error(request, 'El nombre de la máquina es obligatorio.')
        if next_param == 'machine_list':
            return redirect('machine_list')
        request.session['seccion_admin'] = 'maquinas'
        return redirect('gimnasio')

    # Crear en el modelo Machine
    Machine.objects.create(
        nombre=nombre,
        tipo=categoria,
        estado=estado,
        descripcion=descripcion,
        imagen=imagen,
    )
    # Mantener sincronizado en Maquina
    try:
        musculos_raw = request.POST.get('musculos', '')
        musculos = [m.strip() for m in musculos_raw.split(',') if m.strip()]
        Maquina.objects.create(
            nombre=nombre,
            categoria=categoria.lower(),
            descripcion=descripcion,
            musculos=musculos,
            imagen=imagen,
        )
    except Exception:
        pass

    messages.success(request, f'Máquina "{nombre}" agregada correctamente.')
    if next_param == 'machine_list':
        return redirect('machine_list')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')


@login_required
@user_passes_test(es_admin)
@require_POST
def editar_maquina(request, pk):
    next_param = request.POST.get('next')
    machine = Machine.objects.filter(pk=pk).first()
    maquina = Maquina.objects.filter(pk=pk).first()

    nombre = request.POST.get('nombre', '').strip()
    if not nombre:
        messages.error(request, 'El nombre de la máquina es obligatorio.')
        if next_param == 'machine_list':
            return redirect('machine_list')
        request.session['seccion_admin'] = 'maquinas'
        return redirect('gimnasio')

    imagen_val = None
    if request.FILES.get('imagen'):
        try:
            imagen_val = validate_uploaded_file(request.FILES.get('imagen'), allowed_types='image')
        except ValidationError as e:
            messages.error(request, f"Error en la imagen: {e.message}")
            if next_param == 'machine_list':
                return redirect('machine_list')
            request.session['seccion_admin'] = 'maquinas'
            return redirect('gimnasio')

    if machine:
        machine.nombre = nombre
        machine.tipo = request.POST.get('categoria', machine.tipo)
        machine.estado = request.POST.get('estado', machine.estado)
        machine.descripcion = request.POST.get('descripcion', '').strip()
        if imagen_val:
            machine.imagen = imagen_val
        machine.save()

    if maquina:
        maquina.nombre = nombre
        maquina.categoria = request.POST.get('categoria', maquina.categoria).lower()
        maquina.estado = request.POST.get('estado', maquina.estado)
        maquina.descripcion = request.POST.get('descripcion', '').strip()
        if imagen_val:
            maquina.imagen = imagen_val
        maquina.save()

    messages.success(request, 'Máquina actualizada correctamente.')
    if next_param == 'machine_list':
        return redirect('machine_list')
    request.session['seccion_admin'] = 'maquinas'
    return redirect('gimnasio')


@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_maquina(request, pk):
    next_param = request.POST.get('next')
    machine = Machine.objects.filter(pk=pk).first()
    maquina = Maquina.objects.filter(pk=pk).first()

    nombre = machine.nombre if machine else (maquina.nombre if maquina else 'Máquina')

    if machine:
        machine.delete()
    if maquina:
        maquina.delete()

    messages.warning(request, f'Máquina "{nombre}" eliminada.')
    if next_param == 'machine_list':
        return redirect('machine_list')
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


from django.views.generic import ListView
from django.utils.decorators import method_decorator
from .models import Machine


@method_decorator(login_required, name='dispatch')
class MachineListView(ListView):
    """
    Vista basada en clases (ListView) para listar el inventario de máquinas del gimnasio.
    """
    model = Machine
    template_name = 'gimnasio/machine_list.html'
    context_object_name = 'machines'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        tipo_filter = self.request.GET.get('tipo', '').strip()
        search_query = self.request.GET.get('q', '').strip()

        if tipo_filter:
            queryset = queryset.filter(tipo__iexact=tipo_filter)
        if search_query:
            queryset = queryset.filter(nombre__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pre-poblar máquinas por defecto si la base de datos está vacía
        if Machine.objects.count() == 0:
            Machine.objects.bulk_create([
                Machine(nombre='Caminadora Pro X', tipo='Cardio', estado='Disponible', descripcion='Ideal para entrenamiento aeróbico de alta resistencia.'),
                Machine(nombre='Bicicleta Ergométrica', tipo='Cardio', estado='Disponible', descripcion='Monitoreo de frecuencia cardíaca y resistencia ajustable.'),
                Machine(nombre='Elíptica Cross Trainer', tipo='Cardio', estado='En Mantenimiento', descripcion='Bajo impacto articulatorio con movimiento fluido.'),
                Machine(nombre='Press de Banca Olímpico', tipo='Fuerza', estado='Disponible', descripcion='Desarrollo de fuerza pectoral con barra olímpica.'),
                Machine(nombre='Multiestación Multifuerza', tipo='Fuerza', estado='Disponible', descripcion='Estación completa con poleas altas y bajas.'),
                Machine(nombre='Rack de Sentadillas', tipo='Fuerza', estado='Disponible', descripcion='Estructura reforzada con soportes de seguridad.'),
                Machine(nombre='Remo de Resistencia', tipo='Funcional', estado='Disponible', descripcion='Entrenamiento cardiovascular y muscular de cuerpo completo.'),
                Machine(nombre='Estación TRX / Suspension', tipo='Flexibilidad', estado='Disponible', descripcion='Entrenamiento en suspensión con peso corporal.'),
            ])
            context['object_list'] = Machine.objects.all()
            context['machines'] = context['object_list']

        context['total_count'] = Machine.objects.count()
        context['disponibles_count'] = Machine.objects.filter(estado='Disponible').count()
        context['mantenimiento_count'] = Machine.objects.filter(estado='En Mantenimiento').count()
        context['selected_tipo'] = self.request.GET.get('tipo', '')
        context['search_q'] = self.request.GET.get('q', '')
        return context