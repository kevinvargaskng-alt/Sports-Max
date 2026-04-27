from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from .models import Usuario

from inventario.models import Prestamo


def login_view(request):
    """Procesa el inicio de sesión vía AJAX"""
    if request.method == 'POST':
        doc      = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=doc, password=password)
        if user:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'success': True,
                'redirect': '/perfil/',
                'message': 'Bienvenido al sistema'
            })

        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Documento o contraseña incorrectos'
        }, status=401)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def registro_view(request):
    """Procesa el registro con validaciones de seguridad"""
    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento', '').strip()
        nombres          = request.POST.get('nombres', '').strip()
        apellidos        = request.POST.get('apellidos', '').strip()
        contrasena       = request.POST.get('contrasena', '').strip()
        correo           = request.POST.get('email', '').strip()
        tipo_doc         = request.POST.get('tipo_documento', '').strip()
        telefono         = request.POST.get('telefono', '').strip()
        ficha            = request.POST.get('ficha', '').strip()
        programa         = request.POST.get('programa_formacion', '').strip()

        required_fields = {
            'numero_documento': numero_documento, 'nombres': nombres,
            'apellidos': apellidos, 'contrasena': contrasena,
            'email': correo, 'tipo_documento': tipo_doc,
            'telefono': telefono, 'ficha': ficha, 'programa_formacion': programa
        }

        for field, value in required_fields.items():
            if not value:
                return JsonResponse({'status': 'error', 'message': f'El campo {field} es obligatorio.'}, status=400)

        if Usuario.objects.filter(numero_documento=numero_documento).exists():
            return JsonResponse({'status': 'error', 'message': 'El documento ya existe'}, status=400)

        if Usuario.objects.filter(email=correo).exists():
            return JsonResponse({'status': 'error', 'message': 'Este correo ya está en uso'}, status=400)

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

        except IntegrityError as e:
            print(f"\n[❌ ERROR DE INTEGRIDAD EN LA BASE DE DATOS] -> {e}\n")
            return JsonResponse({'status': 'error', 'message': 'Error de base de datos. Revisa la consola.'}, status=400)

        except Exception as e:
            print(f"\n[⚠️ ERROR INESPERADO AL REGISTRAR] -> {e}\n")
            return JsonResponse({'status': 'error', 'message': 'Ocurrió un error inesperado.'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='home')
def perfil_view(request):
    """Muestra el perfil. Si el usuario es staff, también muestra
    los últimos registros y la lista completa de usuarios."""
    usuario = request.user

    # ── EDICIÓN DE PERFIL (POST) ──────────────────────────────────────────
    if request.method == 'POST':
        email   = request.POST.get('email')
        celular = request.POST.get('celular')
        if email:  usuario.email    = email
        if celular: usuario.telefono = celular
        if 'imagen' in request.FILES:
            usuario.foto_perfil = request.FILES.get('imagen')
        usuario.save()
        messages.success(request, '¡Perfil actualizado!')
        return redirect('perfil')

    # ── DATOS DEL PERFIL NORMAL ───────────────────────────────────────────
    prestamos = Prestamo.objects.filter(usuario=usuario).order_by('-fecha_prestamo')

    contexto = {
        'usuario':  usuario,
        'prestamos': prestamos,
    }

    # ── DATOS EXTRA SOLO PARA ADMINS (is_staff) ───────────────────────────
    if usuario.is_staff:
        todos_usuarios    = Usuario.objects.all().order_by('-fecha_registro')
        ultimos_usuarios  = todos_usuarios[:6]          # los 6 más recientes
        total_usuarios    = todos_usuarios.count()
        usuarios_activos  = todos_usuarios.filter(estado='activo').count()

        contexto.update({
            'todos_usuarios':   todos_usuarios,
            'ultimos_usuarios': ultimos_usuarios,
            'total_usuarios':   total_usuarios,
            'usuarios_activos': usuarios_activos,
        })

    return render(request, 'usuarios/perfil.html', contexto)


@login_required(login_url='home')
def toggle_usuario_estado(request, user_id):
    """Activa o desactiva un usuario. Solo staff."""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos.')
        return redirect('perfil')
    if request.method == 'POST':
        u = get_object_or_404(Usuario, pk=user_id)
        if u.estado == 'activo':
            u.estado    = 'inactivo'
            u.is_active = False
            messages.warning(request, f'{u.get_full_name()} desactivado.')
        else:
            u.estado    = 'activo'
            u.is_active = True
            messages.success(request, f'{u.get_full_name()} activado.')
        u.save()
    return redirect('perfil')


@login_required(login_url='home')
def cambiar_rol_usuario(request, user_id):
    """Cambia el rol de un usuario. Solo staff."""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos.')
        return redirect('perfil')
    if request.method == 'POST':
        u        = get_object_or_404(Usuario, pk=user_id)
        nuevo_rol = request.POST.get('rol')
        if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
            u.rol      = nuevo_rol
            u.is_staff = (nuevo_rol == 'admin')
            u.save()
            messages.success(request, f'Rol de {u.get_full_name()} cambiado a {nuevo_rol}.')
    return redirect('perfil')


# ── NUEVA VISTA PARA EDICIÓN COMPLETA DEL ADMINISTRADOR ────────────────────
@login_required(login_url='home')
def admin_editar_usuario(request, user_id):
    """Permite al administrador editar todos los datos de un usuario a través del modal."""
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado. No tienes permisos de administrador.')
        return redirect('perfil')

    if request.method == 'POST':
        usuario_editado = get_object_or_404(Usuario, pk=user_id)

        # Extraemos los datos del modal; si no viene alguno, conservamos el actual
        usuario_editado.first_name = request.POST.get('first_name', usuario_editado.first_name).strip()
        usuario_editado.last_name = request.POST.get('last_name', usuario_editado.last_name).strip()
        usuario_editado.numero_documento = request.POST.get('numero_documento', usuario_editado.numero_documento).strip()
        usuario_editado.ficha = request.POST.get('ficha', usuario_editado.ficha).strip()
        usuario_editado.email = request.POST.get('email', usuario_editado.email).strip()
        usuario_editado.telefono = request.POST.get('telefono', usuario_editado.telefono).strip()

        # Actualizamos el username para que coincida con el nuevo documento si este se cambió
        usuario_editado.username = usuario_editado.numero_documento

        # Rol y staff status
        nuevo_rol = request.POST.get('rol', usuario_editado.rol)
        if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
            usuario_editado.rol = nuevo_rol
            usuario_editado.is_staff = (nuevo_rol == 'admin')

        # Estado y active status
        nuevo_estado = request.POST.get('estado', usuario_editado.estado)
        if nuevo_estado in ['activo', 'inactivo']:
            usuario_editado.estado = nuevo_estado
            usuario_editado.is_active = (nuevo_estado == 'activo')

        # Guardamos en base de datos
        try:
            usuario_editado.save()
            messages.success(request, f'Los datos de {usuario_editado.get_full_name()} han sido actualizados correctamente.')
        except IntegrityError:
            messages.error(request, 'Error: Ya existe un usuario con ese número de documento o correo electrónico.')

    return redirect('perfil')