from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time, timedelta
from .models import Reserva, GimnasioConfig, FranjaHoraria


class GimnasioAppTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_gimnasio",
            password="password123",
            email="gimnasio@sena.edu.co",
            numero_documento="87654321",
            rol="aprendiz"
        )
        self.admin = self.User.objects.create_superuser(
            username="admin_gimnasio",
            password="adminpassword123",
            email="admingym@sena.edu.co",
            numero_documento="11223344",
            rol="admin"
        )
        self.config = GimnasioConfig.get_config()

    def test_gimnasio_configuracion_defecto(self):
        """Prueba que la configuración del gimnasio se cree con valores por defecto."""
        self.assertEqual(self.config.estado, "abierta")
        self.assertEqual(self.config.capacidad_maxima, 40)
        self.assertEqual(self.config.horario_apertura, "07:00")

    def test_creacion_reserva_gimnasio(self):
        """Prueba que un aprendiz pueda realizar un registro de reserva exitosamente."""
        ahora = timezone.localtime(timezone.now())
        reserva = Reserva.objects.create(
            usuario_solicitante=self.usuario,
            fecha_entrada=ahora.date(),
            hora_entrada=ahora.time(),
            tiempo_permanencia=60,
            hora_salida=ahora.time(),
            fecha_salida=ahora.date(),
            estado="Activa"
        )
        self.assertEqual(reserva.usuario_solicitante, self.usuario)
        self.assertEqual(reserva.estado, "Activa")
        self.assertEqual(reserva.tiempo_permanencia, 60)
        self.assertTrue(str(reserva).startswith(self.usuario.get_full_name()))

    def test_cp17_visualizacion_aforo_y_calculo_ocupacion(self):
        """CP-17: Validar correcta visualización de aforo y cálculo de ocupación en tiempo real."""
        franja = FranjaHoraria.objects.create(
            dia_semana="Lunes",
            hora_inicio=time(8, 0),
            hora_fin=time(9, 0),
            aforo_maximo=20,
            habilitada=True
        )
        ahora = timezone.localtime(timezone.now())
        Reserva.objects.create(
            usuario_solicitante=self.usuario,
            fecha_entrada=ahora.date(),
            hora_entrada=time(8, 0),
            tiempo_permanencia=60,
            hora_salida=time(9, 0),
            fecha_salida=ahora.date(),
            franja_horaria=franja,
            estado="Activa"
        )

        # Aprendiz consume endpoint de aforo y turnos
        self.client.login(username="aprendiz_gimnasio", password="password123")
        resp = self.client.get('/aforo/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['capacidad_maxima'], self.config.capacidad_maxima)
        self.assertGreaterEqual(data['ocupacion_actual'], 1)
        self.assertIn('cupos_disponibles', data)
        self.assertIn('turnos', data)
        self.assertTrue(len(data['turnos']) > 0)
        # Verificar cupos calculados en la franja
        turno_info = next((t for t in data['turnos'] if t['id'] == franja.id), None)
        self.assertIsNotNone(turno_info)
        self.assertEqual(turno_info['ocupados'], 1)
        self.assertEqual(turno_info['cupos_disponibles'], 19)

    def test_cp18_crud_franjas_horarias_admin(self):
        """CP-18: Validar operaciones CRUD de franjas horarias con permisos de Administrador."""
        # 1. Un aprendiz no puede crear franjas horarias
        self.client.login(username="aprendiz_gimnasio", password="password123")
        resp_unauth = self.client.post('/gimnasio/admin/franjas/', {
            'dia_semana': 'Martes',
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'aforo_maximo': 25
        })
        self.assertEqual(resp_unauth.status_code, 302)
        self.client.logout()

        # 2. Administrador crea franja horaria (CREATE)
        self.client.login(username="admin_gimnasio", password="adminpassword123")
        resp_create = self.client.post('/gimnasio/admin/franjas/', {
            'dia_semana': 'Martes',
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
            'aforo_maximo': 25
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_create.status_code, 201)
        franja_id = resp_create.json()['franja']['id']
        self.assertTrue(FranjaHoraria.objects.filter(id=franja_id).exists())

        # 3. Administrador consulta franjas horarias (READ)
        resp_read = self.client.get('/gimnasio/admin/franjas/')
        self.assertEqual(resp_read.status_code, 200)
        self.assertTrue(any(f['id'] == franja_id for f in resp_read.json()['franjas']))

        # 4. Administrador actualiza límite de aforo (UPDATE)
        resp_update = self.client.post(f'/gimnasio/admin/franjas/editar/{franja_id}/', {
            'aforo_maximo': 35
        })
        self.assertEqual(resp_update.status_code, 200)
        franja_actualizada = FranjaHoraria.objects.get(id=franja_id)
        self.assertEqual(franja_actualizada.aforo_maximo, 35)

        # 5. Administrador elimina la franja horaria (DELETE)
        resp_delete = self.client.post(f'/gimnasio/admin/franjas/eliminar/{franja_id}/')
        self.assertEqual(resp_delete.status_code, 200)
        self.assertFalse(FranjaHoraria.objects.filter(id=franja_id).exists())

    def test_cp19_integridad_y_control_sobrecupo_en_reservas(self):
        """CP-19: Validar integridad y control de sobrecupo en reservas."""
        # Franja con cupo de solo 1 persona
        franja_llena = FranjaHoraria.objects.create(
            dia_semana="Miercoles",
            hora_inicio=time(14, 0),
            hora_fin=time(15, 0),
            aforo_maximo=1,
            habilitada=True
        )
        ahora = timezone.localtime(timezone.now())

        # Aprendiz 1 reserva turno exitosamente (integridad referencial)
        self.client.login(username="aprendiz_gimnasio", password="password123")
        resp_reserva = self.client.post('/reserva/turno/', {
            'fecha_reserva': ahora.date().isoformat(),
            'franja_id': franja_llena.id
        })
        self.assertEqual(resp_reserva.status_code, 201)
        reserva = Reserva.objects.get(codigo_registro=resp_reserva.json()['reserva_id'])
        self.assertEqual(reserva.usuario_solicitante, self.usuario)
        self.assertEqual(reserva.franja_horaria, franja_llena)
        self.client.logout()

        # Aprendiz 2 intenta reservar el mismo turno con sobrecupo
        aprendiz_2 = self.User.objects.create_user(
            username="aprendiz_dos",
            password="password123",
            email="aprendiz2@sena.edu.co",
            numero_documento="99887766",
            rol="aprendiz"
        )
        self.client.login(username="aprendiz_dos", password="password123")
        resp_sobrecupo = self.client.post('/reserva/turno/', {
            'fecha_reserva': ahora.date().isoformat(),
            'franja_id': franja_llena.id
        })
        # Backend valida sobrecupo y rechaza con 400
        self.assertEqual(resp_sobrecupo.status_code, 400)
        self.assertEqual(resp_sobrecupo.json().get('codigo'), 'SOBRECUPO')
        self.assertIn('Sobrecupo', resp_sobrecupo.json().get('message', ''))
