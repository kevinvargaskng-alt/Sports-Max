from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion, Revision
from datetime import datetime, date, timedelta
from usuarios.models import Usuario


@login_required
def inventario_list(request):
    estaSancionado= Sancion.objects.filter(usuario=request.user, estado_sancion='Activa').exists()
    elementos = ElementoDeportivo.objects.all()
    # Solo muestra los préstamos del usuario logueado
    prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-fecha_prestamo')
    sanciones = Sancion.objects.filter(usuario=request.user, estado_sancion='Activa')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # ─────────────────────────────────────────────
        # 1. CREAR ELEMENTO (CON IMAGEN)
        # ─────────────────────────────────────────────
        if accion == 'crear_elemento':
            ElementoDeportivo.objects.create(
                imagen=request.FILES.get('imagen'),
                tipo_maquina=request.POST.get('tipo_maquina'),
                cantidad_total=request.POST.get('cantidad_total'),
                estado_general=request.POST.get('estado_general'),
                fecha_adquisicion=request.POST.get('fecha_adquisicion'),
                descripcion=request.POST.get('descripcion'),
                docente_responsable=request.POST.get('docente_responsable'),
            )
            messages.success(request, "Elemento creado exitosamente.")
            return redirect('inventario')

        # ─────────────────────────────────────────────
        # 2. EDITAR ELEMENTO
        # ─────────────────────────────────────────────
        elif accion == 'editar_elemento':
            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=codigo)
                if 'imagen' in request.FILES:
                    elemento.imagen = request.FILES['imagen']
                elemento.tipo_maquina          = request.POST.get('tipo_maquina')
                elemento.cantidad_total        = request.POST.get('cantidad_total')
                elemento.estado_general        = request.POST.get('estado_general')
                elemento.fecha_adquisicion     = request.POST.get('fecha_adquisicion')
                elemento.descripcion           = request.POST.get('descripcion')
                elemento.docente_responsable   = request.POST.get('docente_responsable')
                elemento.save()
                messages.success(request, "Elemento actualizado correctamente.")
            return redirect('inventario')

        # ─────────────────────────────────────────────
        # 3. CREAR PRÉSTAMO  ← CORREGIDO
        # ─────────────────────────────────────────────
        elif accion == 'crear_prestamo':
            id_elemento  = request.POST.get('elemento')
            cantidad     = int(request.POST.get('cantidad_prestada', 0))
            dias         = int(request.POST.get('dias_prestamo', 1))

            elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id_elemento)

            # Validación de stock
            if cantidad > elemento.cantidad_total:
                messages.error(
                    request,
                    f"No hay suficiente stock. Disponible: {elemento.cantidad_total}"
                )
                return redirect('inventario')

            # Calcular fecha de devolución automáticamente desde los días
            fecha_devolucion = date.today() + timedelta(days=dias)

            Prestamo.objects.create(
                usuario             = request.user,
                elemento            = elemento,
                cantidad_prestada   = cantidad,
                dias_prestamo       = dias,
                fecha_devolucion    = fecha_devolucion,
                observacion_prestamo= request.POST.get('observacion', ''),
                estado_prestamo     = 'Activo',
            )

            # Descontar del inventario
            elemento.cantidad_total -= cantidad
            elemento.save()

            messages.success(request, "Solicitud de préstamo registrada correctamente.")
            return redirect('inventario')

    return render(request, 'inventario/inventario.html', {
        'elementos': elementos,
        'prestamos': prestamos,
        'sanciones': sanciones,
        'estaSancionado': estaSancionado,
    })


# ─────────────────────────────────────────────────────────────
# DEVOLUCIONES
# ─────────────────────────────────────────────────────────────

@login_required
def devoluciones_list(request):
    """Lista los préstamos activos del usuario y permite registrar devoluciones."""
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
            codigo_prestamo   = request.POST.get('prestamo')
            cantidad_devuelta = int(request.POST.get('cantidad_devuelta', 1))
            tiene_novedad     = request.POST.get('tiene_novedad') == 'on'
            estado_elemento   = request.POST.get('estado_elemento_devolucion')
            tipo_novedad      = request.POST.get('tipo_novedad_devolucion', '')
            observaciones     = request.POST.get('observaciones_devolucion', '')

            prestamo = get_object_or_404(
                Prestamo, codigo_prestamo=codigo_prestamo, usuario=request.user
            )

            # Registrar la devolución
            Devolucion.objects.create(
                prestamo                   = prestamo,
                cantidad_devuelta          = cantidad_devuelta,
                fecha_devolucion           = date.today(),
                hora_devolucion            = datetime.now().time(),
                tiene_novedad              = tiene_novedad,
                estado_elemento_devolucion = estado_elemento,
                tipo_novedad_devolucion    = tipo_novedad,
                observaciones_devolucion   = observaciones,
            )

            # Restaurar stock al inventario
            elemento = prestamo.elemento
            elemento.cantidad_total += cantidad_devuelta
            elemento.save()

            # Crear sanción automática si hay novedad grave
            if tiene_novedad and tipo_novedad in ['Daño', 'Pérdida']:
                Sancion.objects.create(
                    usuario              = prestamo.usuario,
                    tipo_sancion         = f"{tipo_novedad} de {elemento.tipo_maquina}",
                    fecha_inicio_sancion = date.today(),
                    fecha_fin_sancion    = date.today() + timedelta(days=30),
                    estado_sancion       = 'Activa',
                    descripcion_sancion  = (
                        f"Sanción automática por {tipo_novedad.lower()} del elemento "
                        f"'{elemento.tipo_maquina}'. Préstamo #{prestamo.codigo_prestamo}. "
                        f"Observación: {observaciones}"
                    ),
                )
                messages.warning(
                    request,
                    f"Se registró una sanción automática por {tipo_novedad.lower()} del elemento."
                )

            # Marcar préstamo como devuelto
            prestamo.estado_prestamo = 'Devuelto'
            prestamo.save()

            messages.success(request, "Devolución registrada correctamente.")
            return redirect('devoluciones')

    return render(request, 'inventario/devoluciones.html', {
        'prestamos_activos': prestamos_activos,
        'devoluciones':      devoluciones,
    })


# ─────────────────────────────────────────────────────────────
# SANCIONES
# ─────────────────────────────────────────────────────────────

@login_required
def sanciones_list(request):
    """Lista todas las sanciones. Solo staff puede crear o cerrar manualmente."""
    if request.user.is_staff:
        sanciones = Sancion.objects.all().order_by('-fecha_inicio_sancion')
    else:
        sanciones = Sancion.objects.filter(usuario=request.user).order_by('-fecha_inicio_sancion')
        
    usuarios = Usuario.objects.filter(is_active=True).order_by('first_name')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if not request.user.is_staff:
            messages.error(request, "No tienes permisos para esta acción.")
            return redirect('sanciones')

        if accion == 'crear_sancion':
            Sancion.objects.create(
                usuario_id           = request.POST.get('usuario_id'),
                tipo_sancion         = request.POST.get('tipo_sancion'),
                fecha_inicio_sancion = request.POST.get('fecha_inicio_sancion'),
                fecha_fin_sancion    = request.POST.get('fecha_fin_sancion'),
                estado_sancion       = 'Activa',
                descripcion_sancion  = request.POST.get('descripcion_sancion', ''),
            )
            messages.success(request, "Sanción creada correctamente.")
            return redirect('sanciones')

        elif accion == 'cerrar_sancion':
            codigo  = request.POST.get('codigo_sancion')
            sancion = get_object_or_404(Sancion, codigo_sancion=codigo)
            sancion.estado_sancion = 'Cerrada'
            sancion.save()
            messages.success(request, "Sanción cerrada correctamente.")
            return redirect('sanciones')

    return render(request, 'inventario/sanciones.html', {
        'sanciones': sanciones,
        'usuarios': usuarios,
    })


# ─────────────────────────────────────────────────────────────
# CRUD básico (compatibilidad con URLs existentes)
# ─────────────────────────────────────────────────────────────

@login_required
def eliminar_elemento(request, id):
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)
    elemento.delete()
    messages.warning(request, "Elemento eliminado del inventario.")
    return redirect('inventario')


@login_required
def editar_elemento(request, id):
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)
    if request.method == 'POST':
        if 'imagen' in request.FILES:
            elemento.imagen = request.FILES['imagen']
        elemento.tipo_maquina        = request.POST.get('tipo_maquina')
        elemento.cantidad_total      = request.POST.get('cantidad_total')
        elemento.estado_general      = request.POST.get('estado_general')
        elemento.docente_responsable = request.POST.get('docente_responsable')
        elemento.save()
        messages.success(request, "Elemento actualizado correctamente.")
        return redirect('inventario')
    return render(request, 'inventario/editar.html', {'elemento': elemento})


@login_required
def eliminar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, codigo_prestamo=id)
    # Restaurar stock si aún estaba activo
    if prestamo.estado_prestamo == 'Activo':
        elemento = prestamo.elemento
        elemento.cantidad_total += prestamo.cantidad_prestada
        elemento.save()
    prestamo.delete()
    messages.info(request, "Préstamo finalizado/eliminado.")
    return redirect('inventario')