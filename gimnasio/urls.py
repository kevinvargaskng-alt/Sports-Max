# gimnasio/urls.py
# ══════════════════════════════════════════════════════════════
#  URL CONF — Gimnasio completo
#  Incluye rutas de: acceso, anamnesis, tests físicos, rutinas
# ══════════════════════════════════════════════════════════════

from django.urls import path
from . import views

urlpatterns = [

    # ── PRINCIPAL (bifurca admin / aprendiz en la view) ──────
    path('',  views.gimnasio_home,  name='gimnasio_home'),

    # ── ADMIN: config disponibilidad ─────────────────────────
    path('admin/disponibilidad/',
         views.admin_disponibilidad,  name='admin_disponibilidad'),

    # ── ADMIN: fechas especiales ──────────────────────────────
    path('admin/fechas/',
         views.admin_fechas_ingreso,  name='admin_fechas_ingreso'),
    path('admin/fechas/<int:pk>/eliminar/',
         views.admin_eliminar_fecha,  name='admin_eliminar_fecha'),

    # ── REGISTRO DE INGRESO ───────────────────────────────────
    path('registro/<uuid:codigo_registro>/eliminar/',
         views.eliminar_reserva,      name='eliminar_reserva'),

    # ── ANAMNESIS ─────────────────────────────────────────────
    path('mi-ficha/',
         views.anamnesis_propia,      name='anamnesis_propia'),
    path('admin/anamnesis/',
         views.admin_lista_anamnesis, name='admin_lista_anamnesis'),
    path('admin/anamnesis/<int:usuario_id>/',
         views.admin_ver_anamnesis,   name='admin_ver_anamnesis'),

    # ── TESTS FÍSICOS ─────────────────────────────────────────
    path('tests/',
         views.tests_fisicos,         name='tests_fisicos'),
    path('tests/<int:pk>/eliminar/',
         views.eliminar_test,         name='eliminar_test'),
    path('admin/tests/<int:usuario_id>/',
         views.admin_tests_aprendiz,  name='admin_tests_aprendiz'),

    # ── RUTINAS ───────────────────────────────────────────────
    path('rutinas/',
         views.mis_rutinas,           name='mis_rutinas'),
    path('rutinas/nueva/',
         views.crear_rutina,          name='crear_rutina'),
    path('rutinas/<int:pk>/editar/',
         views.editar_rutina,         name='editar_rutina'),
    path('rutinas/<int:pk>/archivar/',
         views.eliminar_rutina,       name='eliminar_rutina'),
    path('admin/rutinas/<int:usuario_id>/asignar/',
         views.admin_asignar_rutina,  name='admin_asignar_rutina'),
]