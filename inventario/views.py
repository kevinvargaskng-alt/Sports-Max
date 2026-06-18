from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion
from datetime import datetime, date, timedelta
from usuarios.models import Usuario


# ─────────────────────────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────────────────────────

@login_required
def inventario_list(request):
    elementos = ElementoDeportivo.objects.all()
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

            ElementoDeportivo.objects.create(
                # el form manda nombre_elemento
                tipo_maquina=request.POST.get('nombre_elemento'),
                cantidad_total=request.POST.get('cantidad_total'),
                estado_general=request.POST.get('estado_general'),
                fecha_adquisicion=request.POST.get(
                    'fecha_adquisicion') or None,
                descripcion=request.POST.get('descripcion', ''),
                imagen=request.FILES.get('imagen'),
                usuario_responsable=responsable,
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
                elemento.estado_general = request.POST.get('estado_general')
                elemento.fecha_adquisicion = request.POST.get(
                    'fecha_adquisicion') or None
                elemento.descripcion = request.POST.get('descripcion', '')
                if 'imagen' in request.FILES:
                    elemento.imagen = request.FILES['imagen']
                elemento.save()
                messages.success(
                    request, "Elemento actualizado correctamente.")
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
            Devolucion.objects.create(
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
            Sancion.objects.create(
                usuario_id=request.POST.get('usuario_id'),
                tipo_sancion=request.POST.get('tipo_sancion'),
                fecha_inicio_sancion=request.POST.get('fecha_inicio_sancion'),
                fecha_fin_sancion=request.POST.get('fecha_fin_sancion'),
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
            elemento.imagen = request.FILES['imagen']
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
