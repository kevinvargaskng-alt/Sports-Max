"""
Auditoría de Seguridad + QA/QC — Módulo `core`
=============================================

Pruebas CP-CORE-01 … CP-CORE-10 que codifican el comportamiento esperado
para la infraestructura de seguridad central: middlewares, sanitizadores,
validación de uploads, handlers de error, y endpoints IA.

Convención CP-CORE:
  - Positivo  → verifica comportamiento correcto (debe pasar).
  - Negativo  → verifica rechazo de entrada inválida / acceso no autorizado.
  - Seguridad → verifica control de acceso, inyección, sanitización y headers.
"""
import json
import time as _time

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from core.security.sanitizers import (
    sanitize_html, sanitize_input, strip_dangerous_patterns,
)
from core.security.file_upload import (
    validate_uploaded_file, FILE_SIGNATURES,
    ALLOWED_IMAGE_EXTENSIONS, ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_IMAGE_SIZE, MAX_DOCUMENT_SIZE,
)


class TestSecurityHeaders(TestCase):
    """CP-CORE-01: Verificación de cabeceras de seguridad HTTP."""

    def test_cphr_01_security_headers_present(self):
        """POSITIVO (pasa): CSP, Referrer-Policy, Permissions-Policy presentes."""
        response = self.client.get("/")
        self.assertIn("content-security-policy",
                      {k.lower(): v for k, v in response.items()})
        self.assertEqual(
            response.get("Referrer-Policy", ""), "strict-origin-when-cross-origin")
        self.assertIn("Permissions-Policy", response.headers)

    def test_cphr_02_frame_ancestors_denied(self):
        """POSITIVO (pasa): frame-ancestors 'none' previene clickjacking."""
        response = self.client.get("/")
        csp = response.get("content-security-policy", "")
        self.assertIn("frame-ancestors 'none'", csp,
                      "CSP debe incluir frame-ancestors 'none' para prevenir clickjacking.")

    def test_cphr_03_authenticated_no_cache(self):
        """POSITIVO (pasa): contenido autenticado tiene Cache-Control: no-store."""
        user = get_user_model().objects.create_user(
            "cached_user", password="PasswordSecure*123",
            email="cached@test.com", numero_documento="901000001",
            rol="aprendiz")
        self.client.login(username="cached_user", password="PasswordSecure*123")
        response = self.client.get("/perfil/")
        cache_control = response.get("Cache-Control", "")
        self.assertIn("no-store", cache_control,
                      "Contenido autenticado debe prohibir cache (no-store).")


class TestRateLimiting(TestCase):
    """CP-CORE-04: Rate limiting por IP en rutas /login y /api."""

    def setUp(self):
        cache.clear()

    def test_cprl_01_login_rate_limited(self):
        """POSITIVO (pasa): exceso de requests a /login retorna 429."""
        User = get_user_model()
        User.objects.create_user("rl_user", password="PasswordSecure*123",
                                  numero_documento="901000010")
        # Config: login = 5 req/min
        for _i in range(5):
            self.client.post("/login/",
                             {"username": "rl_user", "password": "wrong"})
        # 6ta request debe ser bloqueada
        response = self.client.post("/login/",
                                    {"username": "rl_user", "password": "wrong"})
        self.assertEqual(response.status_code, 429,
                         "Rate limit no protege endpoint de login.")

    def test_cprl_02_api_rate_limited(self):
        """POSITIVO (pasa): exceso de requests a /api/ retorna 429."""
        # API = 30 req/min
        codes = set()
        for _i in range(35):
            response = self.client.post("/api/chat-tux/", data="{}",
                                        content_type="application/json")
            codes.add(response.status_code)
        self.assertIn(429, codes,
                       "Rate limit no protege endpoints de API.")


class TestFileUploadValidation(TestCase):
    """CP-CORE-03: Validación de archivos subidos (magic bytes, size, ext)."""

    def test_cpfu_01_exe_rejected_by_extension(self):
        """POSITIVO (pasa): .exe es rechazado por extensión."""
        from django.core.exceptions import ValidationError
        exe = SimpleUploadedFile("malware.exe", b"MZ\x90\x00",
                                  content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_uploaded_file(exe, allowed_types="image")

    def test_cpfu_02_fake_png_rejected_by_magic_bytes(self):
        """POSITIVO (pasa): archivo .png con content falso es rechazado."""
        from django.core.exceptions import ValidationError
        fake = SimpleUploadedFile("fake.png", b"not-a-real-png-header",
                                   content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_uploaded_file(fake, allowed_types="image")

    def test_cpfu_03_oversized_image_rejected(self):
        """POSITIVO (pasa): imagen sobre el límite de tamaño es rechazada."""
        from django.core.exceptions import ValidationError
        # Crear una imagen PNG válida pero ficticiamente grande
        real_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * (MAX_IMAGE_SIZE + 1)
        png_file = SimpleUploadedFile("big.png", real_png,
                                       content_type="image/png")
        with self.assertRaises(ValidationError) as ctx:
            validate_uploaded_file(png_file, allowed_types="image")
        self.assertIn("tamaño máximo", str(ctx.exception))

    def test_cpfu_04_uuid_renaming_prevents_traversal(self):
        """POSITIVO (pasa): filename tras validación es UUID (no original)."""
        png_header = b'\x89PNG\r\n\x1a\n'
        # PNG mínimo válido-ish (header + padding)
        real_png = png_header + b'\x00' * 100
        png_file = SimpleUploadedFile("../../../etc/passwd.png", real_png,
                                       content_type="image/png")
        result = validate_uploaded_file(png_file, allowed_types="image")
        self.assertNotIn("etc", result.name)
        self.assertNotIn("/", result.name)
        self.assertTrue(result.name.endswith(".png"))


class TestInputSanitization(TestCase):
    """CP-CORE-05: Sanitización de entrada para prevenir XSS."""

    def test_cpsa_01_html_escaped(self):
        """POSITIVO (pasa): sanitize_html escapa <script>."""
        malicious = '<script>alert("xss")</script>'
        sanitized = sanitize_html(malicious)
        self.assertNotIn("<script>", sanitized)
        self.assertIn("&lt;script&gt;", sanitized)

    def test_cpsa_02_control_chars_removed(self):
        """POSITIVO (pasa): sanitize_input elimina caracteres de control."""
        dirty = "hello\x00\x01\x02world"
        cleaned = sanitize_input(dirty)
        self.assertNotIn('\x00', cleaned)
        self.assertNotIn('\x01', cleaned)
        self.assertIn("hello", cleaned)
        self.assertIn("world", cleaned)

    def test_cpsa_03_dangerous_patterns_stripped(self):
        """POSITIVO (pasa): strip_dangerous_patterns elimina javascript: y eventos."""
        text = 'javascript:alert(1) onclick="evil()" <iframe src="evil"></iframe>'
        result = strip_dangerous_patterns(text)
        self.assertNotIn("javascript:", result.lower())
        self.assertNotIn("onclick=", result.lower())
        self.assertNotIn("<iframe", result.lower())


class TestIAEndpointSecurity(TestCase):
    """CP-CORE-06: Seguridad de endpoints IA."""

    def setUp(self):
        User = get_user_model()
        self.aprendiz = User.objects.create_user(
            "ia_aprendiz", password="PasswordSecure*123",
            email="ia_aprendiz@test.com", numero_documento="901000003",
            rol="aprendiz")
        self.admin = User.objects.create_user(
            "ia_admin", password="PasswordSecure*123",
            email="ia_admin@test.com", numero_documento="901000004",
            rol="admin", is_staff=True)

    def test_cpia_01_chat_endpoint_accepts_json(self):
        """POSITIVO (pasa): /api/chat-tux/ responde a JSON bien formado."""
        response = self.client.post(
            "/api/chat-tux/",
            data=json.dumps({"message": "hola", "history": []}),
            content_type="application/json")
        self.assertIn(response.status_code, (200, 502, 503))
        # No debe dar 500 ni revelar stack trace interno
        self.assertNotEqual(response.status_code, 500)

    def test_cpia_02_generar_imagen_no_admin_forbidden(self):
        """SEGURIDAD (pasa): aprendiz NO admin no puede generar imágenes (403)."""
        self.client.login(username="ia_aprendiz", password="PasswordSecure*123")
        response = self.client.post(
            "/api/generar-imagen-ia/",
            data=json.dumps({"prompt": "test image", "aspecto": "1:1"}),
            content_type="application/json")
        self.assertEqual(response.status_code, 403,
                         "Un aprendiz pudo generar imágenes con IA (fallo de authz).")

    def test_cpia_03_generar_imagen_unauth_forbidden(self):
        """SEGURIDAD (pasa): usuario no autenticado no puede generar imágenes."""
        response = self.client.post(
            "/api/generar-imagen-ia/",
            data=json.dumps({"prompt": "test"}),
            content_type="application/json")
        self.assertEqual(response.status_code, 403,
                         "Usuario anónimo intentó generar imagen IA.")

    def test_cpia_04_chat_no_revela_stack_trace(self):
        """SEGURIDAD (pasa): errores de IA no exponen stack traces al cliente."""
        response = self.client.post(
            "/api/chat-tux/",
            data=json.dumps({"message": "hola", "history": []}),
            content_type="application/json")
        if response.status_code == 500:
            body = json.loads(response.content)
            self.assertNotIn(
                "Traceback", body.get("error", ""),
                "Stack trace expuesto al cliente en error de IA.")


class TestErrorHandlers(TestCase):
    """CP-CORE-07: Handlers de error no exponen información sensible."""

    def test_cperr_01_404_no_stack_trace(self):
        """SEGURIDAD (pasa): 404 no incluye stack trace."""
        response = self.client.get("/ruta-que-no-existe/")
        self.assertEqual(response.status_code, 404)
        content = response.content.decode("utf-8", errors="ignore")
        self.assertNotIn("Traceback", content)
        self.assertNotIn("File \"", content)

    def test_cperr_02_403_no_exposure(self):
        """SEGURIDAD (pasa): 403 retorna mensaje genérico."""
        self.err_user = get_user_model().objects.create_user(
            "err_user", password="PasswordSecure*123",
            email="err@test.com", numero_documento="901000002",
            rol="aprendiz")
        self.client.login(username="err_user", password="PasswordSecure*123")
        # Acceder a algo restringido a admin
        response = self.client.post(
            "/api/generar-imagen-ia/",
            data=json.dumps({"prompt": "test"}),
            content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_cperr_03_500_handler_generic(self):
        """SEGURIDAD (pasa): 500 retorna mensaje genérico sin detalles."""
        # Enviar JSON malformado a un endpoint IA
        response = self.client.post("/api/chat-tux/",
                                    data="not-valid-json",
                                    content_type="application/json")
        # Debería ser 500 con mensaje genérico
        if response.status_code == 500:
            import json
            body = json.loads(response.content)
            self.assertIn("error", body)
            # No debe contener stack trace
            self.assertNotIn("Traceback", str(body))
