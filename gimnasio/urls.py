from django.urls import path
from . import views

urlpatterns = [
    path('', views.gimnasio_list, name='gimnasio'),
    path('eliminar-reserva/<int:id>/',
         views.eliminar_reserva, name='eliminar_reserva'),
    path('editar-reserva/<int:id>/', views.editar_reserva, name='editar_reserva'),
    path('gimnasio/admin/', views.admin_disponibilidad,
         name='admin_disponibilidad'),
    path('gimnasio/admin/horarios/', views.admin_horarios, name='admin_horarios'),
    path('gimnasio/admin/fechas/', views.admin_fechas_ingreso,
         name='admin_fechas_ingreso'),
    path('gimnasio/admin/fechas/eliminar/<int:pk>/',
         views.admin_eliminar_fecha, name='admin_eliminar_fecha'),
    path('gimnasio/admin/configuracion/',
         views.admin_configuracion, name='admin_configuracion'),
    path('gimnasio/admin/nuevo-registro/',
         views.admin_nuevo_registro, name='admin_nuevo_registro'),
    path('gimnasio/admin/reservas/', views.admin_reservas, name='admin_reservas'),
    path('gimnasio/admin/cancelar/<int:id>/',
         views.cancelar_reserva_admin, name='cancelar_reserva_admin'),
    path('gimnasio/admin/cerrar/', views.cerrar_gimnasio, name='cerrar_gimnasio'),
    path('gimnasio/admin/anamnesis/', views.admin_lista_anamnesis,
         name='admin_lista_anamnesis'),

    # ── Máquinas y equipos ──
    path('maquinas/inventario/', views.MachineListView.as_view(), name='machine_list'),
    path('gimnasio/admin/maquinas/crear/',
         views.crear_maquina, name='crear_maquina'),
    path('gimnasio/admin/maquinas/editar/<int:pk>/',
         views.editar_maquina, name='editar_maquina'),
    path('gimnasio/admin/maquinas/eliminar/<int:pk>/',
         views.eliminar_maquina, name='eliminar_maquina'),
    path('gimnasio/admin/maquinas/estado/<int:pk>/',
         views.toggle_estado_maquina, name='toggle_estado_maquina'),

    # ── CP-17: Endpoint de aforo y turnos en tiempo real ──
    path('aforo/', views.api_aforo_turnos, name='gimnasio_aforo'),

    # ── CP-18: CRUD de franjas horarias (Solo Admin) ──
    path('gimnasio/admin/franjas/', views.admin_franjas_list_create, name='admin_franjas'),
    path('gimnasio/admin/franjas/editar/<int:pk>/', views.admin_franja_editar, name='admin_franja_editar'),
    path('gimnasio/admin/franjas/eliminar/<int:pk>/', views.admin_franja_eliminar, name='admin_franja_eliminar'),

    # ── CP-19: Reserva de turno con control de sobrecupo ──
    path('reserva/turno/', views.crear_reserva_turno, name='crear_reserva_turno'),
]