from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion
from datetime import datetime, date, timedelta
from usuarios.models import Usuario, Notificacion
from django.core.exceptions import ValidationError
from core.security.file_upload import validate_uploaded_file


# ─────────────────────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────────────────────

@login_required
def inventario_list(request):
    if request.user.is_staff:
        elementos = ElementoDeportivo.objects.all().order_by('tipo_maquina')
    else:
        elementos = ElementoDeportivo.objects.filter(habilitado=True).order_by('tipo_maquina')

    usuarios_staff = Usuario.objects.filter(
        is_staff=True, is_active=True).order_by('first_name')

    # Admin ve todos los préstamos; usuario solo los suyos
    if request.user.is_staff:
        prestamos = Prestamo.objects.all().order_by('-fecha_prestamo')
    else:
        prestamos = Prestamo.objects.filter(
            usuario=request.user).order_by('-fecha_prestamo')

    # Sanciones activas del usuario actual (para el aviso en modal de préstamo)
    sanciones = Sancion.objects.filter(
        usuario=request.user, estado_sancion='Activa')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # ─── 1. CREAR ELEMENTO — solo admin ───────────────────────
        if accion == 'crear_elemento':
            if not request.user.is_staff:
                messages.error(
                    request, "No tienes permisos para crear elementos.")
                return redirect('inventario')

            # Obtener el ID del responsable desde el POST
            responsable_id = request.POST.get('usuario_responsable')
            responsable = Usuario.objects.get(
                id=responsable_id) if responsable_id else None

            imagen_file = request.FILES.get('imagen')
            if imagen_file:
                try:
                    imagen_file = validate_uploaded_file(imagen_file, allowed_types='image')
                except ValidationError as e:
                    messages.error(request, f"Error en la imagen: {e.message}")
                    return redirect('inventario')

            ElementoDeportivo.objects.create(
                tipo_maquina=request.POST.get('nombre_elemento'),
                cantidad_total=request.POST.get('cantidad_total'),
                estado_general='Bueno',
                fecha_adquisicion=request.POST.get(
                    'fecha_adquisicion') or None,
                descripcion=request.POST.get('descripcion', ''),
                imagen=imagen_file,
                usuario_responsable=responsable,
                habilitado=request.POST.get('habilitado') == 'on' if 'habilitado' in request.POST else True,
            )
            messages.success(request, "Elemento creado exitosamente.")
            return redirect('inventario')

        # ─── 2. EDITAR ELEMENTO — solo admin ──────────────────────
        elif accion == 'editar_elemento':
            if not request.user.is_staff:
                messages.error(
                    request, "No tienes permisos para editar elementos.")
                return redirect('inventario')

            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, id=codigo)

                # Obtener el ID del responsable desde el POST
                responsable_id = request.POST.get('usuario_responsable')
                if responsable_id:
                    elemento.usuario_responsable = Usuario.objects.get(
                        id=responsable_id)
                else:
                    elemento.usuario_responsable = None

                elemento.tipo_maquina = request.POST.get('nombre_elemento')
                elemento.cantidad_total = request.POST.get('cantidad_total')
                elemento.estado_general = request.POST.get('estado_general') or elemento.estado_general or 'Buen estado'
                elemento.fecha_adquisicion = request.POST.get(
                    'fecha_adquisicion') or None
                elemento.descripcion = request.POST.get('descripcion', '')
                elemento.habilitado = request.POST.get('habilitado') == 'on'
                if 'imagen' in request.FILES:
                    try:
                        elemento.imagen = validate_uploaded_file(request.FILES['imagen'], allowed_types='image')
                    except ValidationError as e:
                        messages.error(request, f"Error en la imagen: {e.message}")
                        return redirect('inventario')
                elemento.save()
                messages.success(
                    request, "Elemento actualizado correctamente.")
            return redirect('inventario')

        # ─── 2B. TOGGLE HABILITADO ELEMENTO — solo admin ──────────
        elif accion == 'toggle_habilitado':
            if not request.user.is_staff:
                messages.error(request, "No tienes permisos.")
                return redirect('inventario')

            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, id=codigo)
                elemento.habilitado = not elemento.habilitado
                elemento.save()
                estado_str = "habilitado" if elemento.habilitado else "inhabilitado"
                messages.info(request, f"El producto {elemento.tipo_maquina} ha sido {estado_str}.")
            return redirect('inventario')

        # ─── 3. CREAR PRÉSTAMO — solo usuarios normales ───────────
        elif accion == 'crear_prestamo':
            if request.user.is_staff:
                messages.error(
                    request, "Los administradores no realizan préstamos.")
                return redirect('inventario')

            # Bloquear si tiene sanciones activas
            if sanciones.exists():
                messages.error(
                    request,
                    "No puedes solicitar un préstamo mientras tengas sanciones activas."
                )
                return redirect('inventario')

            id_elemento = request.POST.get('elemento')
            cantidad = int(request.POST.get('cantidad_prestada', 0))
            dias = int(request.POST.get('dias_prestamo', 1))

            elemento = get_object_or_404(ElementoDeportivo, id=id_elemento)

            # Validar stock disponible
            if cantidad <= 0:
                messages.error(request, "La cantidad debe ser mayor a 0.")
                return redirect('inventario')

            if cantidad > elemento.cantidad_total:
                messages.error(
                    request,
                    f"Stock insuficiente. Disponible: {elemento.cantidad_total}"
                )
                return redirect('inventario')

            # Validar días
            if dias < 1 or dias > 15:
                messages.error(
                    request, "Los días de préstamo deben estar entre 1 y 15.")
                return redirect('inventario')

            fecha_devolucion = date.today() + timedelta(days=dias)

            Prestamo.objects.create(
                usuario=request.user,
                elemento=elemento,
                cantidad_prestada=cantidad,
                dias_prestamo=dias,
                fecha_devolucion=fecha_devolucion,
                observacion_prestamo=request.POST.get('observacion', ''),
                estado_prestamo='Activo',
            )

            # Descontar del inventario
            elemento.cantidad_total -= cantidad
            elemento.save()

            messages.success(
                request,
                f"Préstamo registrado. Devolución antes del {fecha_devolucion.strftime('%d/%m/%Y')}."
            )
            return redirect('inventario')

    context = {
        'elementos': elementos,
        'prestamos': prestamos,
        'sanciones': sanciones,
        'usuarios_staff': usuarios_staff,
    }
    return render(request, 'inventario/inventario.html', context)


# ─────────────────────────────────────────────────────────────
# DEVOLUCIONES
# ─────────────────────────────────────────────────────────────

@login_required
def devoluciones_list(request):
    """
    Admin: ve y gestiona devoluciones de TODOS los usuarios.
    Usuario: ve y gestiona solo sus propios préstamos activos.
    """
    if request.user.is_staff:
        prestamos_activos = Prestamo.objects.filter(
            estado_prestamo='Activo'
        ).select_related('usuario', 'elemento').order_by('-fecha_prestamo')

        devoluciones = Devolucion.objects.all(
        ).select_related('prestamo__usuario', 'prestamo__elemento').order_by('-fecha_devolucion')
    else:
        prestamos_activos = Prestamo.objects.filter(
            usuario=request.user,
            estado_prestamo='Activo'
        ).order_by('-fecha_prestamo')

        devoluciones = Devolucion.objects.filter(
            prestamo__usuario=request.user
        ).order_by('-fecha_devolucion')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'registrar_devolucion':
            codigo_prestamo = request.POST.get('prestamo')
            cantidad_devuelta = int(request.POST.get('cantidad_devuelta', 1))
            tiene_novedad = request.POST.get('tiene_novedad') == 'on'
            estado_elemento = request.POST.get('estado_elemento_devolucion')
            tipo_novedad = request.POST.get('tipo_novedad_devolucion', '')
            observaciones = request.POST.get('observaciones_devolucion', '')

            # Admin puede devolver cualquier préstamo activo;
            # usuario solo los suyos
            if request.user.is_staff:
                prestamo = get_object_or_404(
                    Prestamo, codigo_prestamo=codigo_prestamo, estado_prestamo='Activo'
                )
            else:
                prestamo = get_object_or_404(
                    Prestamo,
                    codigo_prestamo=codigo_prestamo,
                    usuario=request.user,
                    estado_prestamo='Activo'
                )

            # Validar cantidad
            if cantidad_devuelta > prestamo.cantidad_prestada:
                messages.error(
                    request,
                    f"La cantidad a devolver no puede superar la prestada "
                    f"({prestamo.cantidad_prestada})."
                )
                return redirect('devoluciones')

            # Registrar devolución
            devolucion_creada = Devolucion.objects.create(
                prestamo=prestamo,
                cantidad_devuelta=cantidad_devuelta,
                fecha_devolucion=date.today(),
                hora_devolucion=datetime.now().time(),
                tiene_novedad=tiene_novedad,
                estado_elemento_devolucion=estado_elemento,
                tipo_novedad_devolucion=tipo_novedad,
                observaciones_devolucion=observaciones,
            )

            # Restaurar stock
            elemento = prestamo.elemento
            elemento.cantidad_total += cantidad_devuelta
            elemento.save()

            # ── Notificación automática a Administradores (BD y campana) ──
            admins_activos = Usuario.objects.filter(is_staff=True, is_active=True)
            novedad_txt = f" (Novedad: {tipo_novedad} - {observaciones})" if tiene_novedad and tipo_novedad else ""
            notif_tipo = 'warning' if tiene_novedad else 'info'
            notif_icono = 'fa-exclamation-triangle' if tiene_novedad else 'fa-undo'
            notif_titulo = f"Devolución: {elemento.tipo_maquina}"
            notif_mensaje = (
                f"El usuario {prestamo.usuario.get_full_name()} ({prestamo.usuario.numero_documento}) "
                f"ha registrado la devolución de {cantidad_devuelta} unidad(es) de '{elemento.tipo_maquina}'. "
                f"Estado: {estado_elemento or 'Bueno'}.{novedad_txt}"
            )
            for admin_user in admins_activos:
                Notificacion.objects.create(
                    usuario=admin_user,
                    titulo=notif_titulo,
                    mensaje=notif_mensaje,
                    tipo=notif_tipo,
                    icono=notif_icono,
                    enlace='/inventario/devoluciones/'
                )

            # Sanción automática por daño o pérdida
            if tiene_novedad and tipo_novedad in ['Daño', 'Pérdida']:
                Sancion.objects.create(
                    usuario=prestamo.usuario,
                    tipo_sancion=f"{tipo_novedad} de {elemento.tipo_maquina}",
                    fecha_inicio_sancion=date.today(),
                    fecha_fin_sancion=date.today() + timedelta(days=30),
                    estado_sancion='Activa',
                    descripcion_sancion=(
                        f"Sanción automática por {tipo_novedad.lower()} del elemento "
                        f"'{elemento.tipo_maquina}'. Préstamo #{prestamo.codigo_prestamo}. "
                        f"Observación: {observaciones}"
                    ),
                )
                messages.warning(
                    request,
                    f"Se generó una sanción automática de 30 días por {tipo_novedad.lower()} del elemento."
                )

            # Marcar préstamo como devuelto
            prestamo.estado_prestamo = 'Devuelto'
            prestamo.save()

            messages.success(request, "Devolución registrada correctamente.")
            return redirect('devoluciones')

    context = {
        'prestamos_activos': prestamos_activos,
        'devoluciones':      devoluciones,
    }
    return render(request, 'inventario/devoluciones.html', context)


# ─────────────────────────────────────────────────────────────
# SANCIONES
# ─────────────────────────────────────────────────────────────

@login_required
def sanciones_list(request):
    """
    Admin: ve todas las sanciones, puede crear y cerrar.
    Usuario: ve solo sus sanciones, sin acciones.
    """
    if request.user.is_staff:
        sanciones = Sancion.objects.all().select_related(
            'usuario').order_by('-fecha_inicio_sancion')
    else:
        sanciones = Sancion.objects.filter(
            usuario=request.user
        ).order_by('-fecha_inicio_sancion')

    usuarios = Usuario.objects.filter(is_active=True).order_by('first_name')

    if request.method == 'POST':
        if not request.user.is_staff:
            messages.error(request, "No tienes permisos para esta acción.")
            return redirect('sanciones')

        accion = request.POST.get('accion')

        if accion == 'crear_sancion':
            from datetime import datetime as dt_class
            from django.utils import timezone as django_timezone
            
            inicio_str = request.POST.get('fecha_inicio_sancion')
            fin_str = request.POST.get('fecha_fin_sancion')
            
            try:
                inicio_val = dt_class.strptime(inicio_str, '%Y-%m-%d').date()
                fin_val = dt_class.strptime(fin_str, '%Y-%m-%d').date()
                
                if inicio_val < django_timezone.localdate():
                    messages.error(request, "La fecha de inicio de la sanción no puede ser de días anteriores.")
                    return redirect('sanciones')
                
                if fin_val < inicio_val:
                    messages.error(request, "La fecha de fin de la sanción debe ser posterior a la fecha de inicio.")
                    return redirect('sanciones')
            except Exception:
                messages.error(request, "Formato de fechas inválido.")
                return redirect('sanciones')

            Sancion.objects.create(
                usuario_id=request.POST.get('usuario_id'),
                tipo_sancion=request.POST.get('tipo_sancion'),
                fecha_inicio_sancion=inicio_val,
                fecha_fin_sancion=fin_val,
                estado_sancion='Activa',
                descripcion_sancion=request.POST.get(
                    'descripcion_sancion', ''),
            )
            messages.success(request, "Sanción creada correctamente.")
            return redirect('sanciones')

        elif accion == 'cerrar_sancion':
            codigo = request.POST.get('codigo_sancion')
            sancion = get_object_or_404(Sancion, codigo_sancion=codigo)
            sancion.estado_sancion = 'Cerrada'
            sancion.save()
            messages.success(request, "Sanción cerrada correctamente.")
            return redirect('sanciones')

    context = {
        'sanciones': sanciones,
        'usuarios':  usuarios,
    }
    return render(request, 'inventario/sanciones.html', context)


# ─────────────────────────────────────────────────────────────
# OPERACIONES CRUD adicionales
# ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def eliminar_elemento(request, id):
    """Solo admin puede eliminar elementos."""
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para eliminar elementos.")
        return redirect('inventario')
    elemento = get_object_or_404(ElementoDeportivo, id=id)
    elemento.delete()
    messages.warning(request, "Elemento eliminado del inventario.")
    return redirect('inventario')


@login_required
def editar_elemento(request, id):
    """Solo admin puede editar elementos (vista separada para compatibilidad)."""
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para editar elementos.")
        return redirect('inventario')
    elemento = get_object_or_404(ElementoDeportivo, id=id)
    if request.method == 'POST':
        if 'imagen' in request.FILES:
            try:
                elemento.imagen = validate_uploaded_file(request.FILES['imagen'], allowed_types='image')
            except ValidationError as e:
                messages.error(request, f"Error en la imagen: {e.message}")
                return redirect('inventario')
        elemento.tipo_maquina = request.POST.get('tipo_maquina')
        elemento.cantidad_total = request.POST.get('cantidad_total')
        elemento.estado_general = request.POST.get('estado_general')

        responsable_id = request.POST.get('usuario_responsable')
        if responsable_id:
            elemento.usuario_responsable = Usuario.objects.get(
                id=responsable_id)
        else:
            elemento.usuario_responsable = None

        elemento.save()
        messages.success(request, "Elemento actualizado correctamente.")
        return redirect('inventario')
    context = {'elemento': elemento}
    return render(request, 'inventario/editar.html', context)


@login_required
@require_POST
def eliminar_prestamo(request, id):
    """
    Admin puede eliminar cualquier préstamo.
    Usuario solo puede cancelar los suyos (si aún están activos).
    """
    if request.user.is_staff:
        prestamo = get_object_or_404(Prestamo, codigo_prestamo=id)
    else:
        prestamo = get_object_or_404(
            Prestamo, codigo_prestamo=id, usuario=request.user)

    # Restaurar stock si el préstamo estaba activo
    if prestamo.estado_prestamo == 'Activo':
        elemento = prestamo.elemento
        elemento.cantidad_total += prestamo.cantidad_prestada
        elemento.save()

    prestamo.delete()
    messages.info(request, "Préstamo eliminado y stock restaurado.")
    return redirect('inventario')


# ══════════════════════════════════════════════════════════════════════
# CP-21: REPORTE DE PRÉSTAMOS VENCIDOS Y EJECUCIÓN DE BLOQUEOS A MOROSOS
# ══════════════════════════════════════════════════════════════════════
@login_required
def reporte_prestamos_vencidos(request):
    """
    CP-21: Como Administrador, consultar un reporte cruzando las tablas
    Prestamos y Usuarios para detectar morosos con préstamos vencidos.
    """
    if not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'status': 'error', 'message': 'Acceso denegado. Se requieren permisos de administrador.'}, status=403)
        messages.error(request, "Acceso denegado. Se requieren permisos de administrador.")
        return redirect('inventario')

    hoy = timezone.localdate()
    # Cruce relacional explícito entre Prestamo y Usuario
    prestamos_vencidos = Prestamo.objects.filter(
        estado_prestamo='Activo',
        fecha_devolucion__lt=hoy
    ).select_related('usuario', 'elemento').order_by('fecha_devolucion')

    morosos_data = []
    for p in prestamos_vencidos:
        u = p.usuario
        dias_mora = (hoy - p.fecha_devolucion).days if p.fecha_devolucion else 0
        morosos_data.append({
            'prestamo_id': p.codigo_prestamo,
            'usuario_id': u.id,
            'nombre_completo': u.get_full_name() or u.username,
            'documento': u.numero_documento,
            'email': u.email,
            'rol': getattr(u, 'rol', ''),
            'estado_usuario': u.estado,
            'elemento': p.elemento.tipo_maquina if p.elemento else 'Implemento deportivo',
            'cantidad': p.cantidad_prestada,
            'fecha_prestamo': str(p.fecha_prestamo),
            'fecha_limite': str(p.fecha_devolucion),
            'dias_mora': dias_mora,
        })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'status': 'success',
            'total_morosos': len(morosos_data),
            'fecha_corte': str(hoy),
            'morosos': morosos_data
        })

    context = {
        'morosos': morosos_data,
        'total_morosos': len(morosos_data),
        'fecha_corte': hoy
    }
    return render(request, 'inventario/sanciones.html', context)


@login_required
@require_POST
def bloquear_morosos(request):
    """
    CP-21: Como Administrador, ejecutar una acción para aplicar bloqueos
    a los usuarios morosos generando sanciones y suspendiendo su acceso.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Acceso denegado.'}, status=403)

    hoy = timezone.localdate()
    usuario_especifico_id = request.POST.get('usuario_id')
    prestamo_especifico_id = request.POST.get('prestamo_id')

    qs = Prestamo.objects.filter(
        estado_prestamo='Activo',
        fecha_devolucion__lt=hoy
    ).select_related('usuario', 'elemento')

    if usuario_especifico_id:
        qs = qs.filter(usuario_id=usuario_especifico_id)
    elif prestamo_especifico_id:
        qs = qs.filter(codigo_prestamo=prestamo_especifico_id)

    bloqueados_count = 0
    for p in qs:
        u = p.usuario
        # 1. Crear sanción disciplinaria en la base de datos
        sancion_existente = Sancion.objects.filter(
            usuario=u,
            estado_sancion='Activa',
            tipo_sancion__icontains='Mora'
        ).exists()

        if not sancion_existente:
            Sancion.objects.create(
                usuario=u,
                tipo_sancion='Mora en devolución de implementos',
                fecha_inicio_sancion=hoy,
                fecha_fin_sancion=hoy + timedelta(days=15),
                estado_sancion='Activa',
                descripcion_sancion=f'Bloqueo por mora de { (hoy - p.fecha_devolucion).days } días en entrega de {p.elemento.tipo_maquina if p.elemento else "implemento"}.'
            )

        # 2. Bloquear usuario
        if u.estado != 'inactivo':
            u.estado = 'inactivo'
            u.save(update_fields=['estado'])

        # 3. Notificación al usuario
        Notificacion.objects.create(
            usuario=u,
            titulo='Cuenta bloqueada por devolución pendiente',
            mensaje='Has sido bloqueado por no entregar a tiempo los elementos deportivos solicitados. Acércate a la oficina de deportes.',
            enlace='/perfil/'
        )
        bloqueados_count += 1

    return JsonResponse({
        'status': 'success',
        'message': f'Se aplicaron bloqueos y sanciones a {bloqueados_count} moroso(s) correctamente.',
        'bloqueados_count': bloqueados_count
    })
