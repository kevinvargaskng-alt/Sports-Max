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


def _validar_fecha_adquisicion(fecha_str):
    """
    Valida que la fecha de adquisición no sea futura y que como máximo
    sea de 1 año atrás a partir de la fecha actual.
    (fecha_actual - 1 año <= fecha_adquisicion <= fecha_actual).
    Retorna (fecha_date, error_message)
    """
    if not fecha_str or not str(fecha_str).strip():
        return None, None
    try:
        from datetime import datetime as dt
        from django.utils import timezone
        fecha = dt.strptime(str(fecha_str).strip(), '%Y-%m-%d').date()
        hoy = timezone.localdate()
        un_ano_atras = hoy - timedelta(days=365)
        if fecha > hoy:
            return None, f"La fecha de adquisición ({fecha.strftime('%d/%m/%Y')}) no puede ser una fecha futura (hoy es {hoy.strftime('%d/%m/%Y')})."
        if fecha < un_ano_atras:
            return None, f"La fecha de adquisición no puede ser anterior a 1 año atrás a partir de hoy (rango permitido: {un_ano_atras.strftime('%d/%m/%Y')} a {hoy.strftime('%d/%m/%Y')})."
        return fecha, None
    except ValueError:
        return None, "Formato de fecha de adquisición inválido. Use el formato AAAA-MM-DD."


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
    # Una sanción vencida (fecha_fin en el pasado) no debe bloquear préstamos
    sanciones = Sancion.objects.filter(
        usuario=request.user,
        estado_sancion='Activa',
        fecha_fin_sancion__gte=date.today())

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json'
        accion = request.POST.get('accion')

        # ─── 1. CREAR ELEMENTO — solo admin ───────────────────────
        if accion == 'crear_elemento':
            if not request.user.is_staff:
                msg = "No tienes permisos para crear elementos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'permiso': msg}}, status=403)
                messages.error(request, msg)
                return redirect('inventario')

            nombre_elemento = request.POST.get('nombre_elemento', '').strip()
            if not nombre_elemento or len(nombre_elemento) < 2 or len(nombre_elemento) > 100:
                msg = "El nombre del elemento es obligatorio y debe tener entre 2 y 100 caracteres."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'nombre_elemento': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            cantidad_raw = request.POST.get('cantidad_total')
            try:
                cantidad_total = int(cantidad_raw)
            except (ValueError, TypeError):
                msg = "La cantidad debe ser un número entero válido."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_total': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            if cantidad_total < 1 or cantidad_total > 9999:
                msg = "La cantidad debe ser como mínimo 1 y no superar 9999 unidades."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_total': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            # Validar fecha de adquisición (fecha_actual - 1 año <= fecha_adquisicion <= fecha_actual)
            fecha_adq, error_fecha = _validar_fecha_adquisicion(request.POST.get('fecha_adquisicion'))
            if error_fecha:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': error_fecha, 'errors': {'fecha_adquisicion': error_fecha}}, status=400)
                messages.error(request, error_fecha)
                return redirect('inventario')

            # Obtener el ID del responsable desde el POST
            responsable_id = request.POST.get('usuario_responsable')
            responsable = None
            if responsable_id:
                try:
                    responsable = Usuario.objects.get(id=int(responsable_id), is_staff=True, is_active=True)
                except (Usuario.DoesNotExist, ValueError, TypeError):
                    msg = "La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'usuario_responsable': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

            descripcion_elem = request.POST.get('descripcion', '').strip()
            if len(descripcion_elem) > 500:
                msg = "La descripción del elemento no puede superar los 500 caracteres."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'descripcion': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            imagen_file = request.FILES.get('imagen')
            if imagen_file:
                try:
                    imagen_file = validate_uploaded_file(imagen_file, allowed_types='image')
                except ValidationError as e:
                    msg = f"Error en la imagen: {e.message}"
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'imagen': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

            nuevo_elem = ElementoDeportivo.objects.create(
                tipo_maquina=nombre_elemento,
                cantidad_total=cantidad_total,
                estado_general='Bueno',
                fecha_adquisicion=fecha_adq,
                descripcion=descripcion_elem,
                imagen=imagen_file,
                usuario_responsable=responsable,
                habilitado=request.POST.get('habilitado') == 'on' if 'habilitado' in request.POST else True,
            )
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Elemento creado exitosamente.',
                    'id': nuevo_elem.pk,
                    'nombre': nuevo_elem.tipo_maquina
                }, status=201)
            messages.success(request, "Elemento creado exitosamente con todas las validaciones de regla.")
            return redirect('inventario')

        # ─── 2. EDITAR ELEMENTO — solo admin ──────────────────────
        elif accion == 'editar_elemento':
            if not request.user.is_staff:
                msg = "No tienes permisos para editar elementos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'permiso': msg}}, status=403)
                messages.error(request, msg)
                return redirect('inventario')

            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, id=codigo)

                nombre_elemento = request.POST.get('nombre_elemento', '').strip()
                if not nombre_elemento or len(nombre_elemento) < 2 or len(nombre_elemento) > 100:
                    msg = "El nombre del elemento es obligatorio y debe tener entre 2 y 100 caracteres."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'nombre_elemento': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

                cantidad_raw = request.POST.get('cantidad_total')
                try:
                    cantidad_total = int(cantidad_raw)
                except (ValueError, TypeError):
                    msg = "La cantidad debe ser un número entero válido."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_total': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

                if cantidad_total < 1 or cantidad_total > 9999:
                    msg = "La cantidad debe ser como mínimo 1 y no superar 9999 unidades."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_total': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

                # Validar fecha de adquisición (fecha_actual - 1 año <= fecha_adquisicion <= fecha_actual)
                fecha_adq, error_fecha = _validar_fecha_adquisicion(request.POST.get('fecha_adquisicion'))
                if error_fecha:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': error_fecha, 'errors': {'fecha_adquisicion': error_fecha}}, status=400)
                    messages.error(request, error_fecha)
                    return redirect('inventario')

                # Obtener el ID del responsable desde el POST
                responsable_id = request.POST.get('usuario_responsable')
                if responsable_id:
                    try:
                        elemento.usuario_responsable = Usuario.objects.get(id=int(responsable_id), is_staff=True, is_active=True)
                    except (Usuario.DoesNotExist, ValueError, TypeError):
                        msg = "La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista."
                        if is_ajax:
                            return JsonResponse({'status': 'error', 'message': msg, 'errors': {'usuario_responsable': msg}}, status=400)
                        messages.error(request, msg)
                        return redirect('inventario')
                else:
                    elemento.usuario_responsable = None

                estado_input = request.POST.get('estado_general')
                if estado_input:
                    if estado_input not in ['Buen estado', 'Regular', 'Malo', 'En reparación', 'De baja', 'Bueno']:
                        msg = "La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista."
                        if is_ajax:
                            return JsonResponse({'status': 'error', 'message': msg, 'errors': {'estado_general': msg}}, status=400)
                        messages.error(request, msg)
                        return redirect('inventario')
                else:
                    elemento.estado_general = elemento.estado_general or 'Buen estado'

                descripcion_elem = request.POST.get('descripcion', '').strip()
                if len(descripcion_elem) > 500:
                    msg = "La descripción del elemento no puede superar los 500 caracteres."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': msg, 'errors': {'descripcion': msg}}, status=400)
                    messages.error(request, msg)
                    return redirect('inventario')

                elemento.fecha_adquisicion = fecha_adq
                elemento.descripcion = descripcion_elem
                elemento.habilitado = request.POST.get('habilitado') == 'on'
                if 'imagen' in request.FILES:
                    try:
                        elemento.imagen = validate_uploaded_file(request.FILES['imagen'], allowed_types='image')
                    except ValidationError as e:
                        msg = f"Error en la imagen: {e.message}"
                        if is_ajax:
                            return JsonResponse({'status': 'error', 'message': msg, 'errors': {'imagen': msg}}, status=400)
                        messages.error(request, msg)
                        return redirect('inventario')
                elemento.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': "Elemento actualizado correctamente."})
                messages.success(
                    request, "Elemento actualizado correctamente.")
            return redirect('inventario')

        # ─── 2B. TOGGLE HABILITADO ELEMENTO — solo admin ──────────
        elif accion == 'toggle_habilitado':
            if not request.user.is_staff:
                msg = "No tienes permisos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'permiso': msg}}, status=403)
                messages.error(request, msg)
                return redirect('inventario')

            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, id=codigo)
                elemento.habilitado = not elemento.habilitado
                elemento.save()
                estado_str = "habilitado" if elemento.habilitado else "inhabilitado"
                if is_ajax:
                    return JsonResponse({'status': 'success', 'habilitado': elemento.habilitado, 'message': f"El producto {elemento.tipo_maquina} ha sido {estado_str}."})
                messages.info(request, f"El producto {elemento.tipo_maquina} ha sido {estado_str}.")
            return redirect('inventario')

        # ─── 3. CREAR PRÉSTAMO — solo usuarios normales ───────────
        elif accion == 'crear_prestamo':
            if request.user.is_staff:
                msg = "Los administradores no realizan préstamos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'permiso': msg}}, status=403)
                messages.error(request, msg)
                return redirect('inventario')

            # Bloquear si tiene sanciones activas
            if sanciones.exists():
                msg = "No puedes solicitar un préstamo mientras tengas sanciones activas."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'sanciones': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            id_elemento = request.POST.get('elemento')
            cantidad_raw = request.POST.get('cantidad_prestada', 0)
            dias_raw = request.POST.get('dias_prestamo', 1)
            try:
                cantidad = int(cantidad_raw)
                dias = int(dias_raw)
            except (ValueError, TypeError):
                msg = "La cantidad y los días deben ser valores numéricos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            try:
                elemento = ElementoDeportivo.objects.get(id=int(id_elemento), habilitado=True)
            except (ElementoDeportivo.DoesNotExist, ValueError, TypeError):
                msg = "La opción seleccionada no es válida. Por favor, elija una opción correcta de la lista."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'elemento': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            # Validar stock disponible
            if cantidad < 1:
                msg = "La cantidad a prestar debe ser como mínimo 1. No se permiten valores de 0 o negativos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_prestada': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            if cantidad > elemento.cantidad_total:
                msg = f"Stock insuficiente. Disponible: {elemento.cantidad_total}"
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_prestada': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            # Validar días
            if dias < 1 or dias > 15:
                msg = "Los días de préstamo deben estar entre 1 y 15."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'dias_prestamo': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            obs = request.POST.get('observacion', '').strip()
            if len(obs) > 500:
                msg = "La observación no puede superar los 500 caracteres."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'observacion': msg}}, status=400)
                messages.error(request, msg)
                return redirect('inventario')

            fecha_devolucion = date.today() + timedelta(days=dias)

            Prestamo.objects.create(
                usuario=request.user,
                elemento=elemento,
                cantidad_prestada=cantidad,
                dias_prestamo=dias,
                fecha_devolucion=fecha_devolucion,
                observacion_prestamo=obs,
                estado_prestamo='Activo',
            )

            # Descontar del inventario
            elemento.cantidad_total -= cantidad
            elemento.save()

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': f"Préstamo registrado. Devolución antes del {fecha_devolucion.strftime('%d/%m/%Y')}."
                }, status=201)

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
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json'
        accion = request.POST.get('accion')

        if accion == 'registrar_devolucion':
            codigo_prestamo = request.POST.get('prestamo')
            cantidad_raw = request.POST.get('cantidad_devuelta', 1)
            try:
                cantidad_devuelta = int(cantidad_raw)
            except (ValueError, TypeError):
                msg = "La cantidad devuelta debe ser un número entero."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_devuelta': msg}}, status=400)
                messages.error(request, msg)
                return redirect('devoluciones')

            if cantidad_devuelta < 1:
                msg = "La cantidad a devolver debe ser como mínimo 1. No se permiten valores de 0 o negativos."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_devuelta': msg}}, status=400)
                messages.error(request, msg)
                return redirect('devoluciones')

            tiene_novedad = request.POST.get('tiene_novedad') == 'on'
            estado_elemento = request.POST.get('estado_elemento_devolucion')
            tipo_novedad = request.POST.get('tipo_novedad_devolucion', '')
            observaciones = request.POST.get('observaciones_devolucion', '').strip()

            if len(observaciones) > 500:
                msg = "Las observaciones no pueden superar los 500 caracteres."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'observaciones_devolucion': msg}}, status=400)
                messages.error(request, msg)
                return redirect('devoluciones')

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
                msg = f"La cantidad a devolver no puede superar la prestada ({prestamo.cantidad_prestada})."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': msg, 'errors': {'cantidad_devuelta': msg}}, status=400)
                messages.error(request, msg)
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
                    devolucion=devolucion_creada,
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
                Notificacion.objects.create(
                    usuario=prestamo.usuario,
                    titulo=f"Sanción registrada por {tipo_novedad.lower()}",
                    mensaje=f"Se ha generado una sanción preventiva de 30 días asociada a la devolución con novedad de '{elemento.tipo_maquina}'.",
                    tipo='danger',
                    icono='fa-gavel',
                    enlace='/inventario/sanciones/'
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
    Admin: ve todas las sanciones, puede crear, editar y cerrar.
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

        # ── 1. CREAR SANCIÓN ──
        if accion == 'crear_sancion':
            from datetime import datetime as dt_class
            
            usuario_id = request.POST.get('usuario_id')
            if not usuario_id:
                messages.error(request, "Debes seleccionar un usuario válido a sancionar.")
                return redirect('sanciones')

            usuario_target = Usuario.objects.filter(pk=usuario_id, is_active=True).first()
            if not usuario_target:
                messages.error(request, "El usuario seleccionado no existe o está inactivo.")
                return redirect('sanciones')

            tipo_sancion = request.POST.get('tipo_sancion', '').strip()
            if not tipo_sancion or len(tipo_sancion) < 3 or len(tipo_sancion) > 100:
                messages.error(request, "El motivo o tipo de sanción es obligatorio y debe tener entre 3 y 100 caracteres.")
                return redirect('sanciones')

            inicio_str = request.POST.get('fecha_inicio_sancion', '').strip()
            fin_str = request.POST.get('fecha_fin_sancion', '').strip()
            if not inicio_str or not fin_str:
                messages.error(request, "Las fechas de inicio y fin de la sanción son obligatorias.")
                return redirect('sanciones')

            try:
                inicio_val = dt_class.strptime(inicio_str, '%Y-%m-%d').date()
                fin_val = dt_class.strptime(fin_str, '%Y-%m-%d').date()
                
                if fin_val < inicio_val:
                    messages.error(request, f"La fecha de fin ({fin_val.strftime('%d/%m/%Y')}) no puede ser anterior a la fecha de inicio ({inicio_val.strftime('%d/%m/%Y')}).")
                    return redirect('sanciones')

                if (fin_val - inicio_val).days > 365:
                    messages.error(request, "El periodo de una sanción no puede superar los 365 días (1 año).")
                    return redirect('sanciones')
            except ValueError:
                messages.error(request, "Formato de fechas de sanción inválido. Debe ser AAAA-MM-DD.")
                return redirect('sanciones')

            estado_sancion = request.POST.get('estado_sancion', 'Activa').strip()
            if estado_sancion not in ['Activa', 'Cerrada']:
                estado_sancion = 'Activa'

            descripcion = request.POST.get('descripcion_sancion', '').strip()
            if len(descripcion) > 500:
                messages.error(request, "La descripción de la sanción no puede superar los 500 caracteres.")
                return redirect('sanciones')

            sancion = Sancion.objects.create(
                usuario=usuario_target,
                tipo_sancion=tipo_sancion,
                fecha_inicio_sancion=inicio_val,
                fecha_fin_sancion=fin_val,
                estado_sancion=estado_sancion,
                descripcion_sancion=descripcion,
            )

            Notificacion.objects.create(
                usuario=usuario_target,
                titulo='Registro de Sanción Disciplinaria',
                mensaje=f'Se ha registrado una sanción ({tipo_sancion}) del {inicio_val.strftime("%d/%m/%Y")} al {fin_val.strftime("%d/%m/%Y")}.',
                tipo='danger',
                icono='fa-gavel',
                enlace='/inventario/sanciones/'
            )

            messages.success(request, f"Sanción registrada correctamente para {usuario_target.get_full_name()}.")
            return redirect('sanciones')

        # ── 2. EDITAR SANCIÓN ──
        elif accion == 'editar_sancion':
            from datetime import datetime as dt_class

            codigo = request.POST.get('codigo_sancion')
            sancion = get_object_or_404(Sancion, codigo_sancion=codigo)

            usuario_id = request.POST.get('usuario_id')
            usuario_target = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else sancion.usuario
            if not usuario_target:
                messages.error(request, "El usuario asociado a la sanción no es válido.")
                return redirect('sanciones')

            tipo_sancion = request.POST.get('tipo_sancion', '').strip()
            if not tipo_sancion or len(tipo_sancion) < 3 or len(tipo_sancion) > 100:
                messages.error(request, "El motivo o tipo de sanción debe contener entre 3 y 100 caracteres.")
                return redirect('sanciones')

            inicio_str = request.POST.get('fecha_inicio_sancion', '').strip()
            fin_str = request.POST.get('fecha_fin_sancion', '').strip()
            if not inicio_str or not fin_str:
                messages.error(request, "Las fechas de inicio y fin son obligatorias.")
                return redirect('sanciones')

            try:
                inicio_val = dt_class.strptime(inicio_str, '%Y-%m-%d').date()
                fin_val = dt_class.strptime(fin_str, '%Y-%m-%d').date()

                if fin_val < inicio_val:
                    messages.error(request, "La fecha de fin no puede ser anterior a la de inicio.")
                    return redirect('sanciones')

                if (fin_val - inicio_val).days > 365:
                    messages.error(request, "El periodo de sanción no puede superar 365 días.")
                    return redirect('sanciones')
            except ValueError:
                messages.error(request, "Formato de fechas de sanción inválido.")
                return redirect('sanciones')

            estado_sancion = request.POST.get('estado_sancion', sancion.estado_sancion).strip()
            if estado_sancion not in ['Activa', 'Cerrada']:
                estado_sancion = 'Activa'

            descripcion = request.POST.get('descripcion_sancion', '').strip()
            if len(descripcion) > 500:
                messages.error(request, "La descripción no puede superar los 500 caracteres.")
                return redirect('sanciones')

            sancion.usuario = usuario_target
            sancion.tipo_sancion = tipo_sancion
            sancion.fecha_inicio_sancion = inicio_val
            sancion.fecha_fin_sancion = fin_val
            sancion.estado_sancion = estado_sancion
            sancion.descripcion_sancion = descripcion
            sancion.save()

            messages.success(request, f"Sanción #{sancion.codigo_sancion} modificada y validada exitosamente.")
            return redirect('sanciones')

        # ── 3. CERRAR SANCIÓN ──
        elif accion == 'cerrar_sancion':
            codigo = request.POST.get('codigo_sancion')
            sancion = get_object_or_404(Sancion, codigo_sancion=codigo)
            sancion.estado_sancion = 'Cerrada'
            sancion.save()
            if sancion.usuario:
                Notificacion.objects.create(
                    usuario=sancion.usuario,
                    titulo='Sanción levantada / cerrada',
                    mensaje=f'Tu sanción disciplinaria ({sancion.tipo_sancion}) ha sido cerrada por la administración.',
                    tipo='success',
                    icono='fa-check-circle',
                    enlace='/inventario/sanciones/'
                )
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
        tipo_maquina = request.POST.get('tipo_maquina', '').strip()
        if not tipo_maquina or len(tipo_maquina) < 2 or len(tipo_maquina) > 100:
            messages.error(request, "El nombre del elemento es obligatorio y debe tener entre 2 y 100 caracteres.")
            return redirect('inventario')

        cantidad_raw = request.POST.get('cantidad_total')
        try:
            cantidad_total = int(cantidad_raw)
        except (ValueError, TypeError):
            messages.error(request, "La cantidad debe ser un número entero válido.")
            return redirect('inventario')

        if cantidad_total < 1 or cantidad_total > 9999:
            messages.error(request, "La cantidad debe ser como mínimo 1 y no superar 9999 unidades.")
            return redirect('inventario')

        # Validar fecha de adquisición (1 año atrás a hoy)
        fecha_adq, error_fecha = _validar_fecha_adquisicion(request.POST.get('fecha_adquisicion'))
        if error_fecha:
            messages.error(request, error_fecha)
            return redirect('inventario')

        elemento.tipo_maquina = tipo_maquina
        elemento.cantidad_total = cantidad_total
        elemento.estado_general = request.POST.get('estado_general') or elemento.estado_general or 'Buen estado'
        elemento.fecha_adquisicion = fecha_adq

        responsable_id = request.POST.get('usuario_responsable')
        if responsable_id:
            elemento.usuario_responsable = Usuario.objects.filter(id=responsable_id).first()
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
        # Al administrador NUNCA se le bloquea por inventario o morosidad
        if u.rol == 'admin' or u.is_superuser or u.is_staff:
            continue

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
