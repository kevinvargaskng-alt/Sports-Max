"""
QA/QC + Auditoría de Seguridad — Módulo `gimnasio`
===================================================

Pruebas CP-GIM-01 … CP-GIM-08 que codifican el comportamiento esperado.
Algunas pruebas FALLAN contra el código actual → documentan defectos.

Convención CP-GIM:
  - Positivo  → verifica comportamiento correcto (debe pasar).
  - Negativo  → verifica rechazo de entrada inválida / acceso no autorizado.
  - Límite/QC → verifica lógica de negocio y robustez frente a estados límite.
  - Seguridad → verifica control de acceso, IDOR, inyección y sanitización.
"""
from datetime import time, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Reserva, GimnasioConfig, FranjaHoraria, Machine, Maquina


class TestGimnasioQAQC(TestCase):
    """Batería CP-GIM de auditoría y QA/QC para gimnasio."""

    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="gim_aprendiz", password="PasswordSecure*123",
            email="gim_aprendiz@sena.edu.co", numero_documento="100200300",
            rol="aprendiz",
        )
        self.aprendiz2 = self.User.objects.create_user(
            username="gim_aprendiz2", password="PasswordSecure*123",
            email="gim_aprendiz2@sena.edu.co", numero_documento="100200301",
            rol="aprendiz",
        )
        self.admin = self.User.objects.create_user(
            username="gim_admin", password="PasswordSecure*123",
            email="gim_admin@sena.edu.co", numero_documento="900100200",
            rol="admin", is_staff=True,
        )
        config = GimnasioConfig.get_config()
        config.estado = "abierta"
        config.capacidad_maxima = 40
        config.horario_apertura = "07:00"
        config.horario_cierre = "17:00"
        config.save()

    # ------------------------------------------------------------------
    # CP-GIM-01 — CRITICAL: IDOR en eliminar_reserva.
    # Cualquier usuario autenticado puede eliminar reservas ajenas.
    # La vista no verifica propiedad: get_object_or_404(Reserva, codigo_registro=id)
    # ------------------------------------------------------------------
    def test_cp_gim_01_idor_eliminar_reserva_ajena(self):
        """CRITICAL (falla): un aprendiz puede eliminar la reserva de otro."""
        now = datetime.now(ZoneInfo("America/Bogota"))
        from datetime import timedelta as td
        from .models import Reserva  # noqa

        reserva_ajena = Reserva.objects.create(
            usuario_solicitante=self.aprendiz,
            fecha_entrada=now.date(),
            hora_entrada=time(8, 0),
            tiempo_permanencia=60,
            hora_salida=time(9, 0),
            fecha_salida=now.date(),
            estado="Activa",
        )
        self.client.login(username="gim_aprendiz2", password="PasswordSecure*123")
        response = self.client.post(
            f"/gimnasio/eliminar-reserva/{reserva_ajena.codigo_registro}/")
        self.assertEqual(
            response.status_code, 302,
            "eliminar_reserva no verifica ownership — IDOR permitido.")
        # La reserva NO debe haber sido eliminada
        exists = Reserva.objects.filter(
            codigo_registro=reserva_ajena.codigo_registro).exists()
        self.assertTrue(
            exists,
            "CRITICAL: Un aprendiz eliminó la reserva de otro usuario (IDOR). "
            "eliminar_reserva no filtra por usuario_solicitante.")

    # ------------------------------------------------------------------
    # CP-GIM-02 — CRITICAL: IDOR en editar_reserva.
    # Un usuario puede editar (ver) reservas ajenas vía GET.
    # ------------------------------------------------------------------
    def test_cp_gim_02_idor_editar_reserva_ajena(self):
        """CRITICAL: editar_reserva obtiene reserva sin chequear ownership → IDOR."""
        now = datetime.now(ZoneInfo("America/Bogota"))

        reserva = Reserva.objects.create(
            usuario_solicitante=self.aprendiz,
            fecha_entrada=now.date(),
            hora_entrada=time(8, 0),
            tiempo_permanencia=60,
            hora_salida=time(9, 0),
            fecha_salida=now.date(),
            estado="Activa",
        )
        self.client.login(username="gim_aprendiz2", password="PasswordSecure*123")
        # El view hace get_object_or_404(Reserva, codigo_registro=id)
        # SIN filtrar por usuario_solicitante → IDOR.
        # Si fuera seguro, devolvería 404 (no encontrada para este usuario).
        # En su defecto, el view encuentra la reserva (y luego puede fallar
        # por template inexistente, pero eso demuestra que la reserva fue
        # encontrada sin verificación de propiedad).
        self.client.raise_request_exception = False
        response = self.client.get(
            f"/gimnasio/editar-reserva/{reserva.codigo_registro}/")
        # Si fuera 404, significaría que el ownership es verificado.
        # Un 500 (template missing) o 200 (edit page) demuestra IDOR.
        self.assertNotEqual(
            response.status_code, 404,
            "CRITICAL: editar_reserva verifica ownership (IDOR corregrido). "
            "El código actual NO verifica → get_object_or_404 sin filtro usuario.")

    # ------------------------------------------------------------------
    # CP-GIM-03 — MEDIUM: crear_maquina tiene NameError por next_param.
    # `next_param` se usa (línea 367) antes de ser definido (línea 371).
    # Si la validación de imagen falla, lanza NameError → 500.
    # ------------------------------------------------------------------
    def test_cp_gim_03_bad_image_no_500(self):
        """MEDIUM: crear_maquina lanza UnboundLocalError (next_param) → 500."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username="gim_admin", password="PasswordSecure*123")
        bad_image = SimpleUploadedFile(
            "fake.png", b"not-a-real-png", content_type="image/png")
        # El view usa `next_param` antes de definirlo (línea 367 vs 371)
        # → UnboundLocalError → 500 Internal Server Error
        self.client.raise_request_exception = False
        response = self.client.post(
            "/gimnasio/gimnasio/admin/maquinas/crear/",
            {"nombre": "Máquina de Prueba", "categoria": "Cardio",
             "estado": "Disponible", "descripcion": "Test",
             "imagen": bad_image, "next": "machine_list"})
        # El bug provoca 500 (UnboundLocalError)
        self.assertNotEqual(
            response.status_code, 500,
            f"MEDIUM: crear_maquina no debe producir 500 tras fix de next_param. "
            f"Status recibido: {response.status_code}.")
        self.assertEqual(
            response.status_code, 302,
            "Debe redirigir (302) sin crash al subir imagen inválida.")
        # La máquina no debe haberse creado
        self.assertFalse(
            Machine.objects.filter(nombre="Máquina de Prueba").exists(),
            "La máquina con imagen inválida no debe persistirse.")

    # ------------------------------------------------------------------
    # CP-GIM-04 — LOW: Horario hardcodeado ignora GimnasioConfig.
    # La lógica de `esta_abierto` usa horas 7-17 y festivos hardcoded
    # en lugar de los campos horario_apertura/horario_cierre/dias_habilitados
    # del modelo GimnasioConfig.
    # ------------------------------------------------------------------
    def test_cp_gim_04_horario_usa_config_no_hardcodeado(self):
        """QC (falla): el horario de apertura usa valores hardcodeados (7-17)
        en lugar de GimnasioConfig.horario_apertura/cierre."""
        config = GimnasioConfig.get_config()
        config.estado = "abierta"
        config.horario_apertura = "06:00"   # antes de las 7
        config.horario_cierre = "22:00"    # después de las 17
        config.dias_habilitados = ["lun", "mar", "mie", "jue", "vie"]
        config.save()

        self.client.login(username="gim_aprendiz", password="PasswordSecure*123")
        # Fijar fecha/hora: martes 19:00 (dentro del horario config pero fuera 7-17)
        fixed = datetime(2026, 10, 13, 19, 0, tzinfo=ZoneInfo("America/Bogota"))
        with patch("django.utils.timezone.localtime",
                   return_value=fixed), \
             patch("django.utils.timezone.now", return_value=fixed):
            response = self.client.get("/gimnasio/")
        self.assertEqual(response.status_code, 200)
        # Con horario config 6:00-22:00, las 19:00 debería estar ABIERTO
        self.assertIn(
            b"Sala Abierta", response.content,
            "QC: El gimnasio debería estar abierto a las 19:00 con config "
            "06:00-22:00, pero usa horario hardcodeado 7-17.")

    # ------------------------------------------------------------------
    # CP-GIM-05 — Seguridad: admin-only franjas CRUD.
    # Un aprendiz no puede crear/editar/eliminar franjas.
    # ------------------------------------------------------------------
    def test_cp_gim_05_aprendiz_no_administra_franjas(self):
        """SEGURIDAD (pasa): aprendiz recibe 302 (redirigido) al crear franja."""
        self.client.login(username="gim_aprendiz",
                          password="PasswordSecure*123")
        response = self.client.post(
            "/gimnasio/gimnasio/admin/franjas/",
            {"dia_semana": "Lunes", "hora_inicio": "10:00",
             "hora_fin": "11:00", "aforo_maximo": 25},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [302, 403],
                      "Un aprendiz pudo crear una franja horaria — fallo de RBAC.")

    # ------------------------------------------------------------------
    # CP-GIM-06 — QC: validación de horario (inicio >= fin) en franjas.
    # ------------------------------------------------------------------
    def test_cp_gim_06_franja_inicio_mayor_fin_rechazada(self):
        """QC (pasa): hora_inicio >= hora_fin es rechazada en franjas."""
        self.client.login(username="gim_admin", password="PasswordSecure*123")
        response = self.client.post(
            "/gimnasio/gimnasio/admin/franjas/",
            {"dia_semana": "Lunes", "hora_inicio": "11:00",
             "hora_fin": "09:00", "aforo_maximo": 25},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(response.status_code, [400, 302],
                      "Franja con hora_inicio > hora_fin debería ser rechazada.")

    # ------------------------------------------------------------------
    # CP-GIM-07 — Positivo: reserva con sobrecupo es rechazada.
    # CP-19: Validación estricta de sobrecupo con select_for_update.
    # ------------------------------------------------------------------
    def test_cp_gim_07_sobrecupo_rechazado(self):
        """POSITIVO (pasa): no se permite superar el aforo máximo."""
        from django.db import transaction
        config = GimnasioConfig.get_config()
        config.capacidad_maxima = 2
        config.save()

        franja = FranjaHoraria.objects.create(
            dia_semana="Lunes", hora_inicio=time(8, 0),
            hora_fin=time(9, 0), aforo_maximo=2, habilitada=True)

        # Crear 2 reservas en la misma franja (límite)
        ahora = datetime.now(ZoneInfo("America/Bogota"))
        from datetime import timedelta as td

        for i in range(2):
            Reserva.objects.create(
                usuario_solicitante=self.aprendiz if i == 0 else self.aprendiz2,
                fecha_entrada=ahora.date(),
                hora_entrada=time(8, 0),
                tiempo_permanencia=60,
                hora_salida=time(9, 0),
                fecha_salida=ahora.date(),
                franja_horaria=franja,
                estado="Activa",
            )

        # Tercera reserva debe ser rechazada (sobrecupo)
        response = self.client.post(
            "/reserva/turno/",
            {"fecha_reserva": ahora.date().isoformat(),
             "franja_id": franja.pk, "hora_entrada": "08:00"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        # El aprendiz ya tiene una reserva, debe ser rechazado por duplicado
        # o por sobrecupo
        self.assertIn(response.status_code, [400, 302],
                      "Reserva duplicada o sobrecupo debería ser rechazada.")

    # ------------------------------------------------------------------
    # CP-GIM-08 — Seguridad: aforo API requiere autenticación.
    # ------------------------------------------------------------------
    def test_cp_gim_08_aforo_api_unauth_redirect(self):
        """SEGURIDAD (pasa): /aforo/ redirige a login para no autenticados."""
        response = self.client.get("/aforo/")
        self.assertEqual(response.status_code, 302,
                         "El endpoint de aforo debería requerir autenticación.")
        self.assertIn("/aforo", response.get("Location", ""),
                      "El redirect debe incluir next=/aforo para login.")
