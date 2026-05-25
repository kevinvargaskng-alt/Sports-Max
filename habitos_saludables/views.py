"""
views.py - Vistas del módulo Hábitos Saludables SENA
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
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
    """Decorador: redirige al formulario de Habeas Data si no ha sido aceptado."""
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
    """Página principal del módulo."""
    habitos_destacados = HabitoSaludable.objects.filter(activo=True)[:6]
    rutinas_recientes = RutinaFisica.objects.filter(activo=True)[:3]
    materiales_recientes = MaterialApoyo.objects.filter(activo=True)[:4]

    ultimo_seguimiento = SeguimientoSalud.objects.filter(usuario=request.user).first()

    ctx = {
        'habitos': habitos_destacados,
        'rutinas': rutinas_recientes,
        'materiales': materiales_recientes,
        'ultimo_seguimiento': ultimo_seguimiento,
        'tiene_consent': tiene_habeas_data(request.user),
        'titulo_pagina': 'Inicio — Hábitos Saludables',
        'vista': 'inicio',
    }
    return render(request, 'habitos/inicio_dashboard.html', ctx)


@login_required
def dashboard(request):
    """Dashboard personal de salud y bienestar."""
    seguimientos = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).order_by('fecha_evaluacion')

    fechas = [str(s.fecha_evaluacion) for s in seguimientos]
    pesos = [float(s.peso_kg) for s in seguimientos]
    imcs = [float(s.imc) if s.imc else None for s in seguimientos]

    ultimo = seguimientos.last()
    categoria_imc = ultimo.get_categoria_imc() if ultimo else ('Sin datos', 'secondary')

    ctx = {
        'seguimientos': seguimientos,
        'ultimo': ultimo,
        'categoria_imc': categoria_imc,
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
    """Formulario de Habeas Data."""
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
            obj, _ = HabeasDataConsent.objects.get_or_create(usuario=request.user)
            obj.acepta = True
            obj.direccion_ip = get_client_ip(request)
            obj.save()
            messages.success(request, '✓ Has aceptado el tratamiento de datos.')
            return redirect('habitos:dashboard')
    else:
        form = HabeasDataForm()

    return render(request, 'habitos/salud.html', {
        'form': form,
        'titulo_pagina': 'Autorización Habeas Data',
        'vista': 'habeas_data'
    })


# ─────────────────────────────────────────────
# CONTENIDO EDUCATIVO
# ─────────────────────────────────────────────
@login_required
def lista_habitos(request):
    categoria = request.GET.get('categoria', '')
    habitos = HabitoSaludable.objects.filter(activo=True)

    if categoria:
        habitos = habitos.filter(categoria=categoria)

    ctx = {
        'habitos': habitos,
        'categorias': HabitoSaludable.CATEGORIA_CHOICES,
        'categoria_activa': categoria,
        'titulo_pagina': 'Hábitos Saludables',
        'vista': 'habitos'
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def detalle_habito(request, pk):
    habito = get_object_or_404(HabitoSaludable, pk=pk, activo=True)
    relacionados = HabitoSaludable.objects.filter(
        categoria=habito.categoria, activo=True
    ).exclude(pk=pk)[:3]

    return render(request, 'habitos/detalle_habito.html', {
        'habito': habito,
        'relacionados': relacionados,
        'titulo_pagina': habito.titulo,
    })


@login_required
def lista_rutinas(request):
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
        'vista': 'rutinas'   # Si usas contenido_educativo.html
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def detalle_rutina(request, pk):
    rutina = get_object_or_404(RutinaFisica, pk=pk, activo=True)
    return render(request, 'habitos/contenido_educativo.html', {
        'rutina': rutina,
        'titulo_pagina': rutina.nombre,
        'vista': 'detalle_rutina'
    })


@login_required
def piramide_nutricional(request):
    categoria = request.GET.get('categoria', '')
    alimentos = PiramideNutricional.objects.filter(activo=True)

    if categoria:
        alimentos = alimentos.filter(categoria=categoria)

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
        'vista': 'nutricion'
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


@login_required
def biblioteca(request):
    form = BuscarMaterialForm(request.GET)
    materiales = MaterialApoyo.objects.filter(activo=True)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        tipo = form.cleaned_data.get('tipo')
        if q:
            materiales = materiales.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
        if tipo:
            materiales = materiales.filter(tipo_contenido=tipo)

    ctx = {
        'materiales': materiales,
        'form': form,
        'total': materiales.count(),
        'titulo_pagina': 'Biblioteca de Materiales',
        'vista': 'biblioteca'
    }
    return render(request, 'habitos/contenido_educativo.html', ctx)


# ─────────────────────────────────────────────
# MATERIAL DE APOYO
# ─────────────────────────────────────────────
@login_required
def descargar_material(request, pk):
    material = get_object_or_404(MaterialApoyo, pk=pk, activo=True)

    if material.tipo_contenido == 'video':
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
    if request.method == 'POST':
        form = SeguimientoSaludForm(request.POST)
        if form.is_valid():
            seguimiento = form.save(commit=False)
            seguimiento.usuario = request.user
            seguimiento.save()
            messages.success(request, f'✓ Seguimiento registrado. IMC: {seguimiento.imc}')
            return redirect('habitos:historial_salud')
    else:
        form = SeguimientoSaludForm(initial={'fecha_evaluacion': timezone.now().date()})

    return render(request, 'habitos/salud.html', {
        'form': form,
        'titulo_pagina': 'Registrar Seguimiento de Salud',
        'vista': 'registrar'
    })


@login_required
@requiere_habeas_data
def historial_salud(request):
    seguimientos = SeguimientoSalud.objects.filter(usuario=request.user).order_by('fecha_evaluacion')

    ultimo = seguimientos.last()
    primero = seguimientos.first()
    cambio_peso = None
    if ultimo and primero and ultimo != primero:
        cambio_peso = round(float(ultimo.peso_kg) - float(primero.peso_kg), 2)

    ctx = {
        'seguimientos': seguimientos,
        'ultimo': ultimo,
        'cambio_peso': cambio_peso,
        'titulo_pagina': 'Mi Historial de Salud',
        'vista': 'historial'
    }
    return render(request, 'habitos/salud.html', ctx)


@login_required
def detalle_seguimiento(request, pk):
    seguimiento = get_object_or_404(SeguimientoSalud, pk=pk, usuario=request.user)
    return render(request, 'habitos/salud.html', {   # o crea detalle_seguimiento.html
        'seg': seguimiento,
        'titulo_pagina': f'Seguimiento — {seguimiento.fecha_evaluacion}',
        'vista': 'detalle'
    })


@login_required
def eliminar_seguimiento(request, pk):
    seguimiento = get_object_or_404(SeguimientoSalud, pk=pk, usuario=request.user)
    if request.method == 'POST':
        seguimiento.delete()
        messages.success(request, 'Registro eliminado correctamente.')
    return redirect('habitos:historial_salud')