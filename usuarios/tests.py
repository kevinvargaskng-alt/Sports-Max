from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import Sugerencia, HistorialAccion

class UsuariosAppTests(TestCase):
    def setUp(self):
        cache.clear()
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_test",
            password="password123",
            email="test@sena.edu.co",
            numero_documento="12345678",
            tipo_documento="CC",
            rol="aprendiz"
        )

    def test_creacion_usuario(self):
        """Prueba que el usuario se cree correctamente con sus atributos personalizados."""
        user = self.User.objects.get(username="aprendiz_test")
        self.assertEqual(user.numero_documento, "12345678")
        self.assertEqual(user.email, "test@sena.edu.co")
        self.assertEqual(user.rol, "aprendiz")
        self.assertEqual(user.estado, "activo")

    def test_creacion_sugerencia(self):
        """Prueba el registro de una sugerencia vinculada al usuario."""
        sugerencia = Sugerencia.objects.create(
            usuario=self.usuario,
            tipo="queja",
            comentario="Falta material en el gimnasio.",
            anonimo=False
        )
        self.assertEqual(sugerencia.usuario, self.usuario)
        self.assertEqual(sugerencia.tipo, "queja")
        self.assertEqual(sugerencia.anonimo, False)
        self.assertIn("Sugerencia #", str(sugerencia))

    def test_login_por_documento_y_correo(self):
        """Verifica que el login funcione tanto con número de documento como con correo electrónico."""
        # Login con numero de documento (AJAX)
        resp_doc = self.client.post('/login/', {'username': '12345678', 'password': 'password123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_doc.status_code, 200)
        self.assertTrue(resp_doc.json().get('success'))

        self.client.logout()

        # Login con correo electronico (AJAX)
        resp_email = self.client.post('/login/', {'username': 'test@sena.edu.co', 'password': 'password123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_email.status_code, 200)
        self.assertTrue(resp_email.json().get('success'))

        self.client.logout()

        # Login estándar sin AJAX (debe redirigir 302)
        resp_std = self.client.post('/login/', {'username': '12345678', 'password': 'password123'})
        self.assertEqual(resp_std.status_code, 302)
        self.assertEqual(resp_std.url, '/perfil/')

    def test_login_cuenta_inactiva(self):
        """Verifica que una cuenta inactiva retorne un mensaje adecuado."""
        self.usuario.is_active = False
        self.usuario.save()

        resp = self.client.post('/login/', {'username': '12345678', 'password': 'password123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)
        self.assertIn('inactiva', resp.json().get('message', ''))

    def test_cp02_historial_acciones_creacion(self):
        """CP-02: Verifica que la tabla historial_acciones guarde registros correctamente."""
        registro = HistorialAccion.objects.create(
            usuario=self.usuario,
            modulo='Inventario',
            accion='CREAR_PRESTAMO',
            descripcion='Préstamo de balón de fútbol #102',
            ip_origen='127.0.0.1'
        )
        self.assertEqual(HistorialAccion.objects.count(), 1)
        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.modulo, 'Inventario')
        self.assertIn('CREAR_PRESTAMO', str(registro))

    def test_cp07_rechazo_contrasena_corta(self):
        """CP-07: Verifica que el backend rechace contraseñas menores al mínimo de seguridad."""
        resp = self.client.post('/registro/', {
            'numero_documento': '99887766',
            'nombres': 'Prueba',
            'apellidos': 'Seguridad',
            'genero': 'M',
            'telefono': '3001234567',
            'programa_formacion': 'ADSO',
            'email': 'prueba.seg@sena.edu.co',
            'ficha': '2670123',
            'contrasena': '1234'  # Contraseña corta (<8 caracteres)
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get('status'), 'error')

    def test_cp16_restriccion_accesos_segun_rol(self):
        """CP-16: Validar restricción de accesos y rutas según rol de usuario."""
        admin = self.User.objects.create_superuser(
            username="admin_cp16",
            password="adminpassword123",
            email="admin_cp16@sena.edu.co",
            numero_documento="87654321",
            rol="admin"
        )

        # Aprendiz (usuario normal) no puede acceder a /usuarios/
        self.client.login(username="aprendiz_test", password="password123")
        resp_aprendiz = self.client.get('/usuarios/')
        self.assertEqual(resp_aprendiz.status_code, 302)
        self.client.logout()

        # Administrador puede configurar rol a profesional
        self.client.login(username="admin_cp16", password="adminpassword123")
        resp_cambio = self.client.post(f'/perfil/rol/{self.usuario.id}/', {'rol': 'profesional'})
        self.assertEqual(resp_cambio.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.rol, 'profesional')

        # Administrador configura rol a admin y habilita accesos
        resp_admin = self.client.post(f'/perfil/rol/{self.usuario.id}/', {'rol': 'admin'})
        self.assertEqual(resp_admin.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.rol, 'admin')
        self.assertTrue(self.usuario.is_staff)

        # Con rol admin ahora puede acceder a /usuarios/
        self.client.logout()
        self.client.login(username="aprendiz_test", password="password123")
        resp_acceso = self.client.get('/usuarios/')
        self.assertEqual(resp_acceso.status_code, 200)


class TestUsuariosQAQC(TestCase):
    """Batería de Pruebas QA/QC para el Módulo de Autenticación, Auditoría y Seguridad de Usuarios."""

    def setUp(self):
        cache.clear()
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="1029384756",
            password="PasswordValido123*",
            email="aprendiz_seguridad@sena.edu.co",
            numero_documento="1029384756",
            rol="aprendiz"
        )

    def test_cp_usr_01_autenticacion_valida_y_reset_intentos(self):
        """CP-USR-01 (Positivo): Login exitoso resetea contador de intentos fallidos a cero."""
        self.aprendiz.intentos_fallidos = 2
        self.aprendiz.save()

        resp = self.client.post('/login/', {
            'username': '1029384756',
            'password': 'PasswordValido123*'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('success'))

        self.aprendiz.refresh_from_db()
        self.assertEqual(self.aprendiz.intentos_fallidos, 0)
        self.assertIsNone(self.aprendiz.bloqueado_hasta)

    def test_cp_usr_02_bloqueo_por_fuerza_bruta_intentos_fallidos(self):
        """CP-USR-02 (Límite & Seguridad): 3 intentos erróneos activan bloqueo temporal de cuenta."""
        for intento in range(1, 4):
            resp = self.client.post('/login/', {
                'username': '1029384756',
                'password': 'PasswordIncorrecto*'
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Al tercer intento, debe responder 403 con estado bloqueado
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(resp.json().get('bloqueado'))

        self.aprendiz.refresh_from_db()
        self.assertEqual(self.aprendiz.intentos_fallidos, 3)
        self.assertIsNotNone(self.aprendiz.bloqueado_hasta)

    def test_cp_usr_03_restriccion_rutas_administrativas_rol_aprendiz(self):
        """CP-USR-03 (Negativo & Control de Acceso): Aprendiz es redirigido o denegado en rutas de administración."""
        self.client.login(username="1029384756", password="PasswordValido123*")

        # Intentar acceder a módulo de administración de usuarios
        resp = self.client.get('/usuarios/')
        self.assertEqual(resp.status_code, 302)

    def test_administrador_nunca_se_bloquea(self):
        """Valida que un usuario con rol de administrador jamás sea bloqueado por intentos fallidos o toggle."""
        admin = self.User.objects.create_superuser(
            username="admin_inmune",
            password="AdminPassword123*",
            email="admin_inmune@sena.edu.co",
            numero_documento="77778888",
            rol="admin"
        )

        # 1. 5 intentos erróneos de login no bloquean al admin
        for _ in range(5):
            resp = self.client.post('/login/', {
                'username': '77778888',
                'password': 'PasswordIncorrecto*'
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(resp.status_code, 401)
            self.assertFalse(resp.json().get('bloqueado', False))

        admin.refresh_from_db()
        self.assertEqual(admin.intentos_fallidos, 0)
        self.assertIsNone(admin.bloqueado_hasta)
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.estado, 'activo')

        # Limpiar rate limiting de IP para probar autenticación válida
        cache.clear()

        # 2. Login con contraseña correcta funciona inmediatamente
        resp_ok = self.client.post('/login/', {
            'username': '77778888',
            'password': 'AdminPassword123*'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_ok.status_code, 200)

        # 3. Intentar bloquear la cuenta admin mediante toggle_usuario es denegado
        self.client.login(username="admin_inmune", password="AdminPassword123*")
        resp_toggle = self.client.post(f'/perfil/toggle/{admin.id}/')
        self.assertEqual(resp_toggle.status_code, 302)
        admin.refresh_from_db()
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.estado, 'activo')

