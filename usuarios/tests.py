from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import Sugerencia, HistorialAccion, Notificacion

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
        """Verifica que el login funcione con documento (<=10 caracteres) y rechace credenciales que superen 10 caracteres."""
        # Login con numero de documento (AJAX) - 8 dígitos (permitido)
        resp_doc = self.client.post('/login/', {'username': '12345678', 'password': 'password123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_doc.status_code, 200)
        self.assertTrue(resp_doc.json().get('success'))

        self.client.logout()

        # Credenciales mayores a 10 caracteres deben ser rechazadas estrictamente con HTTP 400
        resp_largo = self.client.post('/login/', {'username': 'test@sena.edu.co', 'password': 'password123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_largo.status_code, 400)
        self.assertFalse(resp_largo.json().get('success'))

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

    def test_marcar_todas_notificaciones_leidas(self):
        """Prueba que el endpoint marque todas las notificaciones pendientes del usuario autenticado."""
        Notificacion.objects.create(usuario=self.usuario, titulo="Notif 1", mensaje="Texto 1", leida=False)
        Notificacion.objects.create(usuario=self.usuario, titulo="Notif 2", mensaje="Texto 2", leida=False)
        
        self.assertEqual(self.usuario.notificaciones.filter(leida=False).count(), 2)

        self.client.login(username="aprendiz_test", password="password123")
        resp = self.client.post('/notificaciones/marcar-leidas/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertEqual(data.get('actualizadas'), 2)
        self.assertEqual(data.get('pendientes'), 0)
        self.assertEqual(self.usuario.notificaciones.filter(leida=False).count(), 0)

    def test_marcar_notificacion_individual_leida(self):
        """Prueba que se pueda marcar una sola notificación específica como leída."""
        n1 = Notificacion.objects.create(usuario=self.usuario, titulo="N1", mensaje="M1", leida=False)
        n2 = Notificacion.objects.create(usuario=self.usuario, titulo="N2", mensaje="M2", leida=False)

        self.client.login(username="aprendiz_test", password="password123")
        resp = self.client.post(
            '/notificaciones/marcar-leidas/',
            {'notificacion_id': n1.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertEqual(data.get('pendientes'), 1)

        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(n1.leida)
        self.assertFalse(n2.leida)

    def test_marcar_notificaciones_seguridad(self):
        """Verifica que el endpoint rechace accesos sin autenticación o con método GET."""
        # Sin login redirige
        resp_unauth = self.client.post('/notificaciones/marcar-leidas/')
        self.assertEqual(resp_unauth.status_code, 302)

        # Con login pero método GET responde 405 Method Not Allowed
        self.client.login(username="aprendiz_test", password="password123")
        resp_get = self.client.get('/notificaciones/marcar-leidas/')
        self.assertEqual(resp_get.status_code, 405)


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

    def test_validacion_telefono_estricto_10_digitos(self):
        """Valida que el backend rechace teléfonos que no tengan exactamente 10 dígitos numéricos."""
        base_payload = {
            'tipo_documento': 'CC',
            'numero_documento': '1098765432',
            'nombres': 'Pepito',
            'apellidos': 'Pérez',
            'genero': 'M',
            'programa_formacion': 'ADSO',
            'email': 'pepito.perez@sena.edu.co',
            'ficha': '2826489',
            'contrasena': 'PasswordSegura123*',
            'confirmar_contrasena': 'PasswordSegura123*'
        }

        # 9 dígitos (rechazado)
        payload_corta = dict(base_payload, telefono='300123456')
        resp = self.client.post('/registro/', payload_corta, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('telefono', resp.json().get('errors', {}))

        # 11 dígitos (rechazado)
        payload_larga = dict(base_payload, telefono='30012345678')
        resp = self.client.post('/registro/', payload_larga, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('telefono', resp.json().get('errors', {}))

        # Letras / caracteres especiales (rechazado)
        payload_alfa = dict(base_payload, telefono='300123456a')
        resp = self.client.post('/registro/', payload_alfa, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('telefono', resp.json().get('errors', {}))

        # Exactamente 10 dígitos (aceptado)
        payload_ok = dict(base_payload, telefono='3001234567')
        resp = self.client.post('/registro/', payload_ok, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('status') == 'success')

    def test_validacion_ficha_estricta_7_digitos(self):
        """Valida que la ficha SENA requiera exactamente 7 dígitos numéricos en backend."""
        base_payload = {
            'tipo_documento': 'CC',
            'numero_documento': '1122334455',
            'nombres': 'Ana',
            'apellidos': 'Gómez',
            'genero': 'F',
            'telefono': '3109876543',
            'programa_formacion': 'ADSO',
            'email': 'ana.gomez@sena.edu.co',
            'contrasena': 'PasswordSegura123*',
            'confirmar_contrasena': 'PasswordSegura123*'
        }

        # 6 dígitos (rechazado)
        payload_6 = dict(base_payload, ficha='267001')
        resp = self.client.post('/registro/', payload_6, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ficha', resp.json().get('errors', {}))

        # 8 dígitos (rechazado)
        payload_8 = dict(base_payload, ficha='26700123')
        resp = self.client.post('/registro/', payload_8, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ficha', resp.json().get('errors', {}))

        # Alfanumérico (rechazado)
        payload_letras = dict(base_payload, ficha='267012A')
        resp = self.client.post('/registro/', payload_letras, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ficha', resp.json().get('errors', {}))

        # 7 dígitos exactos (aceptado)
        payload_7 = dict(base_payload, ficha='2826489')
        resp = self.client.post('/registro/', payload_7, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('status') == 'success')

    def test_login_seguridad_longitudes_e_inyecciones(self):
        """Valida que el login rechace desbordamientos de longitud e inyecciones con HTTP 400 y detalle de error."""
        # 1. Documento con longitud excesiva (>20 caracteres)
        resp_largo = self.client.post('/login/', {
            'username': '1234567890123456789012345',  # 25 caracteres
            'password': 'Password123*'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_largo.status_code, 400)
        self.assertIn('username', resp_largo.json().get('errors', {}))

        # 2. Inyección o caracteres peligrosos en credenciales
        resp_sqli = self.client.post('/login/', {
            'username': "admin' OR 1=1 --",
            'password': 'Password123*'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_sqli.status_code, 400)
        self.assertIn('username', resp_sqli.json().get('errors', {}))

        # 3. Contraseña excediendo longitud máxima (>128 caracteres)
        resp_pass_larga = self.client.post('/login/', {
            'username': '12345678',
            'password': 'a' * 129
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp_pass_larga.status_code, 400)
        self.assertIn('password', resp_pass_larga.json().get('errors', {}))

    def test_validacion_documento_estricto_7_a_10_digitos(self):
        """Valida que el documento de identidad requiera estrictamente entre 7 y 10 dígitos numéricos."""
        base_data = {
            'tipo_documento': 'CC',
            'nombres': 'Carlos',
            'apellidos': 'Mejía',
            'genero': 'M',
            'telefono': '3123456789',
            'programa_formacion': 'ADSO',
            'email': 'carlos.mejia@sena.edu.co',
            'ficha': '2826489',
            'contrasena': 'PasswordSegura123*',
            'confirmar_contrasena': 'PasswordSegura123*'
        }

        # 1. Menos de 7 dígitos (6 dígitos) -> Rechazado con 400
        data_corta = dict(base_data, numero_documento='123456')
        r_corta = self.client.post('/registro/', data_corta, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_corta.status_code, 400)
        self.assertIn('numero_documento', r_corta.json().get('errors', {}))

        # 2. Más de 10 dígitos (11 dígitos) -> Rechazado con 400
        data_larga = dict(base_data, numero_documento='12345678901')
        r_larga = self.client.post('/registro/', data_larga, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_larga.status_code, 400)
        self.assertIn('numero_documento', r_larga.json().get('errors', {}))

        # 3. Caracteres no numéricos -> Rechazado con 400
        data_letras = dict(base_data, numero_documento='1234567A')
        r_letras = self.client.post('/registro/', data_letras, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_letras.status_code, 400)
        self.assertIn('numero_documento', r_letras.json().get('errors', {}))

        # 4. Longitud exacta válida de 7 dígitos -> Aceptado (200 o redirect)
        data_7 = dict(base_data, numero_documento='1234567', email='carlos7@sena.edu.co')
        r_7 = self.client.post('/registro/', data_7, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_7.status_code, 200)

        # 5. Longitud exacta válida de 10 dígitos -> Aceptado
        data_10 = dict(base_data, numero_documento='1234567890', email='carlos10@sena.edu.co')
        r_10 = self.client.post('/registro/', data_10, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_10.status_code, 200)

    def test_seguridad_selects_blindaje_backend(self):
        """Valida que si se envían valores manipulados o no válidos en selects, el backend los rechace obligatoriamente."""
        base_data = {
            'numero_documento': '98765432',
            'nombres': 'María',
            'apellidos': 'Gómez',
            'genero': 'F',
            'telefono': '3109876543',
            'programa_formacion': 'ADSO',
            'email': 'maria.gomez@sena.edu.co',
            'ficha': '2826489',
            'contrasena': 'PasswordSegura123*',
            'confirmar_contrasena': 'PasswordSegura123*'
        }

        # Select tipo_documento manipulado (ej. 'HACK' o 'XX')
        data_tipo_doc_invalido = dict(base_data, tipo_documento='XX')
        r_td = self.client.post('/registro/', data_tipo_doc_invalido, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_td.status_code, 400)
        self.assertIn('tipo_documento', r_td.json().get('errors', {}))
        self.assertIn('La opción seleccionada no es válida', r_td.json().get('errors', {}).get('tipo_documento', ''))

        # Select genero manipulado
        data_genero_invalido = dict(base_data, tipo_documento='CC', genero='INVALIDO')
        r_gen = self.client.post('/registro/', data_genero_invalido, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_gen.status_code, 400)
        self.assertIn('genero', r_gen.json().get('errors', {}))

        # Select programa_formacion manipulado
        data_prog_invalido = dict(base_data, tipo_documento='CC', genero='F', programa_formacion='PROGRAMA_INEXISTENTE')
        r_prog = self.client.post('/registro/', data_prog_invalido, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r_prog.status_code, 400)
        self.assertIn('programa_formacion', r_prog.json().get('errors', {}))


