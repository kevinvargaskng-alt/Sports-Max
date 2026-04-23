from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from .models import Usuario, Sugerencia
from inventario.models import Prestamo 

def login_view(request):
    if request.method == 'POST':
        doc = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=doc, password=password)
        if user:
            login(request, user)
            return JsonResponse({'status': 'success', 'success': True, 'redirect': '/perfil/'})
        return JsonResponse({'status': 'error', 'message': 'Credenciales incorrectas'}, status=401)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def registro_view(request):
    if request.method == 'POST':
        # Captura de datos
        num_doc = request.POST.get('numero_documento')
        email = request.POST.get('email')
        
        if Usuario.objects.filter(numero_documento=num_doc).exists():
            return JsonResponse({'status': 'error', 'message': 'El documento ya existe'}, status=400)

        try:
            user = Usuario(
                username=num_doc,
                email=email,
                first_name=request.POST.get('nombres'),
                last_name=request.POST.get('apellidos'),
                numero_documento=num_doc,
                tipo_documento=request.POST.get('tipo_documento'),
                telefono=request.POST.get('telefono'),
                ficha=request.POST.get('ficha'),
                programa_formacion=request.POST.get('programa_formacion'),
            )
            user.set_password(request.POST.get('contrasena'))
            user.save()
            login(request, user)
            return JsonResponse({'status': 'success', 'redirect': '/perfil/'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='home')
def perfil_view(request):
    usuario = request.user
    if request.method == 'POST':
        usuario.email = request.POST.get('email', usuario.email)
        usuario.telefono = request.POST.get('celular', usuario.telefono)
        if 'imagen' in request.FILES: usuario.foto_perfil = request.FILES.get('imagen')
        usuario.save()
        messages.success(request, '¡Perfil actualizado!')
        return redirect('perfil')

    prestamos = Prestamo.objects.filter(usuario=usuario).order_by('-fecha_prestamo')
    sugerencias_usuario = Sugerencia.objects.filter(usuario=usuario).order_by('-fecha')

    contexto = {
        'usuario': usuario,
        'prestamos': prestamos,
        'sugerencias_usuario': sugerencias_usuario,
    }
    return render(request, 'usuarios/perfil.html', contexto)

@login_required
def enviar_sugerencia(request):
    if request.method == 'POST':
        Sugerencia.objects.create(
            usuario=request.user,
            tipo=request.POST.get('tipo', 'otro'),
            comentario=request.POST.get('comentario', ''),
            anonimo=request.POST.get('anonimo') == '1'
        )
        messages.success(request, '¡Sugerencia enviada!')
    return redirect('perfil')