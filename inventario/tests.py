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
