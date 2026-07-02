# core/context_processors.py
from .constants import LISTA_PROGRAMAS


def programas_context(request):
    context = {
        'PROGRAMAS_GLOBALES': LISTA_PROGRAMAS
    }
    if request.user and request.user.is_authenticated:
        from usuarios.models import Sugerencia
        from inventario.models import Prestamo
        from django.utils import timezone
        
        context['sugerencias_usuario'] = Sugerencia.objects.filter(
            usuario=request.user
        ).order_by('-fecha')
        
        # Generar notificaciones dinámicas de préstamos activos
        notifs = []
        prestamos_activos = Prestamo.objects.filter(usuario=request.user, estado_prestamo='Activo')
        for p in prestamos_activos:
            if p.elemento:
                notifs.append({
                    'tipo': 'warning',
                    'icono': 'fa-hourglass-half',
                    'titulo': f'Préstamo de {p.elemento.tipo_maquina} activo',
                    'mensaje': f'Recuerda devolverlo a tiempo para evitar sanciones. Préstamo iniciado el {p.fecha_prestamo.strftime("%d/%m/%Y")}.',
                    'badge': 'Plazo Activo'
                })
        
        # Si no hay alertas de préstamos, añadir notificación de bienvenida y buen estado
        if not notifs:
            notifs.append({
                'tipo': 'info',
                'icono': 'fa-info-circle',
                'titulo': '¡Todo al día!',
                'mensaje': 'No tienes implementos deportivos pendientes por devolver. ¡Buen trabajo!',
                'badge': 'Al día'
            })
            
        context['notificaciones_sistema'] = notifs
        context['notificaciones_count'] = len(prestamos_activos)
    return context
