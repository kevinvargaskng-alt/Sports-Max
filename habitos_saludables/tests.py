from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import HabeasDataConsent, SeguimientoSalud

class HabitosSaludablesAppTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_salud",
            password="password123",
            email="salud@sena.edu.co",
            numero_documento="99998888"
        )

    def test_habeas_data_consent(self):
        """Prueba que el registro de consentimiento de Habeas Data funcione correctamente."""
        consentimiento = HabeasDataConsent.objects.create(
            usuario=self.usuario,
            acepta=True,
            direccion_ip="192.168.1.1"
        )
        self.assertEqual(consentimiento.usuario, self.usuario)
        self.assertTrue(consentimiento.acepta)

    def test_seguimiento_salud_e_imc(self):
        """Prueba que el IMC se calcule y clasifique correctamente al guardar los datos."""
        seguimiento = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("70.00"),
            estatura_cm=Decimal("175.00"),
            nivel_actividad="moderado"
        )
        # IMC esperado: 70 / (1.75 * 1.75) = 70 / 3.0625 = 22.86
        self.assertIsNotNone(seguimiento.imc)
        self.assertAlmostEqual(float(seguimiento.imc), 22.86, places=1)
        self.assertEqual(seguimiento.get_categoria_imc(), "Peso normal")

    def test_categorias_imc(self):
        """Prueba las diferentes clasificaciones de IMC."""
        # Bajo peso
        seg_bajo = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("50.00"),
            estatura_cm=Decimal("180.00")
        )
        self.assertEqual(seg_bajo.get_categoria_imc(), "Bajo peso")

        # Sobrepeso
        seg_sobre = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("85.00"),
            estatura_cm=Decimal("175.00")
        )
        self.assertEqual(seg_sobre.get_categoria_imc(), "Sobrepeso")

        # Obesidad
        seg_obeso = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("100.00"),
            estatura_cm=Decimal("170.00")
        )
        self.assertEqual(seg_obeso.get_categoria_imc(), "Obesidad")
