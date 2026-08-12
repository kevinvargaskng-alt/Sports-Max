from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class InicioAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="aprendiz_inicio",
            password="password123",
            email="inicio@sena.edu.co",
            first_name="Carlos",
            last_name="Ramírez",
            numero_documento="11223344",
            rol="aprendiz"
        )

    def test_inicio_view_anonimo(self):
        """Prueba la respuesta de la vista inicio para usuarios no autenticados."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inicio.html')
        self.assertIn('stats', response.context)
        self.assertFalse(response.context['aprendiz_logueado'])

    def test_inicio_view_autenticado(self):
        """Prueba la respuesta de la vista inicio para usuarios autenticados."""
        self.client.login(username="aprendiz_inicio", password="password123")
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['aprendiz_logueado'])
        self.assertEqual(response.context['nombre_usuario'], "Carlos Ramírez")

    def test_ayuda_view(self):
        """Prueba la vista del centro de ayuda."""
        response = self.client.get(reverse('ayuda'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ayuda.html')
