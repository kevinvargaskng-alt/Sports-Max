from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion, Revision
from datetime import datetime

@login_required
def inventario_list(request):
    elementos = ElementoDeportivo.objects.all()
    prestamos = Prestamo.objects.all().order_by('-fecha_prestamo')
    sanciones = Sancion.objects.all()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # 1. CREAR ELEMENTO (CON IMAGEN)
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

        # 2. EDITAR ELEMENTO (DESDE MODAL)
        elif accion == 'editar_elemento':
            codigo = request.POST.get('codigo_elemento')
            if codigo:
                elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=codigo)
                
                if 'imagen' in request.FILES:
                    elemento.imagen = request.FILES.get('imagen')
                
                elemento.tipo_maquina = request.POST.get('tipo_maquina')
                elemento.cantidad_total = request.POST.get('cantidad_total')
                elemento.estado_general = request.POST.get('estado_general')
                elemento.fecha_adquisicion = request.POST.get('fecha_adquisicion')
                elemento.descripcion = request.POST.get('descripcion')
                elemento.docente_responsable = request.POST.get('docente_responsable')
                elemento.save()
                messages.success(request, "Elemento actualizado correctamente.")
            return redirect('inventario')

        # 3. CREAR PRÉSTAMO (AUTOMATIZADO PARA EL USUARIO LOGUEADO)
        elif accion == 'crear_prestamo':
            id_elemento = request.POST.get('elemento')
            cantidad = int(request.POST.get('cantidad_prestada', 0))
            elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id_elemento)

            # Validación de Stock
            if cantidad > elemento.cantidad_total:
                messages.error(request, f"No hay suficiente stock. Disponible: {elemento.cantidad_total}")
                return redirect('inventario')

            # Se crea el préstamo vinculando automáticamente al usuario que inició sesión
            Prestamo.objects.create(
                usuario=request.user,  # Vinculación automática
                elemento=elemento,
                cantidad_prestada=cantidad,
                # Soporta tanto 'hora_prestamo' (si existe en el modelo) como los días calculados
                dias_prestamo=request.POST.get('dias_prestamo'),
                fecha_devolucion=request.POST.get('fecha_devolucion'), 
                observacion_prestamo=request.POST.get('observacion'),
                estado_prestamo='Activo'
            )
            
            messages.success(request, "Solicitud de préstamo registrada correctamente.")
            return redirect('inventario')

    return render(request, 'inventario/inventario.html', {
        'elementos': elementos,
        'prestamos': prestamos,
        'sanciones': sanciones,
    })

@login_required
def eliminar_elemento(request, id):
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)
    elemento.delete()
    messages.warning(request, "Elemento eliminado del inventario.")
    return redirect('inventario')

# Vista para edición en página separada (si se llega a usar)
@login_required
def editar_elemento(request, id):
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)
    if request.method == 'POST':
        if 'imagen' in request.FILES:
            elemento.imagen = request.FILES.get('imagen')
        elemento.tipo_maquina = request.POST.get('tipo_maquina')
        elemento.cantidad_total = request.POST.get('cantidad_total')
        elemento.estado_general = request.POST.get('estado_general')
        elemento.docente_responsable = request.POST.get('docente_responsable')
        elemento.save()
        messages.success(request, "Elemento actualizado correctamente.")
        return redirect('inventario')
    return render(request, 'inventario/editar.html', {'elemento': elemento})

@login_required
def eliminar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, codigo_prestamo=id)
    prestamo.delete()
    messages.info(request, "Préstamo finalizado/eliminado.")
    return redirect('inventario')