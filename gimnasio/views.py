from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Reserva

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

    # El sistema solo permite ingreso si cumple todas las condiciones
    esta_abierto = horario_ok and not es_fin_de_semana and not es_festivo

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
                    estado='Activo'
                )
                messages.success(request, f"¡Entrada registrada! Bienvenido(a), {request.user.first_name}.")
            except Exception as e:
                messages.error(request, f"Error técnico al registrar asistencia: {e}")
            
            return redirect('gimnasio')

    # 4. RENDERIZADO
    return render(request, 'gimnasio/gimnasio.html', {
        'reservas': mis_reservas,
        'esta_abierto': esta_abierto,
        'ahora': ahora,
        'es_fin_de_semana': es_fin_de_semana,
        'es_festivo': es_festivo
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