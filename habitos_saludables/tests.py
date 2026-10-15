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
        self.assertEqual(seguimiento.get_categoria_imc()[0], "Peso normal")

    def test_categorias_imc(self):
        """Prueba las diferentes clasificaciones de IMC."""
        # Bajo peso
        seg_bajo = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("50.00"),
            estatura_cm=Decimal("180.00")
        )
        self.assertEqual(seg_bajo.get_categoria_imc()[0], "Bajo peso")

        # Sobrepeso
        seg_sobre = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("85.00"),
            estatura_cm=Decimal("175.00")
        )
        self.assertEqual(seg_sobre.get_categoria_imc()[0], "Sobrepeso")

        # Obesidad
        seg_obeso = SeguimientoSalud.objects.create(
            usuario=self.usuario,
            peso_kg=Decimal("100.00"),
            estatura_cm=Decimal("170.00")
        )
        self.assertEqual(seg_obeso.get_categoria_imc()[0], "Obesidad")
        self.assertEqual(seg_obeso.categoria_imc, "Obesidad")
        self.assertEqual(seg_obeso.color_imc, "danger")

    def test_calcular_imc_cero_o_negativo_no_causa_excepcion(self):
        """Prueba que estatura 0 o valores no positivos devuelvan None sin ZeroDivisionError."""
        seg = SeguimientoSalud(
            usuario=self.usuario,
            peso_kg=Decimal("70.00"),
            estatura_cm=Decimal("0.00")
        )
        self.assertIsNone(seg.calcular_imc())

        seg_neg = SeguimientoSalud(
            usuario=self.usuario,
            peso_kg=Decimal("-70.00"),
            estatura_cm=Decimal("170.00")
        )
        self.assertIsNone(seg_neg.calcular_imc())

    def test_formulario_rechaza_valores_cero_y_negativos(self):
        """Prueba que SeguimientoSaludForm rechace 0 y números negativos en todas las variables numéricas."""
        from .forms import SeguimientoSaludForm
        from django.utils import timezone

        hoy = timezone.localdate().isoformat()

        # Peso 0
        form = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '0',
            'estatura_cm': '170',
            'presion_sistolica': '120',
            'presion_diastolica': '80',
            'frecuencia_cardiaca': '70',
            'horas_sueno': '8',
            'vasos_agua': '8',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('peso_kg', form.errors)

        # Peso negativo
        form_neg_peso = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '-70',
            'estatura_cm': '170',
            'presion_sistolica': '120',
            'presion_diastolica': '80',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_neg_peso.is_valid())
        self.assertIn('peso_kg', form_neg_peso.errors)

        # Estatura 0
        form_estatura_cero = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '70',
            'estatura_cm': '0',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_estatura_cero.is_valid())
        self.assertIn('estatura_cm', form_estatura_cero.errors)

        # Presión sistólica 0
        form_presion = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '70',
            'estatura_cm': '170',
            'presion_sistolica': '0',
            'presion_diastolica': '80',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_presion.is_valid())
        self.assertIn('presion_sistolica', form_presion.errors)

        # Frecuencia cardíaca negativa
        form_fc = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '70',
            'estatura_cm': '170',
            'frecuencia_cardiaca': '-60',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_fc.is_valid())
        self.assertIn('frecuencia_cardiaca', form_fc.errors)

        # Horas de sueño 0
        form_sueno = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '70',
            'estatura_cm': '170',
            'horas_sueno': '0',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_sueno.is_valid())
        self.assertIn('horas_sueno', form_sueno.errors)

        # Vasos de agua 0
        form_agua = SeguimientoSaludForm(data={
            'fecha_evaluacion': hoy,
            'peso_kg': '70',
            'estatura_cm': '170',
            'vasos_agua': '0',
            'nivel_actividad': 'moderado'
        })
        self.assertFalse(form_agua.is_valid())
        self.assertIn('vasos_agua', form_agua.errors)
