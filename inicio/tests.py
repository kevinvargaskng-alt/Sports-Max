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

    def test_politica_privacidad_view(self):
        """Prueba la vista de política de privacidad y Habeas Data."""
        response = self.client.get(reverse('politica_privacidad'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'legal/politica_privacidad.html')
        self.assertContains(response, 'Ley Estatutaria 1581 de 2012')

    def test_terminos_condiciones_view(self):
        """Prueba la vista de términos y condiciones."""
        response = self.client.get(reverse('terminos_condiciones'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'legal/terminos_condiciones.html')
        self.assertContains(response, 'Reglamento de la Sala de Gimnasio')

    def test_politica_cookies_view(self):
        """Prueba la vista de política de cookies."""
        response = self.client.get(reverse('politica_cookies'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'legal/politica_cookies.html')
        self.assertContains(response, 'Transparencia Digital')

    def test_robots_txt_view(self):
        """Prueba la generación dinámica de robots.txt."""
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, 'User-agent: *')
        self.assertContains(response, 'Disallow: /admin/')
        self.assertContains(response, 'Sitemap:')

    def test_sitemap_xml_view(self):
        """Prueba la generación dinámica de sitemap.xml."""
        response = self.client.get(reverse('sitemap_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertContains(response, '<urlset')
        self.assertContains(response, '<loc>')

