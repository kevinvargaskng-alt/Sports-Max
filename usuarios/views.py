from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

# ── Módulos de seguridad ──────────────────────────────────────
from core.security.audit import log_login_attempt, log_admin_action, log_suspicious_request
from core.security.sanitizers import sanitize_html, sanitize_input
from core.security.validators import validate_email_strict, validate_text_safe
from core.security.file_upload import validate_uploaded_file
from core.security.decorators import role_required, allowed_fields

# Importaciones de modelos de otras apps
from .models import Usuario, Sugerencia
from inventario.models import Prestamo
from gimnasio.models import Reserva, GimnasioConfig
from interfichas.models import EquipoInterfichas, TorneoInterfichas


def login_view(request):
    """Procesa el inicio de sesión con soporte para documento o correo, AJAX y POST estándar."""
    if request.method == 'POST':
        doc = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get(
            'next') or request.GET.get('next') or '/perfil/'

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

        if not doc or not password:
            msg = 'Por favor ingrese su documento/correo y contraseña.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('home')

        # Intentar obtener el usuario por username, numero_documento o email
        from django.utils import timezone as _tz
        import datetime as _dt
        from django.db.models import Q

        try:
            usuario_obj = Usuario.objects.get(
                Q(username__iexact=doc) | Q(numero_documento__iexact=doc) | Q(email__iexact=doc)
            )
        except Usuario.DoesNotExist:
            usuario_obj = None
        except Usuario.MultipleObjectsReturned:
            usuario_obj = Usuario.objects.filter(
                Q(username__iexact=doc) | Q(numero_documento__iexact=doc) | Q(email__iexact=doc)
            ).first()

        # Verificar si la cuenta está inactiva
        if usuario_obj and (not usuario_obj.is_active or usuario_obj.estado == 'inactivo'):
            msg = 'Tu cuenta se encuentra inactiva. Comunícate con un administrador para activarla.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'success': False, 'message': msg}, status=403)
            messages.error(request, msg)
            return redirect('home')

        # Verificar si la cuenta está bloqueada temporalmente por intentos fallidos
        if usuario_obj and usuario_obj.bloqueado_hasta:
            ahora = _tz.localtime(_tz.now())
            if ahora < usuario_obj.bloqueado_hasta:
                minutos_restantes = int(
                    (usuario_obj.bloqueado_hasta - ahora).total_seconds() / 60) + 1
                msg = f'Cuenta bloqueada. Intente de nuevo en {minutos_restantes} minuto(s).'
                if is_ajax:
                    return JsonResponse({
                        'status': 'blocked',
                        'success': False,
                        'bloqueado': True,
                        'minutos': minutos_restantes,
                        'message': msg
                    }, status=403)
                messages.error(request, msg)
                return redirect('home')
            else:
                # Tiempo de bloqueo expirado — resetear
                usuario_obj.intentos_fallidos = 0
                usuario_obj.bloqueado_hasta = None
                usuario_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

        username_auth = usuario_obj.username if usuario_obj else doc
        user = authenticate(request, username=username_auth, password=password)
        if user:
            # Login exitoso: resetear intentos
            if usuario_obj:
                usuario_obj.intentos_fallidos = 0
                usuario_obj.bloqueado_hasta = None
                usuario_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
            login(request, user)
            # ── Auditoría: login exitoso ──
            log_login_attempt(request, user.username, success=True)
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'success': True,
                    'redirect': next_url,
                    'message': 'Bienvenido al sistema'
                })
            messages.success(request, 'Bienvenido al sistema')
            return redirect(next_url)

        # Fallo de autenticación
        log_login_attempt(request, doc, success=False, reason='credenciales_invalidas')
        if usuario_obj:
            usuario_obj.intentos_fallidos += 1
            intentos = usuario_obj.intentos_fallidos

            if intentos >= 6:
                # Bloqueo de 24 horas
                usuario_obj.bloqueado_hasta = _tz.now() + _dt.timedelta(hours=24)
                usuario_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
                msg = 'Cuenta bloqueada por 24 horas por múltiples intentos fallidos.'
                if is_ajax:
                    return JsonResponse({
                        'status': 'blocked',
                        'success': False,
                        'bloqueado': True,
                        'minutos': 1440,
                        'message': msg
                    }, status=403)
                messages.error(request, msg)
                return redirect('home')
            elif intentos >= 3:
                # Bloqueo de 5 minutos
                usuario_obj.bloqueado_hasta = _tz.now() + _dt.timedelta(minutes=5)
                usuario_obj.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
                msg = f'Cuenta bloqueada por 5 minutos. Intento {intentos}/6.'
                if is_ajax:
                    return JsonResponse({
                        'status': 'blocked',
                        'success': False,
                        'bloqueado': True,
                        'minutos': 5,
                        'message': msg
                    }, status=403)
                messages.error(request, msg)
                return redirect('home')
            else:
                usuario_obj.save(update_fields=['intentos_fallidos'])
                msg = 'Documento/correo o contraseña incorrectos.'
                if is_ajax:
                    return JsonResponse({
                        'status': 'error',
                        'success': False,
                        'message': msg
                    }, status=401)
                messages.error(request, msg)
                return redirect('home')

        msg = 'Documento/correo o contraseña incorrectos.'
        if is_ajax:
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': msg
            }, status=401)
        messages.error(request, msg)
        return redirect('home')

    return redirect('home')


@require_POST
def desbloquear_cuenta_view(request):
    """Permite desbloquear la cuenta ingresando datos de validación."""
    doc = request.POST.get('numero_documento', '').strip()
    correo = request.POST.get('email', '').strip().lower()
    telefono = request.POST.get('telefono', '').strip()

    if not doc or not correo or not telefono:
        return JsonResponse({'status': 'error', 'message': 'Todos los campos son obligatorios.'}, status=400)

    try:
        from django.db.models import Q
        u = Usuario.objects.get(
            Q(username=doc) | Q(numero_documento=doc),
            email__iexact=correo,
            telefono=telefono
        )
        u.intentos_fallidos = 0
        u.bloqueado_hasta = None
        u.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
        return JsonResponse({'status': 'success', 'message': 'Cuenta desbloqueada. Ya puedes iniciar sesión.'})
    except (Usuario.DoesNotExist, Usuario.MultipleObjectsReturned):
        return JsonResponse({'status': 'error', 'message': 'Los datos no coinciden con ningún usuario registrado.'}, status=400)


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

    context = {
        'abrir_admin': abrir_admin,
        'seccion_activa': seccion_admin,
        'reservas': mis_reservas,
        'esta_abierto': esta_abierto,
        'ahora': ahora,
        'es_fin_de_semana': es_fin_de_semana,
        'es_festivo': es_festivo,
        'config': config,
        'admin_reservas': Reserva.objects.all().order_by('-fecha_entrada', '-hora_entrada')
    }
    return render(request, 'gimnasio/gimnasio.html', context)


def registro_view(request):
    """Procesa el registro con validaciones de seguridad"""
    CLAVES_COMUNES = [
        '12345678', '123456789', '1234567890', 'password', 'contrasena',
        'contraseña', 'qwerty', 'abcdefgh', '11111111', '00000000',
        'admin123', 'password1', '12341234', 'abc12345',
    ]

    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento', '').strip()
        nombres = request.POST.get('nombres', '').strip().title()
        apellidos = request.POST.get('apellidos', '').strip().title()
        contrasena = request.POST.get('contrasena', '').strip()
        correo = request.POST.get('email', '').strip()
        tipo_doc = request.POST.get('tipo_documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        ficha = request.POST.get('ficha', '').strip()
        programa = request.POST.get('programa_formacion', '').strip()
        genero = request.POST.get('genero', '').strip()

        if not genero:
            return JsonResponse({'status': 'error', 'message': 'El campo género es obligatorio.'}, status=400)

        # ── Validación de email estricta ──
        try:
            validate_email_strict(correo)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e.message)}, status=400)

        # ── Validación de contraseña robusta (12+ caracteres, complejidad, breached list) ──
        # Crear usuario temporal para que los validadores puedan verificar datos personales
        temp_user = Usuario(username=numero_documento, email=correo,
                            first_name=nombres, last_name=apellidos,
                            numero_documento=numero_documento)
        try:
            validate_password(contrasena, user=temp_user)
        except ValidationError as e:
            # Retornar el primer error de validación
            return JsonResponse({'status': 'error', 'message': e.messages[0]}, status=400)

        # ── Sanitización de campos de texto ──
        nombres = validate_text_safe(nombres, 'nombre', max_length=100)
        apellidos = validate_text_safe(apellidos, 'apellidos', max_length=100)

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
                genero=genero,
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
                comentario=sanitize_html(sanitize_input(comentario, max_length=2000)),
                anonimo=False,
                imagen=validate_uploaded_file(request.FILES.get('imagen_error'), allowed_types='image') if request.FILES.get('imagen_error') else None
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
        eliminar_foto = request.POST.get('eliminar_foto') == 'true'
        foto_posicion = request.POST.get('foto_posicion')

        if email:
            usuario.email = email
        if celular:
            usuario.telefono = celular
        
        if eliminar_foto:
            usuario.foto_perfil = None
            usuario.foto_posicion = '50% 50%'
        elif 'imagen' in request.FILES:
            try:
                validated_img = validate_uploaded_file(request.FILES.get('imagen'), allowed_types='image')
                usuario.foto_perfil = validated_img
            except ValidationError as e:
                messages.error(request, str(e.message))
                return redirect('perfil')
            
        if foto_posicion:
            usuario.foto_posicion = foto_posicion

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
@require_POST
def toggle_usuario_estado(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    # Seguridad: evitar que un admin se bloquee a sí mismo
    if int(user_id) == request.user.id:
        messages.error(
            request, "Acceso denegado: No puedes bloquear tu propia cuenta de administrador.")
        return redirect('gestionar_usuarios')

    u = get_object_or_404(Usuario, pk=user_id)
    u.is_active = not u.is_active
    u.estado = 'activo' if u.is_active else 'inactivo'
    u.save()
    return redirect('gestionar_usuarios')


@login_required(login_url='home')
@require_POST
def cambiar_rol_usuario(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    u = get_object_or_404(Usuario, pk=user_id)
    nuevo_rol = request.POST.get('rol')

    # ── Protección contra escalación a superuser ──
    if nuevo_rol == 'admin' and not request.user.is_superuser:
        log_suspicious_request(request, 'Intento de escalación de rol a admin sin ser superuser')
        messages.error(request, 'Solo un superusuario puede asignar el rol de administrador.')
        return redirect('gestionar_usuarios')

    if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
        u.rol = nuevo_rol
        u.is_staff = (nuevo_rol == 'admin')
        u.save()
        log_admin_action(request, 'CAMBIAR_ROL', 'Usuario', str(user_id),
                         f'Nuevo rol: {nuevo_rol}')
    return redirect('gestionar_usuarios')


@login_required(login_url='home')
@require_POST
@allowed_fields('first_name', 'last_name', 'email')
def admin_editar_usuario(request, user_id):
    if not request.user.is_staff:
        return redirect('perfil')
    u = get_object_or_404(Usuario, pk=user_id)
    u.first_name = validate_text_safe(
        request.POST.get('first_name', u.first_name).strip(), 'nombre', max_length=100
    ).title()
    u.last_name = validate_text_safe(
        request.POST.get('last_name', u.last_name).strip(), 'apellidos', max_length=100
    ).title()
    new_email = request.POST.get('email', u.email).strip()
    try:
        validate_email_strict(new_email)
        u.email = new_email
    except ValidationError:
        messages.error(request, 'Correo electrónico inválido.')
        return redirect('gestionar_usuarios')
    u.save()
    log_admin_action(request, 'EDITAR_USUARIO', 'Usuario', str(user_id),
                     f'Campos: first_name, last_name, email')
    messages.success(request, f'Datos de {u.get_full_name()} actualizados correctamente.')
    return redirect('gestionar_usuarios')


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


@login_required
def export_database_backup(request):
    """Genera y descarga un respaldo completo de la base de datos en formato JSON."""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso denegado: Se requieren privilegios de administrador.")

    import io
    from django.core import management
    from django.http import HttpResponse

    output = io.StringIO()
    try:
        management.call_command('dumpdata', stdout=output, indent=2, exclude=['contenttypes', 'auth.Permission'])
        log_admin_action(request, 'EXPORT_DB_BACKUP', 'Database', '', 'Respaldo completo generado')
        response = HttpResponse(output.getvalue(), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="respaldo_base_datos.json"'
        return response
    except Exception:
        messages.error(request, 'Error al generar el respaldo de la base de datos.')
        return redirect('perfil')


@login_required
def restore_database_backup(request):
    """Restaura la base de datos a partir de un archivo JSON subido."""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso denegado: Se requieren privilegios de administrador.")

    if request.method == 'POST' and request.FILES.get('backup_file'):
        backup_file = request.FILES['backup_file']
        if not backup_file.name.endswith('.json'):
            messages.error(request, "Formato de archivo inválido. Debe ser un archivo .json")
            return redirect('gestionar_usuarios')

        import tempfile
        import os
        from django.core import management

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
                for chunk in backup_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Cargar los datos a la base de datos
            management.call_command('loaddata', temp_path)
            log_admin_action(request, 'RESTORE_DB_BACKUP', 'Database', '', 'Respaldo restaurado')
            messages.success(request, 'Base de datos restaurada exitosamente desde el respaldo JSON.')
        except Exception:
            messages.error(request, 'Error al restaurar la base de datos.')
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    else:
        messages.error(request, "No se ha proporcionado ningún archivo para restaurar.")

    return redirect('gestionar_usuarios')


