from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date

from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion, Revision

def inventario_list(request):
    elementos = ElementoDeportivo.objects.all()
    prestamos = Prestamo.objects.all().order_by('-fecha_prestamo')
    sanciones = Sancion.objects.all()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear_elemento':
            # manejar imagen si viene
            imagen = request.FILES.get('imagen_elemento')
            elemento = ElementoDeportivo.objects.create(
                tipo_maquina=request.POST.get('tipo_maquina'),
                cantidad_total=request.POST.get('cantidad_total') or 0,
                estado_general=request.POST.get('estado_general'),
                fecha_adquisicion=request.POST.get('fecha_adquisicion') or None,
                descripcion=request.POST.get('descripcion'),
                docente_responsable=request.POST.get('docente_responsable'),
            )
            if imagen:
                # asume que tu modelo tiene campo ImageField/ FileField llamado 'imagen'
                elemento.imagen = imagen
                elemento.save()
            return redirect('inventario')

        if accion == 'crear_prestamo':
            Prestamo.objects.create(
                elemento_id=request.POST.get('elemento'),
                hora_prestamo=request.POST.get('hora_prestamo'),
                dias_prestamo=request.POST.get('dias_prestamo'),
                fecha_devolucion=request.POST.get('fecha_devolucion'),
                cantidad_prestada=request.POST.get('cantidad_prestada'),
                observacion_prestamo=request.POST.get('observacion'),
            )
            return redirect('inventario')

    return render(request, 'inventario/inventario.html', {
        'elementos': elementos,
        'prestamos': prestamos,
        'sanciones': sanciones,
    })


def eliminar_elemento(request, id):
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)
    elemento.delete()
    return redirect('inventario')


@require_http_methods(["GET", "POST"])
def editar_elemento(request, id):
    """
    - Si la petición es AJAX (X-Requested-With: XMLHttpRequest):
        GET  -> devuelve JSON con los datos del elemento (incluida URL de imagen si existe).
        POST -> actualiza el elemento con los campos recibidos (acepta imagen nueva en request.FILES)
                y devuelve JSON con el elemento actualizado.
    - Si la petición NO es AJAX:
        GET/POST -> redirige al listado (o podrías renderizar una plantilla de edición si la añades).
    """
    elemento = get_object_or_404(ElementoDeportivo, codigo_elemento=id)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if is_ajax and request.method == 'GET':
        imagen_url = ''
        if getattr(elemento, 'imagen', None) and elemento.imagen:
            try:
                imagen_url = request.build_absolute_uri(elemento.imagen.url)
            except Exception:
                imagen_url = ''
        data = {
            'id': elemento.codigo_elemento,
            'tipo': elemento.tipo_maquina,
            'cantidad': elemento.cantidad_total,
            'estado': elemento.estado_general,
            'docente': str(elemento.docente_responsable) if elemento.docente_responsable is not None else '',
            'fecha': elemento.fecha_adquisicion.isoformat() if elemento.fecha_adquisicion else '',
            'descripcion': elemento.descripcion or '',
            'imagen': imagen_url,
        }
        return JsonResponse({'success': True, 'elemento': data})

    if is_ajax and request.method == 'POST':
        # Actualizar campos (mantener valor actual si no vienen)
        tipo = request.POST.get('tipo_maquina', elemento.tipo_maquina)
        cantidad = request.POST.get('cantidad_total', elemento.cantidad_total)
        estado = request.POST.get('estado_general', elemento.estado_general)
        fecha_str = request.POST.get('fecha_adquisicion')
        docente = request.POST.get('docente_responsable', elemento.docente_responsable)
        descripcion = request.POST.get('descripcion', elemento.descripcion)

        elemento.tipo_maquina = tipo
        elemento.cantidad_total = cantidad
        elemento.estado_general = estado
        # parsear fecha si viene
        if fecha_str:
            try:
                elemento.fecha_adquisicion = parse_date(fecha_str)
            except Exception:
                pass
        elemento.docente_responsable = docente
        elemento.descripcion = descripcion

        # Si se envió imagen nueva, reemplazar
        if 'imagen_elemento' in request.FILES:
            nueva_imagen = request.FILES['imagen_elemento']
            # eliminar imagen antigua (opcional)
            try:
                if getattr(elemento, 'imagen', None):
                    elemento.imagen.delete(save=False)
            except Exception:
                pass
            elemento.imagen = nueva_imagen

        elemento.save()

        imagen_url = ''
        if getattr(elemento, 'imagen', None) and elemento.imagen:
            try:
                imagen_url = request.build_absolute_uri(elemento.imagen.url)
            except Exception:
                imagen_url = ''

        elemento_data = {
            'id': elemento.codigo_elemento,
            'tipo': elemento.tipo_maquina,
            'cantidad': elemento.cantidad_total,
            'estado': elemento.estado_general,
            'docente': str(elemento.docente_responsable) if elemento.docente_responsable is not None else '',
            'fecha': elemento.fecha_adquisicion.isoformat() if elemento.fecha_adquisicion else '',
            'descripcion': elemento.descripcion or '',
            'imagen': imagen_url,
        }
        return JsonResponse({'success': True, 'elemento': elemento_data})

    # Petición normal (no-AJAX): redirigir al listado (evita TemplateDoesNotExist)
    return redirect('inventario')
    

def eliminar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, codigo_prestamo=id)
    prestamo.delete()
    return redirect('inventario')