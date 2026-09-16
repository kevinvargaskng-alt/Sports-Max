# core/context_processors.py
from .constants import LISTA_PROGRAMAS


def programas_context(request):
    context = {
        'PROGRAMAS_GLOBALES': LISTA_PROGRAMAS
    }
    if request.user and request.user.is_authenticated:
        from usuarios.models import Sugerencia, Notificacion
        from inventario.models import Prestamo
        from django.utils import timezone
        from datetime import timedelta
        
        context['sugerencias_usuario'] = Sugerencia.objects.filter(
            usuario=request.user
        ).order_by('-fecha')
        
        notifs = []
        unread_count = 0

        # 1. Notificaciones persistentes en base de datos (ej. devoluciones para admin, avisos del sistema)
        try:
            notificaciones_bd = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:20]
            unread_count += Notificacion.objects.filter(usuario=request.user, leida=False).count()
            for n in notificaciones_bd:
                badge_text = 'Nueva' if not n.leida else 'Leída'
                notifs.append({
                    'id': n.id,
                    'tipo': n.tipo,
                    'icono': n.icono or 'fa-bell',
                    'titulo': n.titulo,
                    'mensaje': n.mensaje,
                    'badge': badge_text,
                    'leida': n.leida,
                    'enlace': n.enlace,
                    'fecha': timezone.localtime(n.fecha_creacion).strftime('%d/%m/%Y %H:%M')
                })
        except Exception:
            pass

        # 2. Notificaciones dinámicas de préstamos activos (plazos y vencimientos)
        prestamos_activos = Prestamo.objects.filter(usuario=request.user, estado_prestamo='Activo')
        ahora_date = timezone.localdate()
        
        for p in prestamos_activos:
            if p.elemento:
                limite = p.fecha_prestamo + timedelta(days=p.dias_prestamo)
                es_vencido = ahora_date > limite
                
                if es_vencido:
                    unread_count += 1
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
                    'badge': badge,
                    'leida': False
                })
        
        if not notifs:
            notifs.append({
                'tipo': 'info',
                'icono': 'fa-info-circle',
                'titulo': '¡Todo al día!',
                'mensaje': 'No tienes notificaciones pendientes ni implementos por devolver.',
                'badge': 'Al día',
                'leida': True
            })
            
        context['notificaciones_sistema'] = notifs
        context['notificaciones_count'] = unread_count
    return context
