from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion

class InventarioAppTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_inventario",
            password="password123",
            email="inventario@sena.edu.co",
            numero_documento="55554444"
        )
        self.elemento = ElementoDeportivo.objects.create(
            tipo_maquina="Balón de Fútbol N° 5",
            cantidad_total=5,
            estado_general="Excelente",
            descripcion="Balón reglamentario de cuero sintético."
        )

    def test_creacion_elemento_deportivo(self):
        """Prueba la creación del implemento deportivo."""
        elem = ElementoDeportivo.objects.get(pk=self.elemento.pk)
        self.assertEqual(elem.tipo_maquina, "Balón de Fútbol N° 5")
        self.assertEqual(elem.cantidad_total, 5)

    def test_prestamo_elemento(self):
        """Prueba la solicitud de préstamo de un implemento deportivo."""
        prestamo = Prestamo.objects.create(
            usuario=self.usuario,
            elemento=self.elemento,
            cantidad_prestada=1,
            dias_prestamo=2,
            estado_prestamo="Activo"
        )
        self.assertEqual(prestamo.usuario, self.usuario)
        self.assertEqual(prestamo.elemento, self.elemento)
        self.assertEqual(prestamo.cantidad_prestada, 1)
        self.assertEqual(prestamo.estado_prestamo, "Activo")

    def test_devolucion_y_sancion(self):
        """Prueba el registro de devolución y la creación de una sanción."""
        prestamo = Prestamo.objects.create(
            usuario=self.usuario,
            elemento=self.elemento,
            cantidad_prestada=1,
            dias_prestamo=1,
            estado_prestamo="Activo"
        )
        devolucion = Devolucion.objects.create(
            prestamo=prestamo,
            cantidad_devuelta=1,
            tiene_novedad=True,
            tipo_novedad_devolucion="Pérdida",
            estado_elemento_devolucion="Perdido",
            observaciones_devolucion="El aprendiz reporta pérdida del balón en el campo."
        )
        self.assertEqual(devolucion.prestamo, prestamo)
        self.assertTrue(devolucion.tiene_novedad)

        sancion = Sancion.objects.create(
            usuario=self.usuario,
            devolucion=devolucion,
            tipo_sancion="Suspensión Temporal",
            fecha_inicio_sancion=date.today(),
            fecha_fin_sancion=date.today(),
            estado_sancion="Activa",
            descripcion_sancion="Sanción por pérdida de elemento deportivo."
        )
        self.assertEqual(sancion.usuario, self.usuario)
        self.assertEqual(sancion.devolucion, devolucion)
        self.assertEqual(sancion.estado_sancion, "Activa")

    def test_cp21_reporte_prestamos_vencidos_y_bloqueo_morosos(self):
        """CP-21: Validar consulta de préstamos vencidos (cruce Prestamo-Usuario) y ejecución de bloqueos."""
        from datetime import timedelta

        # Crear usuario Administrador
        admin = self.User.objects.create_user(
            username="admin_inventario",
            password="password123",
            email="admin_inv@sena.edu.co",
            numero_documento="99998888",
            rol="administrador",
            is_staff=True
        )

        # Crear un préstamo vencido para el usuario aprendiz
        hoy = timezone.localdate()
        fecha_limite = hoy - timedelta(days=5)
        prestamo_vencido = Prestamo.objects.create(
            usuario=self.usuario,
            elemento=self.elemento,
            cantidad_prestada=2,
            dias_prestamo=3,
            fecha_devolucion=fecha_limite,
            estado_prestamo="Activo"
        )

        # 1. Validación de permisos: Usuario aprendiz no puede consultar el reporte administrativo
        self.client.login(username="aprendiz_inventario", password="password123")
        resp_no_admin = self.client.get('/inventario/reportes/morosos/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_no_admin.status_code, 403)

        # 2. Como Administrador, consultar reporte cruzando las tablas Prestamo y Usuario
        self.client.login(username="admin_inventario", password="password123")
        resp_admin = self.client.get('/inventario/reportes/morosos/?format=json')
        self.assertEqual(resp_admin.status_code, 200)
        data = resp_admin.json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['total_morosos'], 1)

        # Validar cruce de datos entre Prestamos y Usuarios
        moroso = next((m for m in data['morosos'] if m['usuario_id'] == self.usuario.id), None)
        self.assertIsNotNone(moroso)
        self.assertEqual(moroso['documento'], self.usuario.numero_documento)
        self.assertEqual(moroso['prestamo_id'], prestamo_vencido.codigo_prestamo)
        self.assertEqual(moroso['dias_mora'], 5)

        # 3. Como Administrador, ejecutar acción para aplicar bloqueos a los morosos
        resp_bloqueo = self.client.post('/inventario/reportes/bloquear-morosos/', {
            'usuario_id': self.usuario.id
        })
        self.assertEqual(resp_bloqueo.status_code, 200)
        resp_bloqueo_data = resp_bloqueo.json()
        self.assertEqual(resp_bloqueo_data['status'], 'success')
        self.assertGreaterEqual(resp_bloqueo_data['bloqueados_count'], 1)

        # 4. Validar persistencia: Usuario bloqueado (estado = inactivo) y sanción activa creada
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, 'inactivo')

        sanciones_usuario = Sancion.objects.filter(usuario=self.usuario, estado_sancion='Activa')
        self.assertTrue(sanciones_usuario.exists())
        self.assertTrue('Mora' in sanciones_usuario.first().tipo_sancion)

