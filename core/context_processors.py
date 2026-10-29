# core/context_processors.py
from .constants import LISTA_PROGRAMAS


def _resolver_posicion_actual(request):
    """Determina el módulo padre y la posición actual del usuario para la barra superior (Criterio 18)."""
    path = getattr(request, 'path', '/') or '/'
    match = getattr(request, 'resolver_match', None)
    url_name = getattr(match, 'url_name', '') if match else ''
    namespace = getattr(match, 'namespace', '') if match else ''

    # Mapa detallado de vistas específicas (nombre de URL -> (Módulo, URL Módulo, Posición Actual, Icono))
    mapa_urls = {
        'home': (None, None, 'Inicio', 'fa-home'),
        'ayuda': ('Soporte', None, 'Centro de Ayuda y Manual de Usuario', 'fa-question-circle'),
        'manual_usuario': ('Soporte', None, 'Manual de Usuario', 'fa-book-open'),
        'politica_privacidad': ('Legal', None, 'Política de Privacidad', 'fa-user-shield'),
        'terminos_condiciones': ('Legal', None, 'Términos y Condiciones', 'fa-file-contract'),
        'politica_cookies': ('Legal', None, 'Política de Cookies', 'fa-cookie-bite'),
        # Usuarios
        'perfil': ('Mi Cuenta', '/perfil/', 'Mi Perfil', 'fa-id-badge'),
        'gestionar_usuarios': ('Administración', '/perfil/', 'Gestión de Usuarios y Copias de Seguridad', 'fa-users-cog'),
        'password_reset': ('Seguridad', '/', 'Recuperar Contraseña', 'fa-key'),
        'password_reset_done': ('Seguridad', '/', 'Correo de Recuperación Enviado', 'fa-envelope-open-text'),
        'password_reset_confirm': ('Seguridad', '/', 'Nueva Contraseña', 'fa-lock'),
        'password_reset_complete': ('Seguridad', '/', 'Contraseña Restablecida', 'fa-check-circle'),
        # Inter-Fichas
        'interfichas': (None, None, 'Torneos Inter-Fichas', 'fa-trophy'),
        'gestionar_torneo': ('Inter-Fichas', '/interfichas/', 'Gestión de Torneo', 'fa-sitemap'),
        'reporte_torneo': ('Inter-Fichas', '/interfichas/', 'Reporte Oficial del Torneo', 'fa-file-invoice'),
        'editar_equipo': ('Inter-Fichas', '/interfichas/', 'Editar Equipo', 'fa-users'),
        # Gimnasio
        'gimnasio': (None, None, 'Gimnasio SENA', 'fa-dumbbell'),
        'machine_list': ('Gimnasio', '/gimnasio/', 'Inventario de Máquinas', 'fa-cogs'),
        'admin_lista_anamnesis': ('Gimnasio', '/gimnasio/', 'Fichas de Valoración y Salud', 'fa-notes-medical'),
        'admin_franjas': ('Gimnasio', '/gimnasio/', 'Gestión de Franjas Horarias', 'fa-clock'),
        'admin_franjas_directo': ('Gimnasio', '/gimnasio/', 'Gestión de Franjas Horarias', 'fa-clock'),
        'reporte_gimnasio': ('Gimnasio', '/gimnasio/', 'Reporte de Ingresos y Picos Horarios', 'fa-chart-bar'),
        # Inventario
        'inventario': (None, None, 'Inventario y Préstamos Deportivos', 'fa-box'),
        'devoluciones': ('Inventario', '/inventario/', 'Control de Devoluciones', 'fa-undo-alt'),
        'sanciones': ('Inventario', '/inventario/', 'Sanciones Deportivas', 'fa-gavel'),
        'reporte_morosos': ('Inventario', '/inventario/', 'Reporte de Préstamos Vencidos', 'fa-exclamation-triangle'),
        'reporte_inventario': ('Inventario', '/inventario/', 'Reporte de Préstamos e Inventario', 'fa-file-export'),
    }

    # Sub-rutas del namespace 'habitos'
    mapa_habitos = {
        'inicio': (None, None, 'Hábitos Saludables', 'fa-heartbeat'),
        'dashboard': ('Hábitos Saludables', '/habitos/', 'Panel de Bienestar', 'fa-chart-pie'),
        'habeas_data': ('Hábitos Saludables', '/habitos/', 'Consentimiento Habeas Data', 'fa-shield-alt'),
        'lista_habitos': ('Hábitos Saludables', '/habitos/', 'Guías de Hábitos Saludables', 'fa-apple-alt'),
        'detalle_habito': ('Hábitos Saludables', '/habitos/habitos/', 'Detalle de Hábito', 'fa-book-reader'),
        'lista_rutinas': ('Hábitos Saludables', '/habitos/', 'Rutinas de Entrenamiento', 'fa-running'),
        'detalle_rutina': ('Hábitos Saludables', '/habitos/rutinas/', 'Detalle de Rutina', 'fa-dumbbell'),
        'mis_rutinas': ('Hábitos Saludables', '/habitos/', 'Mis Rutinas y Seguimiento', 'fa-calendar-check'),
        'nutricion': ('Hábitos Saludables', '/habitos/', 'Pirámide Nutricional', 'fa-carrot'),
        'biblioteca': ('Hábitos Saludables', '/habitos/', 'Biblioteca de Materiales', 'fa-book'),
        'registrar_seguimiento': ('Hábitos Saludables', '/habitos/', 'Registrar Seguimiento de Salud', 'fa-weight'),
        'historial_salud': ('Hábitos Saludables', '/habitos/', 'Historial de Salud', 'fa-notes-medical'),
        'detalle_seguimiento': ('Hábitos Saludables', '/habitos/salud/historial/', 'Detalle de Seguimiento', 'fa-file-medical-alt'),
        'calcular_imc': ('Hábitos Saludables', '/habitos/', 'Calculadora de IMC y Calorías', 'fa-calculator'),
        'lista_recetas': ('Hábitos Saludables', '/habitos/', 'Recetas Saludables', 'fa-utensils'),
        'crear_receta': ('Hábitos Saludables', '/habitos/recetas/', 'Nueva Receta Saludable', 'fa-plus-circle'),
        'detalle_receta': ('Hábitos Saludables', '/habitos/recetas/', 'Detalle de Receta', 'fa-utensils'),
        'editar_receta': ('Hábitos Saludables', '/habitos/recetas/', 'Editar Receta', 'fa-edit'),
        'grafica_sueno': ('Hábitos Saludables', '/habitos/', 'Monitoreo de Sueño Semanal', 'fa-bed'),
        'configurar_notificaciones': ('Hábitos Saludables', '/habitos/', 'Recordatorios y Notificaciones', 'fa-bell'),
        'dashboard_progreso': ('Hábitos Saludables', '/habitos/', 'Mi Progreso Físico', 'fa-chart-line'),
        'reporte_habitos': ('Hábitos Saludables', '/habitos/', 'Reporte de Hábitos Saludables', 'fa-chart-bar'),
    }

    if namespace == 'habitos' and url_name in mapa_habitos:
        modulo, modulo_url, actual, icono = mapa_habitos[url_name]
    elif url_name in mapa_urls:
        modulo, modulo_url, actual, icono = mapa_urls[url_name]
    elif path.startswith('/interfichas/'):
        modulo, modulo_url, actual, icono = ('Inter-Fichas', '/interfichas/', 'Gestión de Torneos', 'fa-trophy')
    elif path.startswith('/gimnasio/'):
        modulo, modulo_url, actual, icono = ('Gimnasio', '/gimnasio/', 'Panel de Gimnasio', 'fa-dumbbell')
    elif path.startswith('/inventario/'):
        modulo, modulo_url, actual, icono = ('Inventario', '/inventario/', 'Gestión de Inventario', 'fa-box')
    elif path.startswith('/habitos/'):
        modulo, modulo_url, actual, icono = ('Hábitos Saludables', '/habitos/', 'Bienestar y Salud', 'fa-heartbeat')
    else:
        modulo, modulo_url, actual, icono = (None, None, 'Inicio', 'fa-home')

    return {
        'app_nombre': 'Sports-Max',
        'modulo': modulo,
        'modulo_url': modulo_url,
        'pagina_actual': actual,
        'icono_actual': icono,
    }


def programas_context(request):
    context = {
        'PROGRAMAS_GLOBALES': LISTA_PROGRAMAS,
        'nav_posicion': _resolver_posicion_actual(request),
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
        try:
            prestamos_activos = Prestamo.objects.filter(usuario=request.user, estado_prestamo='Activo')
            ahora_date = timezone.localdate()
            prestamos_marcados_hoy = (request.session.get('notifs_prestamos_leidas_date') == str(ahora_date))
            
            for p in prestamos_activos:
                if p.elemento:
                    limite = p.fecha_prestamo + timedelta(days=p.dias_prestamo)
                    es_vencido = ahora_date > limite
                    
                    if es_vencido:
                        if not prestamos_marcados_hoy:
                            unread_count += 1
                        tipo = 'danger'
                        icono = 'fa-exclamation-triangle'
                        badge = 'Vencido' if not prestamos_marcados_hoy else 'Vencido (Leído)'
                        mensaje = f'¡ATENCIÓN! Has superado la fecha límite de devolución ({limite.strftime("%d/%m/%Y")}). Devuélvelo hoy mismo.'
                    else:
                        tipo = 'warning'
                        icono = 'fa-hourglass-half'
                        badge = 'Plazo Activo' if not prestamos_marcados_hoy else 'Plazo Activo (Leído)'
                        mensaje = f'Recuerda devolverlo a tiempo. Fecha límite: {limite.strftime("%d/%m/%Y")}.'
                    
                    notifs.append({
                        'tipo': tipo,
                        'icono': icono,
                        'titulo': f'Préstamo de {p.elemento.tipo_maquina} activo',
                        'mensaje': mensaje,
                        'badge': badge,
                        'leida': prestamos_marcados_hoy
                    })
        except Exception:
            pass
        
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
