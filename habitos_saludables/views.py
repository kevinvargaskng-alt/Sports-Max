"""
views.py - Vistas del módulo Hábitos Saludables SENA
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q, Avg
from django.utils import timezone

from .models import (
    HabitoSaludable, PiramideNutricional, MaterialApoyo,
    SeguimientoSalud, HabeasDataConsent, RutinaFisica
)
from .forms import (
    SeguimientoSaludForm, MaterialApoyoForm,
    BuscarMaterialForm, HabeasDataForm
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def tiene_habeas_data(user):
    """Verifica si el usuario ha aceptado el Habeas Data."""
    try:
        return user.habeas_data.acepta
    except HabeasDataConsent.DoesNotExist:
        return False


def requiere_habeas_data(view_func):
    """
    Decorador: redirige al formulario de Habeas Data si no ha sido aceptado.
    """
    def wrapper(request, *args, **kwargs):
        if not tiene_habeas_data(request.user):
            messages.warning(
                request,
                'Debes aceptar el tratamiento de datos (Habeas Data) '
                'antes de acceder a esta sección.'
            )
            return redirect('habitos:habeas_data')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def get_client_ip(request):
    """Obtiene la IP real del cliente."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─────────────────────────────────────────────
# INICIO / DASHBOARD
# ─────────────────────────────────────────────
@login_required
def inicio(request):
    """
    Página principal del módulo con resumen de secciones.
    """
    habitos_destacados = HabitoSaludable.objects.filter(activo=True)[:6]
    rutinas_recientes = RutinaFisica.objects.filter(activo=True)[:3]
    materiales_recientes = MaterialApoyo.objects.filter(activo=True)[:4]

    # Último seguimiento del usuario
    ultimo_seguimiento = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).first()

    tiene_consent = tiene_habeas_data(request.user)

    ctx = {
        'habitos': habitos_destacados,
        'rutinas': rutinas_recientes,
        'materiales': materiales_recientes,
        'ultimo_seguimiento': ultimo_seguimiento,
        'tiene_consent': tiene_consent,
        'titulo_pagina': 'Inicio — Hábitos Saludables',
        'vista': 'inicio',  # Aunque no se usa en inicio.html, es buena práctica
    }
    return render(request, 'habitos/inicio.html', ctx)


@login_required
def dashboard(request):
    """
    Dashboard personal con estadísticas de salud del usuario.
    """
    seguimientos = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).order_by('fecha_evaluacion')

    # Datos para gráficas (JSON)
    fechas = [str(s.fecha_evaluacion) for s in seguimientos]
    pesos = [float(s.peso_kg) for s in seguimientos]
    imcs = [float(s.imc) if s.imc else None for s in seguimientos]
    frecuencias = [
        s.frecuencia_cardiaca for s in seguimientos
        if s.frecuencia_cardiaca
    ]

    # Promedios
    promedios = seguimientos.aggregate(
        avg_peso=Avg('peso_kg'),
        avg_imc=Avg('imc'),
        avg_fc=Avg('frecuencia_cardiaca'),
    )

    ultimo = seguimientos.last()
    categoria_imc = ultimo.get_categoria_imc() if ultimo else ('Sin datos', 'secondary')

    ctx = {
        'seguimientos': seguimientos,
        'ultimo': ultimo,
        'categoria_imc': categoria_imc,
        'promedios': promedios,
        'fechas_json': json.dumps(fechas),
        'pesos_json': json.dumps(pesos),
        'imcs_json': json.dumps(imcs),
        'tiene_consent': tiene_habeas_data(request.user),
        'titulo_pagina': 'Mi Dashboard de Salud',
        'vista': 'dashboard',
    }
    return render(request, 'habitos/inicio_dashboard.html', ctx)


# ─────────────────────────────────────────────
# HABEAS DATA
# ─────────────────────────────────────────────
@login_required
def habeas_data(request):
    """
    Formulario de aceptación del tratamiento de datos personales.
    """
    # Si ya aceptó, mostrar confirmación
    try:
        consent = request.user.habeas_data
        if consent.acepta:
            return render(request, 'habitos/habeas_data_ok.html', {
                'consent': consent,
                'titulo_pagina': 'Habeas Data — Aceptado'
            })
    except HabeasDataConsent.DoesNotExist:
        consent = None

    if request.method == 'POST':
        form = HabeasDataForm(request.POST)
        if form.is_valid():
            obj, _ = HabeasDataConsent.objects.get_or_create(
                usuario=request.user)
            obj.acepta = True
            obj.direccion_ip = get_client_ip(request)
            obj.save()
            messages.success(
                request,
                '✓ Has aceptado el tratamiento de datos. '
                'Ahora puedes registrar tu información de salud.'
            )
            return redirect('habitos:dashboard')
    else:
        form = HabeasDataForm()

    return render(request, 'habitos/salud.html', {
        'form': form,
        'titulo_pagina': 'Autorización Habeas Data',
        'vista': 'habeas_data',
    })


# ─────────────────────────────────────────────
# HÁBITOS SALUDABLES (contenido educativo)
# ─────────────────────────────────────────────
@login_required
def lista_habitos(request):
    """Vista principal del contenido educativo sobre hábitos."""
    categoria = request.GET.get('categoria', '')
    habitos = HabitoSaludable.objects.filter(activo=True)

    if categoria:
        habitos = habitos.filter(categoria=categoria)

    categorias = HabitoSaludable.CATEGORIA_CHOICES

    ctx = {
        'habitos': habitos,
        'categorias': categorias,
        'categoria_activa': categoria,
        'titulo_pagina': 'Hábitos Saludables',
        'vista': 'habitos',
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def detalle_habito(request, pk):
    """Detalle de un hábito saludable específico."""
    habito = get_object_or_404(HabitoSaludable, pk=pk, activo=True)
    relacionados = HabitoSaludable.objects.filter(
        categoria=habito.categoria, activo=True
    ).exclude(pk=pk)[:3]

    return render(request, 'habitos/contenido_educativo.html', {
        'habito': habito,
        'relacionados': relacionados,
        'titulo_pagina': habito.titulo,
        'vista': 'detalle_habito',
    })


# ─────────────────────────────────────────────
# RUTINAS FÍSICAS
# ─────────────────────────────────────────────
@login_required
def lista_rutinas(request):
    """Catálogo de rutinas físicas filtradas por nivel."""
    nivel = request.GET.get('nivel', '')
    objetivo = request.GET.get('objetivo', '')

    rutinas = RutinaFisica.objects.filter(activo=True)
    if nivel:
        rutinas = rutinas.filter(nivel=nivel)
    if objetivo:
        rutinas = rutinas.filter(objetivo=objetivo)

    ctx = {
        'rutinas': rutinas,
        'niveles': RutinaFisica.NIVEL_CHOICES,
        'objetivos': RutinaFisica.OBJETIVO_CHOICES,
        'nivel_activo': nivel,
        'objetivo_activo': objetivo,
        'titulo_pagina': 'Rutinas Físicas',
        'vista': 'rutinas',
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def detalle_rutina(request, pk):
    """Detalle de una rutina física."""
    rutina = get_object_or_404(RutinaFisica, pk=pk, activo=True)
    return render(request, 'habitos/contenido_educativo.html', {
        'rutina': rutina,
        'titulo_pagina': rutina.nombre,
        'vista': 'detalle_rutina',
    })


# ─────────────────────────────────────────────
# PIRÁMIDE NUTRICIONAL
# ─────────────────────────────────────────────
@login_required
def piramide_nutricional(request):
    """Vista de la pirámide nutricional con tarjetas por nivel."""
    categoria = request.GET.get('categoria', '')
    alimentos = PiramideNutricional.objects.filter(activo=True)

    if categoria:
        alimentos = alimentos.filter(categoria=categoria)

    # Agrupar por nivel para mostrar la pirámide
    por_nivel = {}
    for alimento in PiramideNutricional.objects.filter(activo=True).order_by('nivel_piramide'):
        nivel = alimento.nivel_piramide
        if nivel not in por_nivel:
            por_nivel[nivel] = []
        por_nivel[nivel].append(alimento)

    ctx = {
        'alimentos': alimentos,
        'por_nivel': por_nivel,
        'categorias': PiramideNutricional.CATEGORIA_CHOICES,
        'categoria_activa': categoria,
        'titulo_pagina': 'Pirámide Nutricional',
        'vista': 'nutricion',
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


# ─────────────────────────────────────────────
# MATERIAL DE APOYO
# ─────────────────────────────────────────────
@login_required
def biblioteca(request):
    """Biblioteca de materiales de apoyo con búsqueda y filtros."""
    form = BuscarMaterialForm(request.GET)
    materiales = MaterialApoyo.objects.filter(activo=True)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        tipo = form.cleaned_data.get('tipo')

        if q:
            materiales = materiales.filter(
                Q(titulo__icontains=q) | Q(descripcion__icontains=q)
            )
        if tipo:
            materiales = materiales.filter(tipo_contenido=tipo)

    ctx = {
        'materiales': materiales,
        'form': form,
        'total': materiales.count(),
        'titulo_pagina': 'Biblioteca de Materiales',
        'vista': 'biblioteca',
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def descargar_material(request, pk):
    """Descarga/acceso a material y registra el contador."""
    material = get_object_or_404(MaterialApoyo, pk=pk, activo=True)

    if material.tipo_contenido == 'video':
        # Redirigir a URL externa
        material.incrementar_descargas()
        return redirect(material.url_video)

    if material.archivo:
        material.incrementar_descargas()
        try:
            return FileResponse(
                material.archivo.open('rb'),
                as_attachment=True,
                filename=material.archivo.name.split('/')[-1]
            )
        except FileNotFoundError:
            raise Http404('Archivo no encontrado.')

    messages.error(request, 'Este material no tiene archivo disponible.')
    return redirect('habitos:biblioteca')


# ─────────────────────────────────────────────
# SEGUIMIENTO DE SALUD
# ─────────────────────────────────────────────
@login_required
@requiere_habeas_data
def registrar_seguimiento(request):
    """
    Registro de un nuevo seguimiento de salud.
    Requiere Habeas Data aceptado.
    """
    if request.method == 'POST':
        form = SeguimientoSaludForm(request.POST)
        if form.is_valid():
            seguimiento = form.save(commit=False)
            seguimiento.usuario = request.user
            seguimiento.save()  # IMC se calcula en el save() del modelo

            categoria, color = seguimiento.get_categoria_imc()
            messages.success(
                request,
                f'✓ Seguimiento registrado. '
                f'Tu IMC es {seguimiento.imc} — {categoria}'
            )
            return redirect('habitos:historial_salud')
    else:
        form = SeguimientoSaludForm(
            initial={'fecha_evaluacion': timezone.now().date()})

    return render(request, 'habitos/salud.html', {
        'form': form,
        'titulo_pagina': 'Registrar Seguimiento de Salud',
        'vista': 'registrar',
    })


@login_required
@requiere_habeas_data
def historial_salud(request):
    """Historial completo de seguimientos del usuario con gráficas."""
    seguimientos = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).order_by('fecha_evaluacion')

    # Preparar datos JSON para Chart.js
    data_grafica = {
        'fechas': [str(s.fecha_evaluacion) for s in seguimientos],
        'pesos': [float(s.peso_kg) for s in seguimientos],
        'imcs': [float(s.imc) if s.imc else 0 for s in seguimientos],
        'fc': [s.frecuencia_cardiaca or 0 for s in seguimientos],
    }

    ultimo = seguimientos.last()
    primero = seguimientos.first()

    # Cambio de peso entre primer y último registro
    cambio_peso = None
    if ultimo and primero and ultimo != primero:
        cambio_peso = round(float(ultimo.peso_kg) - float(primero.peso_kg), 2)

    ctx = {
        'seguimientos': seguimientos,
        'ultimo': ultimo,
        'cambio_peso': cambio_peso,
        'data_json': json.dumps(data_grafica),
        'titulo_pagina': 'Mi Historial de Salud',
        'vista': 'historial',
    }
    return render(request, 'habitos/salud.html', ctx)


@login_required
def detalle_seguimiento(request, pk):
    """Detalle de un registro de seguimiento específico."""
    seguimiento = get_object_or_404(
        SeguimientoSalud,
        pk=pk,
        usuario=request.user  # Solo puede ver los propios
    )
    categoria, color = seguimiento.get_categoria_imc()

    return render(request, 'habitos/salud.html', {
        'seg': seguimiento,
        'categoria_imc': categoria,
        'color_imc': color,
        'titulo_pagina': f'Seguimiento — {seguimiento.fecha_evaluacion}',
        'vista': 'detalle',
    })


@login_required
@require_POST
def eliminar_seguimiento(request, pk):
    """Elimina un registro de seguimiento (solo el propio usuario)."""
    seguimiento = get_object_or_404(
        SeguimientoSalud, pk=pk, usuario=request.user
    )
    if request.method == 'POST':
        seguimiento.delete()
        messages.success(request, 'Registro eliminado correctamente.')
    return redirect('habitos:historial_salud')
