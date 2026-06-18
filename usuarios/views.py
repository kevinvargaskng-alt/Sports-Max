from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone


# Importaciones de modelos de otras apps
from .models import Usuario, Sugerencia
from inventario.models import Prestamo
from gimnasio.models import Reserva, GimnasioConfig  # Agregado GimnasioConfig
from interfichas.models import EquipoInterfichas, TorneoInterfichas


def login_view(request):
    """Procesa el inicio de sesión vía AJAX"""
    if request.method == 'POST':
        doc = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get(
            'next') or request.GET.get('next') or '/perfil/'

        user = authenticate(request, username=doc, password=password)
        if user:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'success': True,
                'redirect': next_url,
                'message': 'Bienvenido al sistema'
            })

        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Documento o contraseña incorrectos'
        }, status=401)

    # Si es un GET, enviamos a la home o donde tengas el formulario
    return redirect('home')


@login_required
def gimnasio_list(request):
    """
    Controla el acceso al gimnasio y muestra el historial personal.
    """
    # 1. DEFINIR IDENTIDAD PARA FILTRADO
    # Filtramos por el objeto usuario para cumplir con la ForeignKey (MER)
    mis_reservas = Reserva.objects.filter(
        usuario_solicitante=request.user
    ).order_by('-fecha_entrada', '-hora_entrada')

    # 2. LÓGICA DE CONTROL DE ACCESO
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

    # 3. PROCESAR REGISTRO DE ENTRADA (POST)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear_reserva':
            if not esta_abierto:
                messages.error(
                    request, "Acceso denegado: El sistema de registro está bloqueado en este momento.")
                return redirect('gimnasio')

            try:
                Reserva.objects.create(
                    usuario_solicitante=request.user,
                    fecha_entrada=ahora.date(),
                    hora_entrada=ahora.time(),
                    hora_prestamo=ahora.time(),
                    fecha_permanencia=ahora.date(),
                    hora_salida=ahora.time(),
                    fecha_salida=ahora.date(),
                    estado='Activa'
                )
                messages.success(
                    request, f"¡Entrada registrada! Bienvenido(a), {request.user.first_name}.")
            except Exception as e:
                messages.error(
                    request, f"Error técnico al registrar asistencia: {e}")

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
        'admin_reservas': Reserva.objects.all().order_by('-fecha_entrada', '-hora_entrada')
    })


def registro_view(request):
    """Procesa el registro con validaciones de seguridad"""
    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento', '').strip()
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        contrasena = request.POST.get('contrasena', '').strip()
        correo = request.POST.get('email', '').strip()
        tipo_doc = request.POST.get('tipo_documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        ficha = request.POST.get('ficha', '').strip()
        programa = request.POST.get('programa_formacion', '').strip()

        if Usuario.objects.filter(numero_documento=numero_documento).exists():
            return JsonResponse({'status': 'error', 'message': 'El documento ya existe'}, status=400)

        try:
            user = Usuario(
                username=numero_documento,
                email=correo,
                first_name=nombres,
                last_name=apellidos,
                numero_documento=numero_documento,
                tipo_documento=tipo_doc,
                telefono=telefono,
                ficha=ficha,
                programa_formacion=programa,
                rol='aprendiz'
            )
            user.set_password(contrasena)
            user.save()

            login(request, user)
            return JsonResponse({'status': 'success', 'redirect': '/perfil/', 'message': 'Registro exitoso'})

        except IntegrityError:
            return JsonResponse({'status': 'error', 'message': 'Error de integridad en base de datos.'}, status=400)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Ocurrió un error inesperado.'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='home')
def perfil_view(request):
    usuario = request.user

    if request.method == 'POST':
        tipo_post = request.POST.get('tipo')

        # --- CASO 1: BORRAR REPORTE ---
        if tipo_post == 'borrar_reporte':
            reporte_id = request.POST.get('reporte_id')
            reporte = get_object_or_404(
                Sugerencia, id=reporte_id, usuario=usuario)
            if not reporte.respuesta:
                reporte.delete()
                messages.success(request, 'Reporte eliminado con éxito.')
            return redirect('perfil')

        # --- CASO 2: EDITAR REPORTE ---
        if tipo_post == 'editar_reporte':
            reporte_id = request.POST.get('reporte_id')
            nuevo_comentario = request.POST.get('comentario')
            reporte = get_object_or_404(
                Sugerencia, id=reporte_id, usuario=usuario)
            if not reporte.respuesta:
                reporte.comentario = nuevo_comentario
                reporte.save()
                messages.success(request, 'Reporte actualizado con éxito.')
            return redirect('perfil')

        # --- CASO 3: RESPONDER REPORTE (ADMIN) ---
        if tipo_post == 'responder_reporte' and usuario.is_staff:
            reporte_id = request.POST.get('reporte_id')
            respuesta_texto = request.POST.get('respuesta')
            reporte = get_object_or_404(Sugerencia, id=reporte_id)
            reporte.respuesta = respuesta_texto
            reporte.save()
            messages.success(
                request, 'Respuesta enviada al aprendiz correctamente.')
            return redirect('perfil')

        # Procesar Buzón de Sugerencias
        if 'comentario' in request.POST:
            tipo = request.POST.get('tipo', 'otro')
            comentario = request.POST.get('comentario')

            sugerencia = Sugerencia.objects.create(
                usuario=usuario,
                tipo=tipo,
                comentario=comentario,
                anonimo=False,
                imagen=request.FILES.get('imagen_error')
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'reporte': {
                        'id': sugerencia.id,
                        'tipo': sugerencia.tipo,
                        'comentario': sugerencia.comentario,
                        'fecha': timezone.localtime(sugerencia.fecha).strftime("%d/%m/%Y %H:%M"),
                        'imagen_url': sugerencia.imagen.url if sugerencia.imagen else None,
                    }
                })
            messages.success(
                request, '¡Gracias! Tu reporte de error ha sido enviado exitosamente.')
            return redirect('perfil')

        email = request.POST.get('email')
        celular = request.POST.get('celular')
        if email:
            usuario.email = email
        if celular:
            usuario.telefono = celular
        if 'imagen' in request.FILES:
            usuario.foto_perfil = request.FILES.get('imagen')
        usuario.save()
        messages.success(request, '¡Perfil actualizado!')
        return redirect('perfil')

    # Reportes propios para cualquier usuario (Mis Reportes)
    mis_sugerencias = Sugerencia.objects.filter(
        usuario=usuario).order_by('-fecha')

    if usuario.is_staff:
        todos_usuarios = Usuario.objects.all().order_by('-fecha_registro')
        # Préstamos Admin
        todos_prestamos = Prestamo.objects.select_related('usuario').prefetch_related(
            'detalles__elemento').order_by('-fecha_prestamo')
        # Gimnasio Admin
        todas_reservas = Reserva.objects.all().order_by(
            '-fecha_entrada', '-hora_entrada')
        # Sugerencias Admin
        todas_sugerencias = Sugerencia.objects.all().order_by('-fecha')

        contexto = {
            'usuario': usuario,
            'prestamos': todos_prestamos,
            'reservas_gimnasio': todas_reservas,
            'sugerencias_usuario': mis_sugerencias,
            'reportes_todos': todas_sugerencias,
            'todos_usuarios': todos_usuarios,
            'total_usuarios': todos_usuarios.count(),
            'total_torneos_activos': TorneoInterfichas.objects.exclude(estado='cerrado').count(),
        }

    else:
        # APRENDIZ: Filtrado por OBJETO de usuario (ForeignKey)
        prestamos = Prestamo.objects.filter(usuario=usuario).prefetch_related(
            'detalles__elemento').order_by('-fecha_prestamo')

        # CORRECCIÓN CLAVE: Se filtra por el objeto 'usuario', NO por el string del nombre
        reservas_gimnasio = Reserva.objects.filter(
            usuario_solicitante=usuario).order_by('-fecha_entrada', '-hora_entrada')

        contexto = {
            'usuario': usuario,
            'prestamos': prestamos,
            'reservas_gimnasio': reservas_gimnasio,
            'sugerencias_usuario': mis_sugerencias,
            'equipos_interfichas': EquipoInterfichas.objects.filter(usuario_registra=usuario),
        }

    return render(request, 'usuarios/perfil.html', contexto)

# --- Las demás funciones (toggle, cambiar_rol, editar) se mantienen igual ---


@login_required(login_url='home')
def toggle_usuario_estado(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    if request.method == 'POST':
        # Seguridad: evitar que un admin se bloquee a sí mismo
        if int(user_id) == request.user.id:
            messages.error(
                request, "Acceso denegado: No puedes bloquear tu propia cuenta de administrador.")
            return redirect('perfil')

        u = get_object_or_404(Usuario, pk=user_id)
        u.is_active = not u.is_active
        u.estado = 'activo' if u.is_active else 'inactivo'
        u.save()
    return redirect('perfil')


@login_required(login_url='home')
def cambiar_rol_usuario(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    if request.method == 'POST':
        u = get_object_or_404(Usuario, pk=user_id)
        nuevo_rol = request.POST.get('rol')
        if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
            u.rol = nuevo_rol
            u.is_staff = (nuevo_rol == 'admin')
            u.save()
    return redirect('perfil')


@login_required(login_url='home')
def admin_editar_usuario(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    if request.method == 'POST':
        u = get_object_or_404(Usuario, pk=user_id)
        u.first_name = request.POST.get('first_name', u.first_name).strip()
        u.last_name = request.POST.get('last_name', u.last_name).strip()
        u.email = request.POST.get('email', u.email).strip()
        u.save()
    return redirect('perfil')


@login_required(login_url='home')
def gestionar_usuarios_view(request):
    """Vista para la página de gestión de usuarios exclusiva para admins"""
    if not request.user.is_staff:
        messages.error(
            request, 'No tienes permisos para acceder a esta página.')
        return redirect('perfil')

    todos_usuarios = Usuario.objects.all().order_by('-fecha_registro')
    total_usuarios = todos_usuarios.count()
    total_activos = todos_usuarios.filter(is_active=True).count()
    total_bloqueados = todos_usuarios.filter(is_active=False).count()

    contexto = {
        'usuario': request.user,
        'todos_usuarios': todos_usuarios,
        'total_usuarios': total_usuarios,
        'total_activos': total_activos,
        'total_bloqueados': total_bloqueados,
    }
    return render(request, 'usuarios/gestionar_usuarios.html', contexto)
