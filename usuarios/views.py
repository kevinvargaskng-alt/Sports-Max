from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Usuario
from gimnasio.models import Reserva
from inventario.models import Prestamo
from interfichas.models import EquipoInterfichas
from intercentros.models import EquipoIntercentros


def login_view(request):
    if request.method == 'POST':
        doc      = request.POST.get('username')
        password = request.POST.get('password')
        user     = authenticate(request, username=doc, password=password)
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/perfil/'})
        return JsonResponse({'success': False, 'error': 'Documento o contraseña incorrectos'}, status=401)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def registro_view(request):
    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento')
        tipo_documento   = request.POST.get('tipo_documento')
        nombres          = request.POST.get('nombres')
        apellidos        = request.POST.get('apellidos')
        telefono         = request.POST.get('telefono')
        genero           = request.POST.get('genero', '')
        estado           = request.POST.get('estado', 'activo')
        contrasena       = request.POST.get('contrasena')

        if not all([numero_documento, nombres, apellidos, telefono, contrasena]):
            return JsonResponse({'success': False, 'error': 'Todos los campos obligatorios son requeridos'}, status=400)

        if Usuario.objects.filter(numero_documento=numero_documento).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un usuario con ese número de documento'}, status=400)

        user = Usuario.objects.create_user(
            username         = numero_documento,
            password         = contrasena,
            first_name       = nombres,
            last_name        = apellidos,
            numero_documento = numero_documento,
            tipo_documento   = tipo_documento,
            telefono         = telefono,
            genero           = genero,
            estado           = estado,
            rol              = 'aprendiz',
        )
        login(request, user)
        return JsonResponse({'success': True, 'redirect': '/perfil/'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='home')
def perfil_view(request):
    usuario = request.user

    reservas = Reserva.objects.filter(
        usuario_solicitante__icontains=usuario.get_full_name()
    ).order_by('-fecha_entrada')

    prestamos = Prestamo.objects.filter(
        observacion_prestamo__icontains=usuario.get_full_name()
    ).order_by('-fecha_prestamo')

    equipos_interfichas  = EquipoInterfichas.objects.all().order_by('-codigo_equipo_interfichas')
    equipos_intercentros = EquipoIntercentros.objects.all().order_by('-codigo_equipo_centro')

    return render(request, 'usuarios/perfil.html', {
        'usuario': usuario,
        'reservas': reservas,
        'prestamos': prestamos,
        'equipos_interfichas': equipos_interfichas,
        'equipos_intercentros': equipos_intercentros,
    })