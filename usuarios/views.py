from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from .models import Usuario 

# --- IMPORTACIÓN DESDE TU APP DE INVENTARIO ---
# Asegúrate de que 'inventario' sea el nombre exacto de la carpeta de esa app
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
            user = Usuario.objects.create_user(
                username=numero_documento, email=correo, password=contrasena,
                first_name=nombres, last_name=apellidos
            )
            user.numero_documento = numero_documento
            user.tipo_documento   = tipo_doc
            user.telefono         = telefono
            user.ficha            = ficha
            user.programa_formacion = programa
            user.rol              = 'aprendiz'
            user.save()

            login(request, user)
            return JsonResponse({'status': 'success', 'redirect': '/perfil/', 'message': 'Registro exitoso'})
        
        except IntegrityError:
            return JsonResponse({'status': 'error', 'message': 'Error de base de datos'}, status=400)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='home')
def perfil_view(request):
    """Muestra el perfil con los préstamos del usuario logueado"""
    usuario = request.user

    # GESTIÓN DE EDICIÓN DE PERFIL (POST)
    if request.method == 'POST':
        email = request.POST.get('email')
        celular = request.POST.get('celular') 

        if email: usuario.email = email
        if celular: usuario.telefono = celular 
        if 'imagen' in request.FILES: usuario.foto_perfil = request.FILES.get('imagen')

        usuario.save()
        messages.success(request, '¡Perfil actualizado!')
        return redirect('perfil')

    # --- CARGA DE DATOS PARA LAS TABLAS DEL PERFIL ---
    # Traemos solo los préstamos que le pertenecen a este usuario
    prestamos = Prestamo.objects.filter(usuario=usuario).order_by('-fecha_prestamo')
    
    # Aquí puedes agregar más filtros si tienes modelos de Gimnasio o Interfichas:
    # reservas_gimnasio = ReservaGimnasio.objects.filter(aprendiz=usuario)

    contexto = {
        'usuario': usuario,
        'prestamos': prestamos,
        # 'reservas_gimnasio': reservas_gimnasio,
    }

    return render(request, 'usuarios/perfil.html', contexto)