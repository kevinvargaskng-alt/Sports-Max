from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Reserva, GimnasioConfig

class GimnasioAppTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_gimnasio",
            password="password123",
            email="gimnasio@sena.edu.co",
            numero_documento="87654321"
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
