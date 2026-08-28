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
    SeguimientoSalud, HabeasDataConsent, RutinaFisica,
    # CP-09: Nuevos modelos
    RecetaSaludable, RegistroHabitoUsuario, RegistroSueno,
    SuscripcionPush, RegistroSesionRutina,
)
from .forms import (
    SeguimientoSaludForm, MaterialApoyoForm,
    BuscarMaterialForm, HabeasDataForm
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def tiene_habeas_data(user):
    """Verifica si el usuario ha aceptado el Habeas Data o genera el registro automáticamente."""
    if not user.is_authenticated:
        return False
    try:
        return user.habeas_data.acepta
    except (HabeasDataConsent.DoesNotExist, AttributeError):
        try:
            consent, _ = HabeasDataConsent.objects.get_or_create(usuario=user, defaults={'acepta': True})
            return consent.acepta
        except Exception:
            return True


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
        'fechas': fechas,
        'pesos': pesos,
        'imcs': imcs,
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
            context = {
                'consent': consent,
                'titulo_pagina': 'Habeas Data — Aceptado'
            }
            return render(request, 'habitos/habeas_data_ok.html', context)
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

    context = {
        'form': form,
        'titulo_pagina': 'Autorización Habeas Data',
        'vista': 'habeas_data',
    }
    return render(request, 'habitos/salud.html', context)


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

    context = {
        'habito': habito,
        'relacionados': relacionados,
        'titulo_pagina': habito.titulo,
        'vista': 'detalle_habito',
    }
    return render(request, 'habitos/contenido_educativo.html', context)


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
    context = {
        'rutina': rutina,
        'titulo_pagina': rutina.nombre,
        'vista': 'detalle_rutina',
    }
    return render(request, 'habitos/contenido_educativo.html', context)


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

    context = {
        'form': form,
        'titulo_pagina': 'Registrar Seguimiento de Salud',
        'vista': 'registrar',
    }
    return render(request, 'habitos/salud.html', context)


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

    context = {
        'seg': seguimiento,
        'categoria_imc': categoria,
        'color_imc': color,
        'titulo_pagina': f'Seguimiento — {seguimiento.fecha_evaluacion}',
        'vista': 'detalle',
    }
    return render(request, 'habitos/salud.html', context)


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


# =============================================================
# CP-10: API CÁLCULO DE IMC Y REQUERIMIENTOS CALÓRICOS
# =============================================================
@login_required
@require_POST
def calcular_imc_api(request):
    """
    POST /habitos/api/calcular-imc/
    Payload JSON: { peso_kg, estatura_cm, edad, genero, nivel_actividad }
    Formula: Mifflin-St Jeor
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST.dict()

    try:
        peso = float(data.get('peso_kg', 0))
        estatura = float(data.get('estatura_cm', 0))
        edad = int(data.get('edad', 0))
        genero = data.get('genero', 'M')
        nivel_actividad = data.get('nivel_actividad', 'sedentario')
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)

    # Validaciones de rango
    errores = []
    if not (20 <= peso <= 300):
        errores.append('El peso debe estar entre 20 y 300 kg.')
    if not (100 <= estatura <= 250):
        errores.append('La estatura debe estar entre 100 y 250 cm.')
    if not (10 <= edad <= 120):
        errores.append('La edad debe estar entre 10 y 120 años.')
    if errores:
        return JsonResponse({'error': errores}, status=400)

    # Calcular IMC
    estatura_m = estatura / 100
    imc = round(peso / (estatura_m ** 2), 2)

    if imc < 18.5:
        categoria_imc = 'Bajo peso'
    elif imc < 25:
        categoria_imc = 'Peso normal'
    elif imc < 30:
        categoria_imc = 'Sobrepeso'
    else:
        categoria_imc = 'Obesidad'

    # Tasa Metabólica Basal (Mifflin-St Jeor)
    if genero == 'M':
        tmb = (10 * peso) + (6.25 * estatura) - (5 * edad) + 5
    else:
        tmb = (10 * peso) + (6.25 * estatura) - (5 * edad) - 161

    factores = {
        'sedentario':  1.2,
        'ligero':      1.375,
        'moderado':    1.55,
        'activo':      1.725,
        'muy_activo':  1.9,
    }
    factor = factores.get(nivel_actividad, 1.2)
    calorias_objetivo = int(tmb * factor)

    # Macros (30% proteínas, 40% carbos, 30% grasas)
    macros = {
        'proteinas_g':      int(calorias_objetivo * 0.30 / 4),
        'carbohidratos_g':  int(calorias_objetivo * 0.40 / 4),
        'grasas_g':         int(calorias_objetivo * 0.30 / 9),
    }

    # Guardar en SeguimientoSalud si los datos biométricos cambiaron
    try:
        from decimal import Decimal
        ultimo = SeguimientoSalud.objects.filter(usuario=request.user).order_by('-fecha_evaluacion').first()
        if not ultimo or float(ultimo.peso_kg) != peso or float(ultimo.estatura_cm) != estatura:
            SeguimientoSalud.objects.create(
                usuario=request.user,
                peso_kg=Decimal(str(peso)),
                estatura_cm=Decimal(str(estatura)),
                nivel_actividad=nivel_actividad,
            )
    except Exception:
        pass  # No interrumpir la respuesta por error de guardado

    return JsonResponse({
        'imc':               imc,
        'categoria_imc':     categoria_imc,
        'calorias_base':     int(tmb),
        'calorias_objetivo': calorias_objetivo,
        'factor_actividad':  factor,
        'macros':            macros,
    })


@login_required
def vista_calcular_imc(request):
    """GET /habitos/calcular-imc/ — Renderiza el formulario de IMC."""
    ultimo_seguimiento = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).order_by('-fecha_evaluacion').first()
    return render(request, 'habitos/calcular_imc.html', {
        'ultimo_seguimiento': ultimo_seguimiento,
    })


# =============================================================
# CP-13: RECETAS SALUDABLES
# =============================================================
def lista_recetas(request):
    """GET /habitos/recetas/ — Listado público de recetas."""
    qs = RecetaSaludable.objects.filter(activa=True)

    categoria = request.GET.get('categoria', '')
    objetivo  = request.GET.get('objetivo', '')
    q         = request.GET.get('q', '').strip()

    if categoria:
        qs = qs.filter(categoria=categoria)
    if objetivo:
        qs = qs.filter(objetivo=objetivo)
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))

    return render(request, 'habitos/recetas_lista.html', {
        'recetas': qs,
        'categoria_actual': categoria,
        'objetivo_actual':  objetivo,
        'q': q,
        'categorias': RecetaSaludable.CATEGORIA_CHOICES,
        'objetivos':  RecetaSaludable.OBJETIVO_CHOICES,
    })


def detalle_receta(request, pk):
    """GET /habitos/recetas/<pk>/ — Detalle de una receta."""
    receta = get_object_or_404(RecetaSaludable, pk=pk, activa=True)
    return render(request, 'habitos/receta_detalle.html', {'receta': receta})


@login_required
def crear_receta(request):
    """GET/POST /habitos/recetas/nueva/ — Solo nutricionistas/admin."""
    from core.permisos import es_profesional_salud
    from django.core.exceptions import PermissionDenied
    if not (es_profesional_salud(request.user) or request.user.is_superuser):
        raise PermissionDenied

    if request.method == 'POST':
        campos = ['titulo', 'descripcion', 'ingredientes', 'preparacion',
                  'tiempo_preparacion_min', 'porciones', 'categoria', 'objetivo',
                  'calorias_por_porcion', 'proteinas_g', 'carbohidratos_g', 'grasas_g']
        datos = {c: request.POST.get(c, '') for c in campos}
        datos['autor'] = request.user
        datos['activa'] = True
        if 'imagen' in request.FILES:
            datos['imagen'] = request.FILES['imagen']
        try:
            # Convertir nulos
            for campo_num in ['calorias_por_porcion', 'proteinas_g', 'carbohidratos_g', 'grasas_g']:
                if not datos[campo_num]:
                    datos[campo_num] = None
            receta = RecetaSaludable.objects.create(**datos)
            messages.success(request, f'Receta "{receta.titulo}" creada exitosamente.')
            return redirect('habitos:detalle_receta', pk=receta.pk)
        except Exception as e:
            messages.error(request, f'Error al guardar la receta: {e}')

    return render(request, 'habitos/receta_form.html', {
        'accion': 'Crear',
        'categorias': RecetaSaludable.CATEGORIA_CHOICES,
        'objetivos':  RecetaSaludable.OBJETIVO_CHOICES,
    })


@login_required
def editar_receta(request, pk):
    """GET/POST /habitos/recetas/<pk>/editar/ — Solo nutricionistas/admin."""
    from core.permisos import es_profesional_salud
    from django.core.exceptions import PermissionDenied
    if not (es_profesional_salud(request.user) or request.user.is_superuser):
        raise PermissionDenied

    receta = get_object_or_404(RecetaSaludable, pk=pk)
    if request.method == 'POST':
        campos = ['titulo', 'descripcion', 'ingredientes', 'preparacion',
                  'tiempo_preparacion_min', 'porciones', 'categoria', 'objetivo',
                  'calorias_por_porcion', 'proteinas_g', 'carbohidratos_g', 'grasas_g']
        for c in campos:
            val = request.POST.get(c)
            if val is not None:
                setattr(receta, c, val if val else None)
        if 'imagen' in request.FILES:
            receta.imagen = request.FILES['imagen']
        try:
            receta.save()
            messages.success(request, f'Receta "{receta.titulo}" actualizada.')
            return redirect('habitos:detalle_receta', pk=receta.pk)
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

    return render(request, 'habitos/receta_form.html', {
        'receta': receta,
        'accion': 'Editar',
        'categorias': RecetaSaludable.CATEGORIA_CHOICES,
        'objetivos':  RecetaSaludable.OBJETIVO_CHOICES,
    })


# =============================================================
# CP-11: SEGUIMIENTO DE RUTINAS DE EJERCICIO
# =============================================================
@login_required
def mis_rutinas(request):
    """GET /habitos/mis-rutinas/ — Panel de rutinas del usuario."""
    from datetime import date, timedelta
    hoy = date.today()

    rutinas = RutinaFisica.objects.filter(activo=True)

    # Sesiones de los últimos 7 días
    hace_7 = hoy - timedelta(days=6)
    sesiones_semana = RegistroSesionRutina.objects.filter(
        usuario=request.user,
        fecha__gte=hace_7,
    ).order_by('-fecha')

    # Calcular racha (días consecutivos completados)
    racha = 0
    dia_check = hoy
    while True:
        completado_hoy = RegistroSesionRutina.objects.filter(
            usuario=request.user, fecha=dia_check, completado=True
        ).exists()
        if completado_hoy:
            racha += 1
            dia_check -= timedelta(days=1)
        else:
            break

    # Días de la última semana para el historial visual
    dias_semana = []
    for i in range(6, -1, -1):
        d = hoy - timedelta(days=i)
        sesion = RegistroSesionRutina.objects.filter(
            usuario=request.user, fecha=d
        ).first()
        dias_semana.append({
            'fecha': d,
            'dia': d.strftime('%a'),
            'sesion': sesion,
            'completado': sesion.completado if sesion else None,
        })

    return render(request, 'habitos/mis_rutinas.html', {
        'rutinas': rutinas,
        'sesiones_semana': sesiones_semana,
        'dias_semana': dias_semana,
        'racha': racha,
        'hoy': hoy,
    })


@login_required
@require_POST
def registrar_sesion(request):
    """POST /habitos/api/registrar-sesion/ — Guarda sesión de rutina."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST.dict()

    rutina_id      = data.get('rutina_id')
    fecha_str      = data.get('fecha', str(timezone.now().date()))
    duracion       = int(data.get('duracion_real_min', 0))
    completado     = data.get('completado', True)
    nivel_esfuerzo = int(data.get('nivel_esfuerzo', 3))
    notas          = data.get('notas', '')

    rutina = get_object_or_404(RutinaFisica, pk=rutina_id)

    from datetime import date as date_type
    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha = timezone.now().date()

    sesion, creada = RegistroSesionRutina.objects.update_or_create(
        usuario=request.user, rutina=rutina, fecha=fecha,
        defaults={
            'duracion_real_min': duracion,
            'completado': completado,
            'nivel_esfuerzo': nivel_esfuerzo,
            'notas': notas,
        }
    )

    return JsonResponse({
        'ok': True,
        'sesion_id': sesion.pk,
        'creada': creada,
        'completado': sesion.completado,
    })


# =============================================================
# CP-15: GRÁFICA DE SUEÑO SEMANAL
# =============================================================
@login_required
def grafica_sueno(request):
    """GET /habitos/sueno/ — Vista con la gráfica de sueño."""
    return render(request, 'habitos/grafica_sueno.html')


@login_required
def api_sueno_semanal(request):
    """GET /habitos/api/sueno-semanal/ — Datos JSON para la gráfica."""
    from datetime import date, timedelta
    hoy = date.today()

    DIAS_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    labels = []
    horas_lista = []

    for i in range(6, -1, -1):
        d = hoy - timedelta(days=i)
        labels.append(DIAS_ES[d.weekday()])
        registro = RegistroSueno.objects.filter(usuario=request.user, fecha=d).first()
        horas_lista.append(float(registro.horas) if registro else None)

    horas_validas = [h for h in horas_lista if h is not None]
    promedio = round(sum(horas_validas) / len(horas_validas), 1) if horas_validas else 0
    dias_optimos = sum(1 for h in horas_validas if 7 <= h <= 9)

    return JsonResponse({
        'labels': labels,
        'horas': horas_lista,
        'promedio': promedio,
        'recomendacion': 'Se recomienda dormir entre 7 y 9 horas para adultos jóvenes (OMS).',
        'dias_optimos': dias_optimos,
    })


@login_required
@require_POST
def registrar_sueno(request):
    """POST /habitos/api/registrar-sueno/ — Crea o actualiza RegistroSueno."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST.dict()

    fecha_str = data.get('fecha', str(timezone.now().date()))
    horas_raw = data.get('horas', '0')
    calidad   = int(data.get('calidad', 3))
    nota      = data.get('nota', '')

    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        horas = float(horas_raw)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)

    if not (0 <= horas <= 24):
        return JsonResponse({'error': 'Las horas deben estar entre 0 y 24.'}, status=400)

    from decimal import Decimal
    registro, creado = RegistroSueno.objects.update_or_create(
        usuario=request.user,
        fecha=fecha,
        defaults={'horas': Decimal(str(horas)), 'calidad': calidad, 'nota': nota},
    )

    return JsonResponse({
        'ok': True,
        'horas': float(registro.horas),
        'es_optimo': registro.es_optimo,
        'categoria': registro.categoria_texto,
        'creado': creado,
    })


# =============================================================
# CP-12: NOTIFICACIONES PUSH
# =============================================================
@login_required
def configurar_notificaciones(request):
    """GET /habitos/notificaciones/ — Página de configuración de push."""
    suscripcion_activa = SuscripcionPush.objects.filter(
        usuario=request.user, activa=True
    ).exists()
    return render(request, 'habitos/configurar_notificaciones.html', {
        'suscripcion_activa': suscripcion_activa,
    })


@login_required
@require_POST
def guardar_suscripcion_push(request):
    """POST /habitos/api/guardar-suscripcion/ — Guarda endpoint de push."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    endpoint = data.get('endpoint', '')
    p256dh   = data.get('keys', {}).get('p256dh', '')
    auth_key = data.get('keys', {}).get('auth', '')

    if not all([endpoint, p256dh, auth_key]):
        return JsonResponse({'error': 'Faltan campos de suscripción.'}, status=400)

    # Desactivar suscripciones previas
    SuscripcionPush.objects.filter(usuario=request.user).update(activa=False)

    SuscripcionPush.objects.create(
        usuario=request.user,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth_key,
        activa=True,
    )
    return JsonResponse({'ok': True, 'mensaje': 'Suscripción registrada correctamente.'})


# =============================================================
# CP-14: DASHBOARD DE PROGRESO
# =============================================================
@login_required
def dashboard_progreso(request):
    """GET /habitos/mi-progreso/ — Dashboard con métricas del usuario."""
    from datetime import date, timedelta
    from django.db.models import Avg, Count, Sum

    hoy = date.today()
    hace_30 = hoy - timedelta(days=29)
    hace_7  = hoy - timedelta(days=6)

    # ── IMC y seguimiento ────────────────────────────────────
    ultimo_seguimiento = SeguimientoSalud.objects.filter(
        usuario=request.user
    ).order_by('-fecha_evaluacion').first()

    seguimientos_30d = SeguimientoSalud.objects.filter(
        usuario=request.user,
        fecha_evaluacion__gte=hace_30
    ).order_by('fecha_evaluacion')

    # ── Sueño ────────────────────────────────────────────────
    registros_sueno = RegistroSueno.objects.filter(
        usuario=request.user,
        fecha__gte=hace_7
    ).order_by('fecha')
    promedio_sueno = registros_sueno.aggregate(p=Avg('horas'))['p'] or 0

    # ── Racha de hábitos ────────────────────────────────────
    racha = 0
    dia_check = hoy
    while True:
        if RegistroSesionRutina.objects.filter(
            usuario=request.user, fecha=dia_check, completado=True
        ).exists():
            racha += 1
            dia_check -= timedelta(days=1)
        else:
            break

    # ── Sesiones de ejercicio (últimas 4 semanas, por semana) ─
    sesiones_4s = []
    for i in range(3, -1, -1):
        ini = hoy - timedelta(weeks=i+1)
        fin = hoy - timedelta(weeks=i)
        cnt = RegistroSesionRutina.objects.filter(
            usuario=request.user, fecha__gte=ini, fecha__lt=fin, completado=True
        ).count()
        sesiones_4s.append({'label': f'Sem -{i+1}', 'count': cnt})

    # ── Actividad reciente ───────────────────────────────────
    actividad_reciente = list(
        RegistroSesionRutina.objects.filter(
            usuario=request.user
        ).order_by('-fecha_registro')[:5]
    )

    # Datos de evolución de peso para el gráfico
    pesos_labels = [str(s.fecha_evaluacion) for s in seguimientos_30d]
    pesos_data   = [float(s.peso_kg) for s in seguimientos_30d]

    return render(request, 'habitos/dashboard_progreso.html', {
        'ultimo_seguimiento':  ultimo_seguimiento,
        'promedio_sueno':      round(float(promedio_sueno), 1),
        'racha':               racha,
        'sesiones_4s':         sesiones_4s,
        'actividad_reciente':  actividad_reciente,
        'pesos_labels':        json.dumps(pesos_labels),
        'pesos_data':          json.dumps(pesos_data),
        'sesiones_labels':     json.dumps([s['label'] for s in sesiones_4s]),
        'sesiones_data':       json.dumps([s['count'] for s in sesiones_4s]),
    })
