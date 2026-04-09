from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError  # Importación clave para manejar duplicados
from .models import Usuario # Importamos tu modelo personalizado

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
    """Procesa el registro vía AJAX"""
    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento')
        nombres          = request.POST.get('nombres')
        apellidos        = request.POST.get('apellidos')
        contrasena       = request.POST.get('contrasena')
        correo           = request.POST.get('email')  # <-- Capturamos el correo
        
        # Validación de documento duplicado
        if Usuario.objects.filter(numero_documento=numero_documento).exists():
            return JsonResponse({'status': 'error', 'success': False, 'message': 'El documento ya está registrado'}, status=400)

        # Validación de correo duplicado
        if Usuario.objects.filter(email=correo).exists():
            return JsonResponse({'status': 'error', 'success': False, 'message': 'Este correo ya está en uso'}, status=400)

        try:
            # Creamos el usuario agregando el email
            user = Usuario.objects.create_user(
                username=numero_documento,
                email=correo,  # <-- Guardamos el correo en el sistema nativo
                password=contrasena,
                first_name=nombres,
                last_name=apellidos
            )

            # Asignamos los campos extra
            user.numero_documento = numero_documento
            user.tipo_documento   = request.POST.get('tipo_documento')
            user.telefono         = request.POST.get('telefono')
            user.genero           = request.POST.get('genero')
            user.ficha            = request.POST.get('ficha') 
            user.programa_formacion = request.POST.get('programa_formacion') 
            user.rol              = 'aprendiz'
            user.save()

            # Lo logueamos de una vez
            login(request, user)
            return JsonResponse({
                'status': 'success', 
                'success': True, 
                'redirect': '/perfil/', 
                'message': 'Registro exitoso. Redirigiendo...'
            })
        
        # Atrapamos errores de duplicados (por si fallan las validaciones de arriba)
        except IntegrityError:
            return JsonResponse({
                'status': 'error', 
                'success': False, 
                'message': 'Error de integridad: El documento o correo ya existen en el sistema.'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    """Cierra la sesión y manda al inicio"""
    logout(request)
    return redirect('home')


@login_required(login_url='home')
def perfil_view(request):
    """Muestra y edita el perfil (Solo usuarios logueados)"""
    usuario = request.user

    if request.method == 'POST':
        email = request.POST.get('email')
        celular = request.POST.get('celular') 

        if email:
            usuario.email = email
        if celular is not None:
            usuario.telefono = celular 

        if 'imagen' in request.FILES:
            usuario.foto_perfil = request.FILES.get('imagen')

        usuario.save()
        messages.success(request, '¡Tu perfil ha sido actualizado correctamente!')
        return redirect('perfil')

    return render(request, 'usuarios/perfil.html', {'usuario': usuario})