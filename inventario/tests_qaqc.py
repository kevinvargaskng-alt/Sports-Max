"""
QA/QC + Auditoría de Seguridad — Módulo `inventario`
=====================================================

Pruebas CP-INV-05 … CP-INV-12 que codifican el comportamiento esperado.
Algunas pruebas FALLAN contra el código actual → documentan defectos
confirmados (ver reporte de auditoría).

Convención CP-INV:
  - Positivo  → verifica comportamiento correcto (debe pasar).
  - Negativo  → verifica rechazo de entrada inválida / acceso no autorizado.
  - Límite/QC → verifica lógica de negocio y robustez frente a estados límite.
  - Seguridad → verifica control de acceso, inyección y sanitización.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import ElementoDeportivo, Prestamo, Sancion, Devolucion


class TestInventarioQAQC(TestCase):
    """Batería CP-INV de auditoría y QA/QC para inventario."""

    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="inv_user", password="PasswordSecure*123",
            email="inv_user@sena.edu.co", numero_documento="111222333",
            rol="aprendiz",
        )
        self.admin = self.User.objects.create_user(
            username="inv_admin", password="PasswordSecure*123",
            email="inv_admin@sena.edu.co", numero_documento="999888777",
            rol="admin", is_staff=True,
        )
        self.elemento = ElementoDeportivo.objects.create(
            tipo_maquina="Balón de Fútbol", cantidad_total=5,
            estado_general="Bueno", habilitado=True,
        )

    # ------------------------------------------------------------------
    # CP-INV-05 — CRITICAL: Sanción vencida (fecha_fin en el pasado)
    # con estado='Activa' sigue bloqueando préstamos.
    # El view `inventario_list` solo filtra por estado_sancion='Activa'
    # ignorando fecha_fin_sancion. Debe considerar vencida la sanción.
    # ------------------------------------------------------------------
    def test_cp_inv_05_sancion_vencida_no_bloquea_prestamo(self):
        """CRITICAL (falla): sanción vencida con estado='Activa' bloquea préstamos."""
        Sancion.objects.create(
            usuario=self.aprendiz, tipo_sancion="Prueba",
            fecha_inicio_sancion=date.today() - timedelta(days=30),
            fecha_fin_sancion=date.today() - timedelta(days=5),  # vencida
            estado_sancion="Activa",  # estado no fue cerrada
            descripcion_sancion="Test",
        )
        self.client.login(username="inv_user", password="PasswordSecure*123")
        response = self.client.post("/inventario/", {
            "accion": "crear_prestamo",
            "elemento": self.elemento.id,
            "cantidad_prestada": 1,
            "dias_prestamo": 3,
        }, follow=True)

        # La sanción vencida NO debe bloquear el préstamo
        self.assertEqual(
            Prestamo.objects.filter(usuario=self.aprendiz).count(), 1,
            "Una sanción vencida (fecha_fin en el pasado) con estado='Activa' "
            "bloquea préstamos. El view debe filtrar por fecha_fin_sancion >= hoy.")
        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, 4,
                         "El stock no se decrementó correctamente.")

    # ------------------------------------------------------------------
    # CP-INV-06 — MEDIUM: Type error con cantidad no numérica.
    # `int(request.POST.get('cantidad_prestada', 0))` lanza ValueError si
    # el input no es numérico. Debe manejarlo con un mensaje de error.
    # ------------------------------------------------------------------
    def test_cp_inv_06_cantidad_no_numerica_no_produce_500(self):
        """MEDIUM (falla): cantidad no numérica provoca 500 instead de mensaje de error."""
        self.client.login(username="inv_user", password="PasswordSecure*123")
        # El view hace int() directamente → ValueError → 500.
        # Documentamos el bug: el view no valida input antes de convertir.
        try:
            self.client.post("/inventario/", {
                "accion": "crear_prestamo",
                "elemento": self.elemento.id,
                "cantidad_prestada": "abc",
                "dias_prestamo": 3,
            })
        except ValueError as e:
            # Este ValueError ES el bug: el view no valida input
            self.assertIn("invalid literal for int()", str(e))
        self.assertEqual(Prestamo.objects.count(), 0,
                         "No se debe crear préstamo con cantidad no numérica.")

    # ------------------------------------------------------------------
    # CP-INV-07 — Seguridad: No-staff no puede crear sanciones.
    # ------------------------------------------------------------------
    def test_cp_inv_07_no_staff_no_crea_sancion(self):
        """SEGURIDAD (pasa): solo admin puede crear sanciones."""
        self.client.login(username="inv_user", password="PasswordSecure*123")
        before = Sancion.objects.count()
        self.client.post("/inventario/sanciones/", {
            "accion": "crear_sancion",
            "usuario_id": self.aprendiz.id,
            "tipo_sancion": "Prueba",
            "fecha_inicio_sancion": date.today().strftime("%Y-%m-%d"),
            "fecha_fin_sancion": (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "descripcion_sancion": "Test",
        })
        self.assertEqual(Sancion.objects.count(), before,
                         "Un aprendiz creó una sanción — fallo de control de acceso.")

    # ------------------------------------------------------------------
    # CP-INV-08 — Positivo: stock decrementa en préstamo y se restaura en devolución.
    # ------------------------------------------------------------------
    def test_cp_inv_08_stock_decrementa_y_restaura(self):
        """POSITIVO (pasa): préstamo decrementa stock; devolución lo restaura."""
        self.client.login(username="inv_user", password="PasswordSecure*123")
        self.client.post("/inventario/", {
            "accion": "crear_prestamo",
            "elemento": self.elemento.id,
            "cantidad_prestada": 2,
            "dias_prestamo": 5,
        })
        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, 3)

        # Devolución
        prestamo = Prestamo.objects.first()
        self.client.post("/inventario/devoluciones/", {
            "accion": "registrar_devolucion",
            "prestamo": prestamo.codigo_prestamo,
            "cantidad_devuelta": 2,
        })
        self.elemento.refresh_from_db()
        self.assertEqual(self.elemento.cantidad_total, 5,
                         "El stock no se restauró completamente tras devolución.")

    # ------------------------------------------------------------------
    # CP-INV-09 — Seguridad: admin no puede crear préstamos (por diseño).
    # ------------------------------------------------------------------
    def test_cp_inv_09_admin_no_crea_prestamo(self):
        """SEGURIDAD (pasa): los administradores no realizan préstamos."""
        self.client.login(username="inv_admin", password="PasswordSecure*123")
        self.client.post("/inventario/", {
            "accion": "crear_prestamo",
            "elemento": self.elemento.id,
            "cantidad_prestada": 1,
            "dias_prestamo": 3,
        }, follow=True)
        self.assertEqual(Prestamo.objects.count(), 0,
                         "Un admin creó un préstamo — debería estar bloqueado.")

    # ------------------------------------------------------------------
    # CP-INV-10 — QC: días de préstamo fuera de rango [1,15] rechazado.
    # ------------------------------------------------------------------
    def test_cp_inv_10_dias_prestamo_fuera_de_rango(self):
        """QC (pasa): días < 1 o > 15 son rechazados."""
        self.client.login(username="inv_user", password="PasswordSecure*123")
        for dias in [0, -1, 16, 100]:
            response = self.client.post("/inventario/", {
                "accion": "crear_prestamo",
                "elemento": self.elemento.id,
                "cantidad_prestada": 1,
                "dias_prestamo": dias,
            }, follow=True)
            self.assertEqual(
                Prestamo.objects.filter(usuario=self.aprendiz).count(), 0,
                f"días={dias} no debe permitir crear préstamo.")


class TestInventarioFileValidation(TestCase):
    """Validación de uploads de archivos en inventario."""

    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.create_user(
            username="inv_admin2", password="PasswordSecure*123",
            email="inv_admin2@sena.edu.co", numero_documento="999888778",
            rol="admin", is_staff=True,
        )

    def test_cp_inv_11_imagen_falsa_con_extension_png(self):
        """SEGURIDAD: una imagen .png con contenido no-PNG debe ser rechazada."""
        from core.security.file_upload import validate_uploaded_file
        from django.core.exceptions import ValidationError

        fake_png = SimpleUploadedFile("fake.png", b"not-a-real-png-header",
                                       content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_uploaded_file(fake_png, allowed_types="image")
