from django.shortcuts import render


def inicio(request):
    """Renderiza la página principal (Hero Section)"""
    context = {
        # Usamos el sistema nativo de Django para saber si está logueado
        'aprendiz_logueado': request.user.is_authenticated,
        'nombre_usuario': request.user.get_full_name() if request.user.is_authenticated else ''
    }
    return render(request, 'inicio.html', context)
