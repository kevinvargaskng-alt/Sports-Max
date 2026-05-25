# gimnasio/views.py
# ══════════════════════════════════════════════════════════════
#  VIEWS — Gimnasio completo
#  Ramas: admin (config, fechas, registros, anamnesis de todos)
#         aprendiz (ingreso, anamnesis propia, tests, rutinas)
# ══════════════════════════════════════════════════════════════

from django.shortcuts           import render, redirect, get_object_or_404
from django.contrib             import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils               import timezone
from django.db.models           import Count
import json

from .models  import (
    ConfiguracionGimnasio, FechaEspecial, RegistroIngreso,
    Anamnesis, TestFisico, Rutina, EjercicioRutina,
)
from .forms   import (
    AnamnesisForm, TestFisicoForm, RutinaForm, EjercicioFormSet,
)


# ─── helpers ────────────────────────────────────────────────
def es_admin(user):
    return user.is_staff or user.is_superuser

def _get_or_create_config():
    config, _ = ConfiguracionGimnasio.objects.get_or_create(pk=1)
    return config

DIAS_SEMANA = [
    {'codigo': 'lun', 'label': 'Lun'},
    {'codigo': 'mar', 'label': 'Mar'},
    {'codigo': 'mie', 'label': 'Mié'},
    {'codigo': 'jue', 'label': 'Jue'},
    {'codigo': 'vie', 'label': 'Vie'},
    {'codigo': 'sab', 'label': 'Sáb'},
    {'codigo': 'dom', 'label': 'Dom'},
]

def _esta_abierto(config):
    """Devuelve True si el gimnasio está abierto ahora mismo."""
    if config.estado != 'abierta':
        return False
    ahora = timezone.localtime(timezone.now())
    dia_actual = ['lun','mar','mie','jue','vie','sab','dom'][ahora.weekday()]
    if dia_actual not in config.dias_habilitados:
        return False
    hora_actual = ahora.time()
    return config.horario_apertura <= hora_actual <= config.horario_cierre


# ══════════════════════════════════════════════════════════════
#  VISTA PRINCIPAL — bifurca admin / aprendiz
# ══════════════════════════════════════════════════════════════
@login_required
def gimnasio_home(request):
    config   = _get_or_create_config()
    ahora    = timezone.localtime(timezone.now())
    esta_ab  = _esta_abierto(config)
    fechas   = FechaEspecial.objects.all()

    ctx = {
        'config':       config,
        'ahora':        ahora,
        'esta_abierto': esta_ab,
        'dias_semana':  DIAS_SEMANA,
        'dias_activos': config.dias_habilitados,
        'fechas':       fechas,
    }

    if request.user.is_staff or request.user.is_superuser:
        # ── ADMIN ──
        from django.contrib.auth import get_user_model
        User = get_user_model()
        ctx.update({
            'total_reservas':   RegistroIngreso.objects.count(),
            'reservas_hoy':     RegistroIngreso.objects.filter(fecha_entrada=ahora.date()).count(),
            'total_aprendices': User.objects.filter(is_staff=False, is_superuser=False).count(),
            'todas_reservas':   RegistroIngreso.objects.select_related('usuario').order_by('-fecha_entrada', '-hora_entrada'),
            'seccion_activa':   request.GET.get('sec', ''),
        })
        return render(request, 'gimnasio/gimnasio.html', ctx)

    # ── APRENDIZ ──
    if request.method == 'POST' and request.POST.get('accion') == 'crear_reserva':
        fecha_str = request.POST.get('fecha_entrada')
        hora_str  = request.POST.get('hora_entrada')
        if fecha_str and hora_str:
            from datetime import date, time as dtime
            fecha_obj = date.fromisoformat(fecha_str)
            h, m      = map(int, hora_str.split(':'))
            hora_obj  = dtime(h, m)
            RegistroIngreso.objects.create(
                usuario      = request.user,
                fecha_entrada= fecha_obj,
                hora_entrada = hora_obj,
            )
            messages.success(request, '✅ Ingreso registrado correctamente.')
        else:
            messages.error(request, '⚠️ Completa todos los campos.')
        return redirect('gimnasio_home')

    ctx.update({
        'reservas': RegistroIngreso.objects.filter(usuario=request.user).order_by('-fecha_entrada', '-hora_entrada')[:20],
    })
    return render(request, 'gimnasio/gimnasio.html', ctx)


# ══════════════════════════════════════════════════════════════
#  ADMIN — disponibilidad
# ══════════════════════════════════════════════════════════════
@login_required
@user_passes_test(es_admin)
def admin_disponibilidad(request):
    if request.method == 'POST':
        config = _get_or_create_config()
        config.estado            = request.POST.get('estado', 'abierta')
        config.horario_apertura  = request.POST.get('horario_apertura', '07:00')
        config.horario_cierre    = request.POST.get('horario_cierre',   '17:00')
        config.capacidad_maxima  = int(request.POST.get('capacidad_maxima', 40))
        dias_json                = request.POST.get('dias_json', '[]')
        try:
            config.dias_habilitados = json.loads(dias_json)
        except json.JSONDecodeError:
            config.dias_habilitados = []
        config.actualizado_por = request.user
        config.save()
        messages.success(request, '✅ Configuración actualizada.')
    return redirect(f'{__import__("django.urls", fromlist=["reverse"]).reverse("gimnasio_home")}?sec=disponibilidad')


# ══════════════════════════════════════════════════════════════
#  ADMIN — fechas especiales
# ══════════════════════════════════════════════════════════════
@login_required
@user_passes_test(es_admin)
def admin_fechas_ingreso(request):
    if request.method == 'POST':
        fecha_str   = request.POST.get('fecha')
        descripcion = request.POST.get('descripcion', '')
        habilitada  = request.POST.get('habilitada') == 'on'
        if fecha_str:
            from datetime import date
            FechaEspecial.objects.update_or_create(
                fecha       = date.fromisoformat(fecha_str),
                defaults    = {'descripcion': descripcion, 'habilitada': habilitada},
            )
            messages.success(request, '✅ Fecha especial guardada.')
        else:
            messages.error(request, '⚠️ Selecciona una fecha válida.')
    return redirect(f'{__import__("django.urls", fromlist=["reverse"]).reverse("gimnasio_home")}?sec=fechas')


@login_required
@user_passes_test(es_admin)
def admin_eliminar_fecha(request, pk):
    fecha = get_object_or_404(FechaEspecial, pk=pk)
    if request.method == 'POST':
        fecha.delete()
        messages.success(request, '🗑️ Fecha eliminada.')
    return redirect(f'{__import__("django.urls", fromlist=["reverse"]).reverse("gimnasio_home")}?sec=fechas')


# ══════════════════════════════════════════════════════════════
#  ELIMINAR REGISTRO (admin o el propio aprendiz)
# ══════════════════════════════════════════════════════════════
@login_required
def eliminar_reserva(request, codigo_registro):
    registro = get_object_or_404(RegistroIngreso, codigo_registro=codigo_registro)
    if request.user == registro.usuario or request.user.is_staff or request.user.is_superuser:
        registro.delete()
        messages.success(request, '🗑️ Registro eliminado.')
    else:
        messages.error(request, '⛔ Sin permisos.')
    return redirect('gimnasio_home')


# ══════════════════════════════════════════════════════════════
#  ANAMNESIS — crear / editar (aprendiz sobre sí mismo)
# ══════════════════════════════════════════════════════════════
@login_required
def anamnesis_propia(request):
    """Vista del aprendiz para ver/editar su propia anamnesis."""
    anamnesis = getattr(request.user, 'anamnesis', None)
    form = AnamnesisForm(request.POST or None, instance=anamnesis)

    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.usuario = request.user
        obj.save()
        messages.success(request, '✅ Ficha de salud actualizada. IMC calculado correctamente.')
        return redirect('anamnesis_propia')

    return render(request, 'gimnasio/anamnesis.html', {
        'form':      form,
        'anamnesis': anamnesis,
    })


# ── Admin: ver anamnesis de cualquier aprendiz ──────────────
@login_required
@user_passes_test(es_admin)
def admin_ver_anamnesis(request, usuario_id):
    from django.contrib.auth import get_user_model
    User  = get_user_model()
    aprendiz  = get_object_or_404(User, pk=usuario_id)
    anamnesis = getattr(aprendiz, 'anamnesis', None)
    return render(request, 'gimnasio/anamnesis_detalle.html', {
        'aprendiz':  aprendiz,
        'anamnesis': anamnesis,
    })


@login_required
@user_passes_test(es_admin)
def admin_lista_anamnesis(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    aprendices = User.objects.filter(
        is_staff=False, is_superuser=False
    ).prefetch_related('anamnesis').order_by('first_name', 'last_name')
    return render(request, 'gimnasio/lista_anamnesis.html', {'aprendices': aprendices})


# ══════════════════════════════════════════════════════════════
#  TESTS FÍSICOS
# ══════════════════════════════════════════════════════════════
@login_required
def tests_fisicos(request):
    """Aprendiz crea su propio test; ve su historial."""
    form = TestFisicoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.usuario = request.user
        obj.save()
        messages.success(request, f'✅ Test "{obj.get_tipo_display()}" registrado.')
        return redirect('tests_fisicos')

    mis_tests = TestFisico.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'gimnasio/tests_fisicos.html', {
        'form':      form,
        'mis_tests': mis_tests,
    })


@login_required
def eliminar_test(request, pk):
    test = get_object_or_404(TestFisico, pk=pk)
    if request.user == test.usuario or request.user.is_staff:
        test.delete()
        messages.success(request, '🗑️ Test eliminado.')
    return redirect('tests_fisicos')


# ── Admin: ver tests de cualquier aprendiz ──────────────────
@login_required
@user_passes_test(es_admin)
def admin_tests_aprendiz(request, usuario_id):
    from django.contrib.auth import get_user_model
    User     = get_user_model()
    aprendiz = get_object_or_404(User, pk=usuario_id)
    tests    = TestFisico.objects.filter(usuario=aprendiz).order_by('-fecha')
    return render(request, 'gimnasio/admin_tests.html', {
        'aprendiz': aprendiz,
        'tests':    tests,
    })


# ══════════════════════════════════════════════════════════════
#  RUTINAS
# ══════════════════════════════════════════════════════════════
@login_required
def mis_rutinas(request):
    """Aprendiz ve sus rutinas activas."""
    rutinas = Rutina.objects.filter(usuario=request.user, activa=True).prefetch_related('ejercicios')
    return render(request, 'gimnasio/rutinas_lista.html', {'rutinas': rutinas})


@login_required
def crear_rutina(request):
    """Aprendiz (o admin) crea una nueva rutina."""
    form      = RutinaForm(request.POST or None)
    formset   = EjercicioFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        rutina = form.save(commit=False)
        rutina.usuario     = request.user
        rutina.asignada_por = request.user
        rutina.save()
        formset.instance = rutina
        formset.save()
        messages.success(request, f'✅ Rutina "{rutina.nombre}" creada.')
        return redirect('mis_rutinas')

    return render(request, 'gimnasio/rutina_form.html', {
        'form':    form,
        'formset': formset,
        'titulo':  'Nueva Rutina',
    })


@login_required
def editar_rutina(request, pk):
    rutina  = get_object_or_404(Rutina, pk=pk)
    if request.user != rutina.usuario and not request.user.is_staff:
        messages.error(request, '⛔ Sin permisos.')
        return redirect('mis_rutinas')

    form    = RutinaForm(request.POST or None, instance=rutina)
    formset = EjercicioFormSet(request.POST or None, instance=rutina)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, '✅ Rutina actualizada.')
        return redirect('mis_rutinas')

    return render(request, 'gimnasio/rutina_form.html', {
        'form':    form,
        'formset': formset,
        'titulo':  f'Editar: {rutina.nombre}',
        'rutina':  rutina,
    })


@login_required
def eliminar_rutina(request, pk):
    rutina = get_object_or_404(Rutina, pk=pk)
    if request.user == rutina.usuario or request.user.is_staff:
        rutina.activa = False   # soft delete
        rutina.save()
        messages.success(request, '🗑️ Rutina archivada.')
    return redirect('mis_rutinas')


# ── Admin: asignar rutina a un aprendiz ──────────────────────
@login_required
@user_passes_test(es_admin)
def admin_asignar_rutina(request, usuario_id):
    from django.contrib.auth import get_user_model
    User     = get_user_model()
    aprendiz = get_object_or_404(User, pk=usuario_id)
    form     = RutinaForm(request.POST or None)
    formset  = EjercicioFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        rutina = form.save(commit=False)
        rutina.usuario      = aprendiz
        rutina.asignada_por = request.user
        rutina.save()
        formset.instance = rutina
        formset.save()
        messages.success(request, f'✅ Rutina asignada a {aprendiz.get_full_name()}.')
        return redirect('admin_lista_anamnesis')

    return render(request, 'gimnasio/rutina_form.html', {
        'form':    form,
        'formset': formset,
        'titulo':  f'Asignar Rutina → {aprendiz.get_full_name()}',
        'aprendiz': aprendiz,
    })