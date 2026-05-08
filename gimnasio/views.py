from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Reserva
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import GimnasioConfig, FechaIngreso
from django.db.models import Q 



@login_required
def gimnasio_list(request):
    """
    Controla el acceso al gimnasio y muestra el historial personal.
    """
    
    # 1. DEFINIR IDENTIDAD PARA FILTRADO
    # Usamos el nombre completo tal como se guarda en el CharField del modelo
    
    nombre_usuario_logueado = f"{request.user.first_name} {request.user.last_name}"
    
    # Traemos solo las reservas del usuario actual para su historial personal
    mis_reservas = Reserva.objects.filter(
        usuario_solicitante=nombre_usuario_logueado
    ).order_by('-fecha_entrada', '-hora_entrada')
    
    # 2. LÓGICA DE CONTROL DE ACCESO (HORARIO, FINES DE SEMANA Y FESTIVOS)
    ahora = timezone.localtime(timezone.now())
    
    # Horario: 7:00 AM a 5:00 PM
    horario_ok = 7 <= ahora.hour < 17
    
    # Fines de Semana: Sábado (5) y Domingo (6)
    dia_semana = ahora.weekday() 
    es_fin_de_semana = dia_semana in [5, 6]
    
    # Calendario de Festivos Colombia 2026 (Mes-Día)
    festivos_2026 = [
        "01-01", "01-06", "03-23", "04-02", "04-03", "05-01", 
        "05-18", "06-08", "06-15", "06-29", "07-20", "08-07",
        "08-17", "10-12", "11-02", "11-16", "12-08", "12-25"
    ]
    es_festivo = ahora.strftime("%m-%d") in festivos_2026
    
    config = GimnasioConfig.get_config()

    # Verifica estado manual del admin
    estado_manual = config.estado == 'abierta'

# El sistema solo permite ingreso si cumple todo
    esta_abierto = (
    horario_ok
    and not es_fin_de_semana
    and not es_festivo
    and estado_manual
)
    # 3. PROCESAR REGISTRO DE ENTRADA (POST)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear_reserva':
            # Validación de seguridad extra en el servidor
            if not esta_abierto:
                messages.error(request, "Acceso denegado: El sistema de registro está bloqueado en este momento.")
                return redirect('gimnasio')

            try:
                # Creamos el registro llenando los campos que tu modelo pide como obligatorios
                Reserva.objects.create(
                    usuario_solicitante=nombre_usuario_logueado,
                    fecha_entrada=ahora.date(),
                    hora_entrada=ahora.time(),
                    # Campos de compatibilidad con tu modelo actual
                    hora_prestamo=ahora.time(),
                    fecha_permanencia=ahora.date(),
                    hora_salida=ahora.time(),
                    fecha_salida=ahora.date(),
                    estado='Activa'
                )
                messages.success(request, f"¡Entrada registrada! Bienvenido(a), {request.user.first_name}.")
            except Exception as e:
                messages.error(request, f"Error técnico al registrar asistencia: {e}")
            
            request.session['abrir_admin'] = True
            request.session['seccion_admin'] = 'reservas'
            return redirect('gimnasio')

    # 4. RENDERIZADO
    abrir_admin = request.session.pop('abrir_admin', False)
    seccion_admin = request.session.pop('seccion_admin', '')
    return render(request, 'gimnasio/gimnasio.html', {
    'abrir_admin': abrir_admin,
    'seccion_activa': seccion_admin,
    'reservas': mis_reservas,
    'esta_abierto': esta_abierto,
    'ahora': ahora,
    'es_fin_de_semana': es_fin_de_semana,
    'es_festivo': es_festivo,
    'config': config,
    'admin_reservas': Reserva.objects.all().order_by(
        '-fecha_entrada',
        '-hora_entrada'
    )
})

# --- ELIMINAR REGISTRO ---
@login_required
def eliminar_reserva(request, id):
    # Solo permitimos borrar si el registro existe
    reserva = get_object_or_404(Reserva, codigo_registro=id)
    reserva.delete()
    messages.warning(request, "El registro de asistencia ha sido eliminado.")
    return redirect('gimnasio')

# --- EDITAR REGISTRO ---
@login_required
def editar_reserva(request, id):
    reserva = get_object_or_404(Reserva, codigo_registro=id)
    if request.method == 'POST':
        # Aquí puedes añadir lógica para editar campos específicos si lo deseas
        reserva.save()
        messages.info(request, "Información actualizada.")
        return redirect('gimnasio')
    return render(request, 'gimnasio/editar.html', {'reserva': reserva})



import json
from django.contrib.auth.decorators import user_passes_test
from .models import GimnasioConfig, FechaIngreso


def es_admin(user):
    return user.is_staff or user.is_superuser


# ── DISPONIBILIDAD ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_disponibilidad(request):
    config = GimnasioConfig.get_config()

    if request.method == 'POST':
        estado       = request.POST.get('estado', config.estado)
        dias_json    = request.POST.get('dias_json', '[]')
        try:
            dias = json.loads(dias_json)
        except (ValueError, TypeError):
            dias = []

        horario_apertura = request.POST.get('horario_apertura', '07:00')
        horario_cierre   = request.POST.get('horario_cierre',   '17:00')
        capacidad        = request.POST.get('capacidad_maxima', 40)

        config.estado            = estado
        config.dias_habilitados  = dias
        config.horario_apertura  = horario_apertura
        config.horario_cierre    = horario_cierre
        config.capacidad_maxima  = int(capacidad)
        config.actualizado_por   = request.user
        config.save()

        messages.success(request, 'Configuración actualizada correctamente.')
        return redirect('admin_disponibilidad')

    dias_semana = [
        {'codigo': 'lun', 'label': 'LUN'},
        {'codigo': 'mar', 'label': 'MAR'},
        {'codigo': 'mie', 'label': 'MIÉ'},
        {'codigo': 'jue', 'label': 'JUE'},
        {'codigo': 'vie', 'label': 'VIE'},
        {'codigo': 'sab', 'label': 'SÁB'},
        {'codigo': 'dom', 'label': 'DOM'},
    ]

    return render(request, 'gimnasio/disponibilidad.html', {
        'config':          config,
        'dias_semana':     dias_semana,
        'dias_activos':    config.dias_habilitados,
        'seccion_activa':  'disponibilidad',
    })


# ── HORARIOS ────────────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_horarios(request):
    config = GimnasioConfig.get_config()
    return render(request, 'gimnasio/admin_horarios.html', {
        'config':         config,
        'seccion_activa': 'horarios',
    })


# ── FECHAS DE INGRESO ───────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_fechas_ingreso(request):
    config = GimnasioConfig.get_config()
    fechas = FechaIngreso.objects.filter(config=config)

    if request.method == 'POST':
        fecha_str   = request.POST.get('fecha', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        habilitada  = request.POST.get('habilitada') == 'on'

        if fecha_str:
            FechaIngreso.objects.create(
                config=config,
                fecha=fecha_str,
                descripcion=descripcion,
                habilitada=habilitada,
            )
            messages.success(request, 'Fecha de ingreso agregada.')
        else:
            messages.error(request, 'Debes ingresar una fecha válida.')

        return redirect('admin_fechas_ingreso')

    return render(request, 'gimnasio/admin_fechas_ingreso.html', {
        'fechas':         fechas,
        'seccion_activa': 'fechas_ingreso',
    })


# ── ELIMINAR FECHA ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_eliminar_fecha(request, pk):
    get_object_or_404(FechaIngreso, pk=pk).delete()
    messages.success(request, 'Fecha eliminada.')
    return redirect('admin_fechas_ingreso')


# ── CONFIGURACIÓN ───────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_configuracion(request):
    config = GimnasioConfig.get_config()
    return render(request, 'gimnasio/admin_configuracion.html', {
        'config':         config,
        'seccion_activa': 'configuracion',
    })


# ── NUEVO REGISTRO ──────────────────────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_nuevo_registro(request):
    return render(request, 'gimnasio/admin_nuevo_registro.html', {
        'seccion_activa': 'nuevo_registro',
    })

# ── VER TODAS LAS RESERVAS ──────────────────────────
@login_required
@user_passes_test(es_admin)
def admin_reservas(request):

    reservas = Reserva.objects.all().order_by(
        '-fecha_entrada',
        '-hora_entrada'
    )

    return render(request, 'gimnasio/gimnasio.html', {
        'admin_reservas': reservas,
        'seccion_activa': 'reservas',
        'config': GimnasioConfig.get_config(),
    })


# ── CANCELAR RESERVA ──────────────────────────
@login_required
@user_passes_test(es_admin)
def cancelar_reserva_admin(request, id):

    reserva = get_object_or_404(
        Reserva,
        codigo_registro=id
    )

    reserva.estado = 'Cancelada'
    reserva.save()

    messages.warning(
        request,
        'La reservación fue cancelada correctamente.'
    )
    
    request.session['abrir_admin'] = True
    request.session['seccion_admin'] = 'reservas'   
    return redirect('gimnasio')


# ── CERRAR / ABRIR GIMNASIO ──────────────────────────
@login_required
@user_passes_test(es_admin)
def cerrar_gimnasio(request):

    config = GimnasioConfig.get_config()

    if request.method == 'POST':

        accion = request.POST.get('accion')

        if accion == 'cerrar':
            config.estado = 'cerrada'
            messages.error(
                request,
                'El gimnasio fue cerrado.'
            )

        elif accion == 'abrir':
            config.estado = 'abierta'
            messages.success(
                request,
                'El gimnasio fue abierto.'
            )

        config.actualizado_por = request.user
        config.save()

    return redirect('gimnasio')