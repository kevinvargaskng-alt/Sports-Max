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
        from datetime import timedelta
        
        context['sugerencias_usuario'] = Sugerencia.objects.filter(
            usuario=request.user
        ).order_by('-fecha')
        
        # Generar notificaciones dinámicas de préstamos activos
        notifs = []
        prestamos_activos = Prestamo.objects.filter(usuario=request.user, estado_prestamo='Activo')
        overdue_count = 0
        ahora_date = timezone.localdate()
        
        for p in prestamos_activos:
            if p.elemento:
                limite = p.fecha_prestamo + timedelta(days=p.dias_prestamo)
                es_vencido = ahora_date > limite
                
                if es_vencido:
                    overdue_count += 1
                    tipo = 'danger'
                    icono = 'fa-exclamation-triangle'
                    badge = 'Vencido'
                    mensaje = f'¡ATENCIÓN! Has superado la fecha límite de devolución ({limite.strftime("%d/%m/%Y")}). Devuélvelo hoy mismo.'
                else:
                    tipo = 'warning'
                    icono = 'fa-hourglass-half'
                    badge = 'Plazo Activo'
                    mensaje = f'Recuerda devolverlo a tiempo. Fecha límite: {limite.strftime("%d/%m/%Y")}.'
                
                notifs.append({
                    'tipo': tipo,
                    'icono': icono,
                    'titulo': f'Préstamo de {p.elemento.tipo_maquina} activo',
                    'mensaje': mensaje,
                    'badge': badge
                })
        
        if not notifs:
            notifs.append({
                'tipo': 'info',
                'icono': 'fa-info-circle',
                'titulo': '¡Todo al día!',
                'mensaje': 'No tienes implementos deportivos pendientes por devolver. ¡Buen trabajo!',
                'badge': 'Al día'
            })
            
        context['notificaciones_sistema'] = notifs
        context['notificaciones_count'] = overdue_count
    return context
