"""
Auditoría de Seguridad + QA/QC — Módulo `habitos_saludables`
=============================================================

Codifica el COMPORTAMIENTO ESPERADO (seguro y correcto) del módulo.
Algunas pruebas FALLAN contra el código actual → documentan defectos
confirmados por la auditoría (ver reporte AUDIT_HABITOS.md).

Convención CP-HAB:
  - Positivo  → verifica comportamiento correcto (debe pasar).
  - Negativo  → verifica rechazo de entrada inválida / acceso no autorizado.
  - Seguridad → verifica control de acceso, inyección y sanitización.
  - CRITICAL  → hallazgo de seguridad grave.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import (
    HabeasDataConsent, HabitoSaludable, RutinaFisica,
    PiramideNutricional, MaterialApoyo, SeguimientoSalud,
)


class AuditoriaHabitosTests(TestCase):
    """Batería CP-HAB de auditoría de seguridad y QA/QC."""

    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="aprendiz_hab", password="PasswordSecure*123",
            email="hab_aprendiz@sena.edu.co", numero_documento="1001001001",
            rol="aprendiz",
        )
        # Material con URL de video (tipo 'video')
        self.material_video = MaterialApoyo.objects.create(
            titulo="Clase de Yoga", tipo_contenido="video",
            descripcion="Video de yoga", autor="SENA",
            url_video="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            activo=True,
        )
        # Material con archivo (tipo 'pdf')
        self.material_pdf = MaterialApoyo.objects.create(
            titulo="Guía PDF", tipo_contenido="pdf",
            descripcion="Documento PDF", autor="SENA",
            activo=True,
        )

    # ------------------------------------------------------------------
    # CP-HAB-01 — CRITICAL: Habeas Data es auto-aceptado sin interacción.
    # `tiene_habeas_data()` crea el consentimiento con acepta=True si no
    # existe. Esto anula por completo el mecanismo de protección de datos.
    # La Ley 1581 de 2012 exige consentimiento libre, expreso y prolongado.
    # ------------------------------------------------------------------
    def test_cp_hab_01_habeas_data_nunca_es_auto_aceptado(self):
        """CRITICAL (falla): El Habeas Data no debe auto-crearse como aceptado."""
        from .views import tiene_habeas_data
        # Asegurar que no existe consentimiento previo
        self.assertFalse(HabeasDataConsent.objects.filter(usuario=self.aprendiz).exists())
        # tiene_habeas_data NO debe auto-crear un consentimiento aceptado
        result = tiene_habeas_data(self.aprendiz)
        # El resultado debe ser False (no hay consentimiento todavía)
        self.assertFalse(
            result,
            "tiene_habeas_data() retornó True para un usuario sin consentimiento "
            "explícito — el consentimiento se auto-crea con acepta=True, anulando "
            "la protección de datos personales (Ley 1581/2012).")

    # ------------------------------------------------------------------
    # CP-HAB-02 — CRITICAL: Open redirect / phishing en descargar_material.
    # La vista redirige a material.url_video sin validación de dominio.
    # Un admin malicioso o comprometido puede establecer URLs de phishing.
    # ------------------------------------------------------------------
    def test_cp_hab_02_descargar_material_video_restringe_dominios(self):
        """CRITICAL (falla): descargar_material redirige a URLs externas no validadas."""
        from .views import descargar_material
        from django.core.handlers.wsgi import WSGIRequest

        # Un material con URL de phishing
        phish_material = MaterialApoyo.objects.create(
            titulo="Video Falso", tipo_contenido="video",
            descripcion="Test", autor="SENA",
            url_video="https://malicious-site.com/phishing",
            activo=True,
        )
        # Simular con TestClient
        self.client.login(username="aprendiz_hab", password="PasswordSecure*123")
        response = self.client.get(f"/habitos/biblioteca/descargar/{phish_material.pk}/")

        # No debe redirigir a un dominio externo no autorizado
        # Debe retornar 403/400 o redirigir solo a dominios permitidos
        if response.status_code in (302, 301):
            location = response.get("Location", "")
            self.assertNotIn(
                "malicious-site.com", location,
                f"descargar_material redirige a dominio externo no validado: {location}. "
                "Debe validar que la URL pertenezca a un dominio permitido "
                "(youtube.com, vimeo.com, etc.) o bloquear redirecciones externas.")
        else:
            # Si no redirige, al menos no debe permitir acceso directo a URL externa
            self.assertNotIn(
                "malicious-site.com", response.content.decode("utf-8", errors="ignore"),
                "El contenido de la página contiene la URL de phishing.")

    # ------------------------------------------------------------------
    # CP-HAB-03 — MEDIUM: MaterialApoyoForm no valida uploads.
    # El formulario acepta archivo e imagen_portada pero nunca llama
    # validate_uploaded_file(). No hay sanitización de tipo/size/magic bytes.
    # ------------------------------------------------------------------
    def test_cp_hab_03_material_apoyo_form_valida_archivos(self):
        """MEDIUM (falla): MaterialApoyoForm no valida archivos subidos."""
        from .forms import MaterialApoyoForm
        from core.security.file_upload import validate_uploaded_file

        # Intentar subir un archivo .exe (no permitido)
        exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
        exe_file = SimpleUploadedFile(
            "malware.exe", exe_content, content_type="application/x-msdownload")
        form = MaterialApoyoForm(
            data={
                "titulo": "Test Malware",
                "descripcion": "Test",
                "tipo_contenido": "documento",
                "autor": "SENA",
                "fecha_publicacion": "2026-10-14",
            },
            files={"archivo": exe_file},
        )
        # El formulario ahora valida el tipo de archivo (llama a validate_uploaded_file)
        # Un .exe debe ser rechazado en el campo 'archivo'
        self.assertIn(
            "archivo", form.errors,
            "MaterialApoyoForm debe validar y rechazar archivos .exe.")
        # Verificar que validate_uploaded_file SÍ rechazaría el .exe
        try:
            validate_uploaded_file(exe_file, allowed_types="document")
            file_validated = True
        except Exception:
            file_validated = False
        self.assertFalse(
            file_validated,
            "validate_uploaded_file NO rechaza .exe — validación de magic bytes fallida.")

    # ------------------------------------------------------------------
    # CP-HAB-04 — POSITIVO: MaterialApoyoForm requiere archivo para tipos
    # que no son video/url. Este test verifica la validación existente.
    # ------------------------------------------------------------------
    def test_cp_hab_04_form_rechaza_tipo_documento_sin_archivo(self):
        """POSITIVO (pasa): tipo 'pdf' requiere adjuntar archivo."""
        from .forms import MaterialApoyoForm
        form = MaterialApoyoForm(
            data={
                "titulo": "Test PDF",
                "descripcion": "Test",
                "tipo_contenido": "pdf",
                "autor": "SENA",
                "fecha_publicacion": "2026-10-14",
            },
            files={},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("archivo", str(form.errors["__all__"]).lower())

    # ------------------------------------------------------------------
    # CP-HAB-05 — BUG: get_categoria_imc() devuelve string, vista hace
    # unpacking de tupla (ValueError: too many values to unpack).
    # ------------------------------------------------------------------
    def test_cp_hab_05_get_categoria_imc_returns_tuple(self):
        """CORREGIDO: get_categoria_imc() devuelve tupla (categoria, color)."""
        # Crear un seguimiento con IMC calculado
        seg = SeguimientoSalud.objects.create(
            usuario=self.aprendiz, peso_kg=70.0, estatura_cm=170,
            presion_sistolica=120, presion_diastolica=80)
        # get_categoria_imc() devuelve una tupla (categoria, color)
        result = seg.get_categoria_imc()
        self.assertIsInstance(
            result, tuple,
            "get_categoria_imc() debe devolver una tupla (categoria, color) "
            "para que la vista pueda hacer unpacking.")
        self.assertEqual(len(result), 2)
        categoria, color = result
        self.assertIsInstance(categoria, str)
        self.assertIsInstance(color, str)

    # ------------------------------------------------------------------
    # CP-HAB-06 — Negativo: fecha_evaluacion no puede ser futura/pasada.
    # ------------------------------------------------------------------
    def test_cp_hab_06_fecha_pasada_rechazada(self):
        """NEGATIVO (pasa): fecha de evaluación en el pasado es rechazada."""
        from .forms import SeguimientoSaludForm
        from datetime import date, timedelta
        form = SeguimientoSaludForm(
            data={
                "fecha_evaluacion": (date.today() - timedelta(days=1)).isoformat(),
                "peso_kg": "70.0",
                "estatura_cm": "170",
                "presion_sistolica": "120",
                "presion_diastolica": "80",
                "nivel_actividad": "moderado",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_evaluacion", form.errors)

    # ------------------------------------------------------------------
    # CP-HAB-07 — Seguridad: detalle_seguimiento forzarOwnership.
    # Un aprendiz no debe ver el seguimiento de otro usuario.
    # ------------------------------------------------------------------
    def test_cp_hab_07_seguimiento_propio_no_accesible_por_otro(self):
        """SEGURIDAD (pasa): un usuario no ve seguimientos ajenos (404)."""
        otro = self.User.objects.create_user(
            username="otro_hab", password="PasswordSecure*123",
            email="otro@sena.edu.co", numero_documento="2002002002", rol="aprendiz")
        self.client.login(username="aprendiz_hab", password="PasswordSecure*123")
        seg = SeguimientoSalud.objects.create(
            usuario=otro, peso_kg="75.0", estatura_cm="175",
            presion_sistolica=120, presion_diastolica=80)
        response = self.client.get(f"/habitos/salud/{seg.pk}/")
        self.assertEqual(response.status_code, 404,
                         "Un aprendiz puede acceder al seguimiento de otro usuario (IDOR).")

    # ------------------------------------------------------------------
    # CP-HAB-08 — Negativo: presión sistólica debe ser mayor que diastólica.
    # ------------------------------------------------------------------
    def test_cp_hab_08_presion_invertida_rechazada(self):
        """NEGATIVO (pasa): presión sistólica <= diastólica es rechazada."""
        from .forms import SeguimientoSaludForm
        form = SeguimientoSaludForm(
            data={
                "fecha_evaluacion": "2026-10-14",
                "peso_kg": "70.0",
                "estatura_cm": "170",
                "presion_sistolica": "80",      # ERROR: menor que diastólica
                "presion_diastolica": "120",
                "nivel_actividad": "moderado",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
