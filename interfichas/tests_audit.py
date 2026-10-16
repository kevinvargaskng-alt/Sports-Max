"""
Auditoría de Seguridad + QA/QC — Módulo `interfichas`
======================================================

Conjunto de pruebas CP-INT-04 … CP-INT-10 que codifican el COMPORTAMIENTO
ESPERADO (seguro y correcto) del módulo. Algunas pruebas FALLAN contra el
código actual del módulo → documentan defectos confirmados por la auditoría
(ver reporte `AUDIT_INTERFICHAS.md` adjunto).

Convención CP-INT:
  - Positivo  → verifica comportamiento correcto (debe pasar).
  - Negativo  → verifica rechazo de entrada inválida / acceso no autorizado.
  - Límite/QC → verifica lógica de negocio y robustez frente a estados límite.
  - Seguridad → verifica control de acceso, inyección y sanitización.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import (
    Disciplina, EquipoInterfichas, GrupoInterfichas, JugadorEquipo,
    PartidoInterfichas, TorneoInterfichas,
)
from .views import _calcular_tabla, _ficha_duplicada, es_admin


class AuditoriaInterfichasTests(TestCase):
    """Batería CP-INT de auditoría de seguridad y QA/QC para interfichas."""

    def setUp(self):
        self.User = get_user_model()
        # Aprendiz (rol bajo): NO administrador
        self.aprendiz = self.User.objects.create_user(
            username="aprendiz_audit", password="Password123*",
            email="aprendiz@audit.com", numero_documento="10000001", rol="aprendiz",
        )
        # Instructor (rol admin-tier) PERO is_staff=False → expone el bug de
        # `solo_admin` que referencia `user` (variable indefinida).
        self.instructor = self.User.objects.create_user(
            username="instructor_audit", password="Password123*",
            email="instructor@audit.com", numero_documento="20000002", rol="instructor",
        )
        # Admin completo (is_staff=True)
        self.admin = self.User.objects.create_user(
            username="admin_audit", password="Password123*",
            email="admin@audit.com", numero_documento="30000003",
            rol="admin", is_staff=True,
        )
        self.disc_futbol = Disciplina.objects.create(
            nombre_disciplina="Fútbol 8", tipo_marcador="goles")
        self.disc_volei = Disciplina.objects.create(
            nombre_disciplina="Voleibol Mixto", tipo_marcador="sets")
        self.torneo = TorneoInterfichas.objects.create(
            nombre_torneo="Torneo Auditoría",
            fecha_torneo_fichas=date.today(),
            lugar="Cancha Central",
            disciplina=self.disc_futbol,
            estado="activo",
        )

    # ------------------------------------------------------------------
    # CP-INT-04 — RBAC: instructor (rol='instructor', is_staff=False) debe
    # acceder a vistas @solo_admin. Bug confirmado: `solo_admin` referencia
    # `user` (indefinido) → NameError → 500 para instructores no staff.
    # ------------------------------------------------------------------
    def test_cp_int_04_instructor_non_staff_puede_gestionar_torneo(self):
        """RB (falla): instructor non-staff debe poder gestionar (es_admin incluye 'instructor')."""
        self.client.login(username="instructor_audit", password="Password123*")
        EquipoInterfichas.objects.create(
            ficha=9001, programa="ADSO", nombre_equipo="Equipo X",
            capitan="Cap X", torneo=self.torneo, disciplina=self.disc_futbol)
        url = f"/interfichas/torneo/{self.torneo.pk}/"
        try:
            resp = self.client.get(url)
            crashed = False
            last_err = None
        except Exception as exc:  # noqa: BLE001 — queremos atrapar CUALQUIER 500
            crashed = True
            last_err = repr(exc)
        self.assertFalse(
            crashed,
            "Un instructor (rol='instructor', is_staff=False) pertenece al "
            "grupo admin-tier según es_admin; no debe provocar 500. "
            f"Decorator @solo_admin referencia `user` indefinido → {last_err}")
        self.assertIn(resp.status_code, (200,))

    # ------------------------------------------------------------------
    # CP-INT-05 — Negativo/robustez: ficha no numérica debe rechazarse con
    # redirect + mensaje, NUNCA 500 (DataError al insertar 'abc' en INT).
    # ------------------------------------------------------------------
    def test_cp_int_05_ficha_no_numerica_rechazada_sin_500(self):
        """RB (falla): ficha no numérica provoca 500 en lugar de rechazo limpio."""
        self.client.login(username="aprendiz_audit", password="Password123*")
        url = "/interfichas/"
        for bad_ficha in ("abc", "12.3.4", "12 34"):
            with self.subTest(ficha=bad_ficha):
                payload = {
                    "accion_tipo": "inscribir_equipo",
                    "torneo_id": self.torneo.pk,
                    "ficha": bad_ficha,
                    "programa": "ADSO",
                    "capitan": "Capitán Prueba",
                    "nombre_equipo": "Equipo Prueba",
                }
                try:
                    resp = self.client.post(url, payload)
                    crashed = False
                except Exception as exc:  # noqa: BLE001
                    crashed = True
                    last_err = repr(exc)
                self.assertFalse(
                    crashed,
                    f"ficha='{bad_ficha}' no debe provocar 500.")
                # No debe crear el equipo
                self.assertEqual(EquipoInterfichas.objects.count(), 0)
                # Y debe rechazar con redirect (302) a /interfichas/
                self.assertEqual(resp.status_code, 302)

    # ------------------------------------------------------------------
    # CP-INT-06 — QC robustez: _calcular_tabla y puntos_local() deben
    # tolerar goles nulos. Bug confirmado: `st['gf'] += p.goles_local` y
    # `p.goles_local > p.goles_visitante` lanzan TypeError con None.
    # ------------------------------------------------------------------
    def test_cp_int_06_tabla_robusta_con_goles_nulos(self):
        """RB (falla): goles nulos en partido jugado hacen crashear la tabla."""
        eq1 = EquipoInterfichas.objects.create(
            ficha=101, programa="ADSO", nombre_equipo="A", capitan="Cap A",
            torneo=self.torneo, disciplina=self.disc_futbol)
        eq2 = EquipoInterfichas.objects.create(
            ficha=102, programa="ADSO", nombre_equipo="B", capitan="Cap B",
            torneo=self.torneo, disciplina=self.disc_futbol)
        g = GrupoInterfichas.objects.create(torneo=self.torneo, nombre_grupo="Z")
        g.equipos.set([eq1, eq2])
        partido = PartidoInterfichas.objects.create(
            torneo=self.torneo, grupo=g, fase="grupo",
            equipo_local=eq1, equipo_visitante=eq2,
            goles_local=None, goles_visitante=None, jugado=True)

        # 1) puntos_local() debe no crashear
        try:
            partido.puntos_local()
            partido.puntos_visitante()
            methods_ok = True
        except TypeError:
            methods_ok = False
        self.assertTrue(
            methods_ok,
            "puntos_local()/puntos_visitante() deben tolerar goles nulos "
            "(jugado=True implica goles definidos, pero la defensiva evita 500).")

        # 2) _calcular_tabla debe no crashear ni devolver pj inconsistente
        try:
            tabla = _calcular_tabla(g)
            tabla_ok = True
        except TypeError:
            tabla_ok = False
            tabla = None
        self.assertTrue(
            tabla_ok,
            "_calcular_tabla() lanza TypeError al encontrar goles nulos "
            "(st['gf'] += p.goles_local).")
        self.assertIsNotNone(tabla)
        self.assertEqual(len(tabla), 2)

    # ------------------------------------------------------------------
    # CP-INT-07 — QC POSITIVO: cálculo correcto 3-1-0 y orden de tabla.
    # ------------------------------------------------------------------
    def test_cp_int_07_calculo_correcto_tabla_posiciones(self):
        """QC (pasa): 3 pts victoria, 1 empate, 0 derrota; orden descendente por pts, dg, gf."""
        eq_a = EquipoInterfichas.objects.create(
            ficha=201, programa="ADSO", nombre_equipo="Equipo A",
            capitan="Cap A", torneo=self.torneo, disciplina=self.disc_futbol)
        eq_b = EquipoInterfichas.objects.create(
            ficha=202, programa="ADSO", nombre_equipo="Equipo B",
            capitan="Cap B", torneo=self.torneo, disciplina=self.disc_futbol)
        g = GrupoInterfichas.objects.create(torneo=self.torneo, nombre_grupo="G")
        g.equipos.set([eq_a, eq_b])

        # A(local) 3-1 B  → A gana (3 pts), B pierde (0 pts)
        PartidoInterfichas.objects.create(
            torneo=self.torneo, grupo=g, fase="grupo",
            equipo_local=eq_a, equipo_visitante=eq_b,
            goles_local=3, goles_visitante=1, jugado=True)

        # A: pj=1, pg=1, pe=0, pp=0, gf=3, gc=1, dg=+2, pts=3
        # B: pj=1, pg=0, pe=0, pp=1, gf=1, gc=3, dg=-2, pts=0
        tabla = _calcular_tabla(g)
        stats = {row["equipo"].pk: row for row in tabla}
        a = stats[eq_a.pk]
        b = stats[eq_b.pk]
        self.assertEqual(a["pj"], 1)
        self.assertEqual(a["pg"], 1)
        self.assertEqual(a["gf"], 3)
        self.assertEqual(a["gc"], 1)
        self.assertEqual(a["dg"], 2)
        self.assertEqual(a["pts"], 3)
        self.assertEqual(b["pp"], 1)
        self.assertEqual(b["gf"], 1)
        self.assertEqual(b["gc"], 3)
        self.assertEqual(b["pts"], 0)
        # Orden descendente: A (3 pts) antes que B (0 pts)
        self.assertEqual(tabla[0]["equipo"], eq_a)
        self.assertEqual(tabla[1]["equipo"], eq_b)

    # ------------------------------------------------------------------
    # CP-INT-08 — Seguridad: sanitización de entrada (XSS almacenado).
    # `capitan` se renderiza vía innerHTML en el modal de equipos; si se
    # almacena HTML activo, es XSS almacenado. La app debe neutralizarlo.
    # ------------------------------------------------------------------
    def test_cp_int_08_sanitizacion_capitan_contra_xss_almacenado(self):
        """RB (falla): capitán con payload XSS debe almacenarse neutralizado."""
        self.client.login(username="aprendiz_audit", password="Password123*")
        xss_payload = "<img src=x onerror=alert(1)>"
        payload = {
            "accion_tipo": "inscribir_equipo",
            "torneo_id": self.torneo.pk,
            "ficha": "5556667",
            "programa": "ADSO",
            "capitan": xss_payload,
            "nombre_equipo": "Equipo XSS",
        }
        self.client.post("/interfichas/", payload)
        # El equipo debe haberse creado, pero el capitán debe estar sanitizado
        eq = EquipoInterfichas.objects.filter(torneo=self.torneo).first()
        self.assertIsNotNone(eq, "El equipo debe haberse creado.")
        # El payload activo NO debe estar presente tal cual (debe estar neutralizado)
        self.assertNotIn(
            "<img", eq.capitan,
            "capitan contiene HTML activo → XSS almacenado posible vía innerHTML.")
        self.assertNotIn("onerror", eq.capitan)

    # ------------------------------------------------------------------
    # CP-INT-09 — RBAC POSITIVO: un aprendiz NO puede crear torneos.
    # ------------------------------------------------------------------
    def test_cp_int_09_aprendiz_no_puede_crear_torneo(self):
        """RB (pasa): aprendiz es rechazado al intentar crear un torneo (302)."""
        self.client.login(username="aprendiz_audit", password="Password123*")
        before = TorneoInterfichas.objects.count()
        resp = self.client.post("/interfichas/", {
            "accion_tipo": "crear_torneo",
            "nombre": "Torneo Prohibido",
            "disciplina_id": self.disc_futbol.pk,
            "fecha": date.today().isoformat(),
            "horario": "09:00",
            "lugar": "Lugar",
            "estado": "activo",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(TorneoInterfichas.objects.count(), before)
        self.assertFalse(es_admin(self.aprendiz))

    # ------------------------------------------------------------------
    # CP-INT-10 — Negativo: ficha duplicada es rechazada a nivel vista
    # (control de unicidad por torneo, no solo cliente).
    # ------------------------------------------------------------------
    def test_cp_int_10_ficha_duplicada_rechazada_en_vista(self):
        """QC (pasa): la segunda inscripción con misma ficha en un torneo es rechazada."""
        self.client.login(username="aprendiz_audit", password="Password123*")
        base = {
            "accion_tipo": "inscribir_equipo",
            "torneo_id": self.torneo.pk,
            "ficha": "7788990",
            "programa": "ADSO",
            "capitan": "Capitán Único",
            "nombre_equipo": "Equipo Único",
        }
        resp1 = self.client.post("/interfichas/", base)
        self.assertEqual(resp1.status_code, 302)
        self.assertTrue(_ficha_duplicada(self.torneo, "7788990"))
        resp2 = self.client.post("/interfichas/", base)
        self.assertEqual(resp2.status_code, 302)
        # No debe crear un segundo equipo
        self.assertEqual(EquipoInterfichas.objects.filter(ficha=7788990).count(), 1)
