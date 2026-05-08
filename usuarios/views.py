from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from .models import Usuario
from inventario.models import Prestamo
from gimnasio.models import Reserva
from interfichas.models import EquipoInterfichas, TorneoInterfichas
from intercentros.models import TorneoIntercentros, Postulacion


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
    usuario = request.user

    # ── EDICIÓN DE PERFIL (POST) ──────────────────────────────────────────
    if request.method == 'POST':
        email   = request.POST.get('email')
        celular = request.POST.get('celular')
        if email:   usuario.email    = email
        if celular: usuario.telefono = celular
        if 'imagen' in request.FILES:
            usuario.foto_perfil = request.FILES.get('imagen')
        usuario.save()
        messages.success(request, '¡Perfil actualizado!')
        return redirect('perfil')

    hace_30_dias = timezone.now() - timedelta(days=30)

    # ── DATOS PARA ADMIN ──────────────────────────────────────────────────
    if usuario.is_staff:

        # Usuarios
        todos_usuarios   = Usuario.objects.all().order_by('-fecha_registro')
        ultimos_usuarios = todos_usuarios[:6]
        total_usuarios   = todos_usuarios.count()
        usuarios_activos = todos_usuarios.filter(estado='activo').count()
        nuevos_mes       = todos_usuarios.filter(fecha_registro__gte=hace_30_dias).count()

        # Préstamos — Corregido select_related (se quitó 'elemento')
        todos_prestamos = (
            Prestamo.objects
            .select_related('usuario')
            .prefetch_related('detalles__elemento')
            .order_by('-fecha_prestamo')
        )
        prestamos_recientes     = todos_prestamos.filter(fecha_prestamo__gte=hace_30_dias)
        total_prestamos_recientes = prestamos_recientes.count()
        prestamo_mas_reciente   = todos_prestamos.first()

        # Gimnasio — todos los registros
        todas_reservas = (
            Reserva.objects
            .order_by('-fecha_entrada', '-hora_entrada')
        )
        total_ingresos_gimnasio = todas_reservas.filter(
            fecha_entrada__gte=hace_30_dias.date()
        ).count()

        # Inter-fichas — todos los equipos con torneo
        todos_equipos_interfichas = (
            EquipoInterfichas.objects
            .select_related('torneo', 'disciplina')
            .order_by('-torneo__fecha_torneo_fichas')
        )
        torneos_interfichas_activos = TorneoInterfichas.objects.exclude(estado='cerrado').count()

        # Inter-centros — todos los equipos / postulaciones
        todas_postulaciones = (
            Postulacion.objects
            .select_related('torneo')
            .order_by('-fecha_postulacion')
        )
        torneos_intercentros_activos = TorneoIntercentros.objects.filter(estado='Activo').count()
        total_torneos_activos = torneos_interfichas_activos + torneos_intercentros_activos

        contexto = {
            'usuario': usuario,

            # Tabs con datos de TODOS
            'prestamos':             todos_prestamos,
            'reservas_gimnasio':     todas_reservas,
            'equipos_interfichas':   todos_equipos_interfichas,
            'equipos_intercentros':  todas_postulaciones,

            # Panel admin — usuarios
            'todos_usuarios':   todos_usuarios,
            'ultimos_usuarios': ultimos_usuarios,
            'total_usuarios':   total_usuarios,
            'usuarios_activos': usuarios_activos,

            # Novedades admin
            'total_prestamos_recientes':  total_prestamos_recientes,
            'prestamo_mas_reciente':      prestamo_mas_reciente,
            'total_ingresos_gimnasio':    total_ingresos_gimnasio,
            'total_torneos_activos':      total_torneos_activos,
            'nuevos_usuarios_mes':        nuevos_mes,
        }

    # ── DATOS PARA APRENDIZ ───────────────────────────────────────────────
    else:
        nombre_completo = f"{usuario.first_name} {usuario.last_name}"

        # Préstamos Aprendiz — Corregido select_related (se quitó 'elemento')
        prestamos = (
            Prestamo.objects
            .filter(usuario=usuario)
            .prefetch_related('detalles__elemento')
            .order_by('-fecha_prestamo')
        )

        reservas_gimnasio = (
            Reserva.objects
            .filter(usuario_solicitante=nombre_completo)
            .order_by('-fecha_entrada', '-hora_entrada')
        )

        equipos_interfichas = (
            EquipoInterfichas.objects
            .filter(usuario_registra=usuario)
            .select_related('torneo', 'disciplina')
        )

        equipos_intercentros = (
            Postulacion.objects
            .filter(numero_documento=str(usuario.numero_documento))
            .select_related('torneo')
            .order_by('-fecha_postulacion')
        )

        contexto = {
            'usuario':               usuario,
            'prestamos':             prestamos,
            'reservas_gimnasio':     reservas_gimnasio,
            'equipos_interfichas':   equipos_interfichas,
            'equipos_intercentros':  equipos_intercentros,
        }

    return render(request, 'usuarios/perfil.html', contexto)


@login_required(login_url='home')
def toggle_usuario_estado(request, user_id):
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
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos.')
        return redirect('perfil')
    if request.method == 'POST':
        u         = get_object_or_404(Usuario, pk=user_id)
        nuevo_rol = request.POST.get('rol')
        if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
            u.rol      = nuevo_rol
            u.is_staff = (nuevo_rol == 'admin')
            u.save()
            messages.success(request, f'Rol de {u.get_full_name()} cambiado a {nuevo_rol}.')
    return redirect('perfil')


@login_required(login_url='home')
def admin_editar_usuario(request, user_id):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('perfil')

    if request.method == 'POST':
        u = get_object_or_404(Usuario, pk=user_id)

        u.first_name       = request.POST.get('first_name',       u.first_name).strip()
        u.last_name        = request.POST.get('last_name',        u.last_name).strip()
        u.numero_documento = request.POST.get('numero_documento', u.numero_documento).strip()
        u.ficha            = request.POST.get('ficha',            u.ficha or '').strip()
        u.email            = request.POST.get('email',            u.email).strip()
        u.telefono         = request.POST.get('telefono',         u.telefono or '').strip()
        u.username         = u.numero_documento  # mantener sincronizado

        nuevo_rol = request.POST.get('rol', u.rol)
        if nuevo_rol in ['aprendiz', 'instructor', 'admin']:
            u.rol      = nuevo_rol
            u.is_staff = (nuevo_rol == 'admin')

        nuevo_estado = request.POST.get('estado', u.estado)
        if nuevo_estado in ['activo', 'inactivo']:
            u.estado    = nuevo_estado
            u.is_active = (nuevo_estado == 'activo')

        try:
            u.save()
            messages.success(request, f'Datos de {u.get_full_name()} actualizados correctamente.')
        except IntegrityError:
            messages.error(request, 'Error: ya existe un usuario con ese documento o correo.')

    return redirect('perfil')