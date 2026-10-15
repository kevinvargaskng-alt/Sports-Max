from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
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


class TestInventarioQAQC(TestCase):
    """Batería de Pruebas QA/QC automatizadas para el módulo de Inventario y Préstamos."""

    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="aprendiz_qa",
            password="Password123*",
            email="aprendiz_qa@sena.edu.co",
            numero_documento="1098765432",
            rol="aprendiz"
        )
        self.elemento = ElementoDeportivo.objects.create(
            tipo_maquina="Balón de Microfútbol Golty",
            cantidad_total=10,
            estado_general="Bueno",
            habilitado=True
        )

    def test_cp_inv_01_prestamo_exitoso_y_decremento_stock(self):
        """CP-INV-01 (Positivo): Préstamo regular descuenta del inventario y queda en estado Activo."""
        self.client.login(username="aprendiz_qa", password="Password123*")
        stock_inicial = self.elemento.cantidad_total

        resp = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': 2,
            'dias_prestamo': 3,
            'observacion': 'Entrenamiento de ficha ADSO'
        })
        self.assertEqual(resp.status_code, 302)

        # Validar persistencia del préstamo
        prestamo = Prestamo.objects.filter(usuario=self.aprendiz).latest('codigo_prestamo')
        self.assertEqual(prestamo.cantidad_prestada, 2)
        self.assertEqual(prestamo.estado_prestamo, 'Activo')

        # Validar decremento de stock
        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, stock_inicial - 2)

    def test_cp_inv_02_rechazo_prestamo_usuario_sancionado(self):
        """CP-INV-02 (Negativo): Usuario con sanción activa no puede realizar préstamos."""
        Sancion.objects.create(
            usuario=self.aprendiz,
            tipo_sancion="Suspensión por daño",
            fecha_inicio_sancion=date.today(),
            fecha_fin_sancion=date.today() + timedelta(days=15),
            estado_sancion="Activa",
            descripcion_sancion="Sanción disciplinaria vigente"
        )
        self.client.login(username="aprendiz_qa", password="Password123*")
        stock_inicial = self.elemento.cantidad_total

        resp = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': 1,
            'dias_prestamo': 2
        })
        self.assertEqual(resp.status_code, 302)

        # No se debió crear el préstamo
        self.assertFalse(Prestamo.objects.filter(usuario=self.aprendiz).exists())
        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, stock_inicial)

    def test_cp_inv_03_prestamo_limite_ultima_unidad(self):
        """CP-INV-03 (Límite): Préstamo de la última unidad disponible (stock pasa exactamente a 0)."""
        self.elemento.cantidad_total = 1
        self.elemento.save()

        self.client.login(username="aprendiz_qa", password="Password123*")
        resp = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': 1,
            'dias_prestamo': 1
        })
        self.assertEqual(resp.status_code, 302)

        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, 0)
        self.assertTrue(Prestamo.objects.filter(usuario=self.aprendiz, elemento=self.elemento).exists())

    def test_cp_inv_04_devolucion_con_novedad_y_sancion_automatica(self):
        """CP-INV-04 (QC Integración): Devolución con daño restaura stock y genera sanción automática."""
        prestamo = Prestamo.objects.create(
            usuario=self.aprendiz,
            elemento=self.elemento,
            cantidad_prestada=1,
            dias_prestamo=1,
            estado_prestamo='Activo'
        )
        self.elemento.cantidad_total = 9
        self.elemento.save()

        self.client.login(username="aprendiz_qa", password="Password123*")
        resp = self.client.post('/inventario/devoluciones/', {
            'accion': 'registrar_devolucion',
            'prestamo': prestamo.codigo_prestamo,
            'cantidad_devuelta': 1,
            'tiene_novedad': 'on',
            'estado_elemento_devolucion': 'Dañado',
            'tipo_novedad_devolucion': 'Daño',
            'observaciones_devolucion': 'Balón pinchado durante el partido'
        })
        self.assertEqual(resp.status_code, 302)

        # Validar creación de devolución
        devolucion = Devolucion.objects.filter(prestamo=prestamo).first()
        self.assertIsNotNone(devolucion)
        self.assertTrue(devolucion.tiene_novedad)
        self.assertEqual(devolucion.tipo_novedad_devolucion, 'Daño')

        # Validar que se generó la sanción automática
        sancion = Sancion.objects.filter(usuario=self.aprendiz, estado_sancion='Activa').first()
        self.assertIsNotNone(sancion)
        self.assertIn('Daño', sancion.tipo_sancion)

    def test_crear_elemento_rechaza_cantidad_cero_y_negativa(self):
        """Prueba que crear_elemento rechace cantidades menores a 1 (0 y negativos)."""
        admin = self.User.objects.create_user(
            username="admin_qty_test",
            password="Password123*",
            email="admin_qty@sena.edu.co",
            numero_documento="77778888",
            is_staff=True
        )
        self.client.login(username="admin_qty_test", password="Password123*")

        # Intentar crear con cantidad 0
        resp_cero = self.client.post('/inventario/', {
            'accion': 'crear_elemento',
            'nombre_elemento': 'Aro de Básquet Cero',
            'cantidad_total': '0',
            'habilitado': 'on'
        })
        self.assertEqual(resp_cero.status_code, 302)
        self.assertFalse(ElementoDeportivo.objects.filter(tipo_maquina='Aro de Básquet Cero').exists())

        # Intentar crear con cantidad negativa
        resp_neg = self.client.post('/inventario/', {
            'accion': 'crear_elemento',
            'nombre_elemento': 'Aro de Básquet Negativo',
            'cantidad_total': '-3',
            'habilitado': 'on'
        })
        self.assertEqual(resp_neg.status_code, 302)
        self.assertFalse(ElementoDeportivo.objects.filter(tipo_maquina='Aro de Básquet Negativo').exists())

    def test_crear_prestamo_rechaza_cantidad_cero_y_negativa(self):
        """Prueba que crear_prestamo rechace cantidades menores a 1 (0 y negativos)."""
        self.client.login(username="aprendiz_qa", password="Password123*")

        # Intentar prestar cantidad 0
        resp_cero = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': '0',
            'dias_prestamo': '2'
        })
        self.assertEqual(resp_cero.status_code, 302)
        self.assertFalse(Prestamo.objects.filter(usuario=self.aprendiz, cantidad_prestada=0).exists())

        # Intentar prestar cantidad negativa
        resp_neg = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': '-2',
            'dias_prestamo': '2'
        })
        self.assertEqual(resp_neg.status_code, 302)
        self.assertFalse(Prestamo.objects.filter(usuario=self.aprendiz, cantidad_prestada__lte=0).exists())


