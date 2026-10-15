"""
Diagnostic tests to verify hypothesized vulnerabilities.
These are throwaway — will be removed after confirming behaviors.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from .models import ElementoDeportivo, Prestamo, Devolucion, Sancion


class DiagnosticTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="diag_user", password="Password123*",
            email="diag@sena.edu.co", numero_documento="11112222",
            rol="aprendiz"
        )
        self.admin = self.User.objects.create_user(
            username="diag_admin", password="Password123*",
            email="diagadmin@sena.edu.co", numero_documento="99998888",
            rol="administrador", is_staff=True
        )
        self.elemento = ElementoDeportivo.objects.create(
            tipo_maquina="Balón Diagnóstico", cantidad_total=5,
            estado_general="Bueno", habilitado=True
        )

    def test_diag_1_non_numeric_cantidad(self):
        """Does non-numeric cantidad_prestada crash?"""
        self.client.login(username="diag_user", password="Password123*")
        try:
            resp = self.client.post('/inventario/', {
                'accion': 'crear_prestamo',
                'elemento': self.elemento.id,
                'cantidad_prestada': 'abc',
                'dias_prestamo': 3,
            })
            print(f"\n[DIAG1] Response status: {resp.status_code}")
        except Exception as e:
            print(f"\n[DIAG1] CRASH: {type(e).__name__}: {e}")

    def test_diag_2_negative_cantidad(self):
        """Does negative cantidad_prestada crash or pass validation?"""
        self.client.login(username="diag_user", password="Password123*")
        try:
            resp = self.client.post('/inventario/', {
                'accion': 'crear_prestamo',
                'elemento': self.elemento.id,
                'cantidad_prestada': '-5',
                'dias_prestamo': 3,
            })
            print(f"\n[DIAG2] Response status: {resp.status_code}")
            print(f"[DIAG2] Préstamos created: {Prestamo.objects.filter(usuario=self.aprendiz).count()}")
            self.elemento.refresh_from_db()
            print(f"[DIAG2] Stock after: {self.elemento.cantidad_total}")
        except Exception as e:
            print(f"\n[DIAG2] CRASH: {type(e).__name__}: {e}")

    def test_diag_3_delete_element_with_active_prestamo(self):
        """Does deleting an element cascade-delete active préstamos?"""
        self.client.login(username="diag_admin", password="Password123*")
        prestamo = Prestamo.objects.create(
            usuario=self.aprendiz, elemento=self.elemento,
            cantidad_prestada=1, estado_prestamo='Activo',
            dias_prestamo=1
        )
        print(f"\n[DIAG3] Préstamo exists before delete: {Prestamo.objects.filter(codigo_prestamo=prestamo.codigo_prestamo).exists()}")
        self.client.get(f'/inventario/eliminar-elemento/{self.elemento.id}/')
        print(f"[DIAG3] Préstamo exists after delete: {Prestamo.objects.filter(codigo_prestamo=prestamo.codigo_prestamo).exists()}")
        print(f"[DIAG3] Elemento exists after delete: {ElementoDeportivo.objects.filter(id=self.elemento.id).exists()}")

    def test_diag_4_expired_sancion_blocks_loan(self):
        """Does a sanción with fecha_fin in past but estado='Activa' block loans?"""
        Sancion.objects.create(
            usuario=self.aprendiz, tipo_sancion="Test",
            fecha_inicio_sancion=date.today() - timedelta(days=10),
            fecha_fin_sancion=date.today() - timedelta(days=5),  # expired
            estado_sancion="Activa",
            descripcion_sancion="Test"
        )
        self.client.login(username="diag_user", password="Password123*")
        resp = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': 1,
            'dias_prestamo': 3,
        })
        print(f"\n[DIAG4] Response status: {resp.status_code}")
        print(f"[DIAG4] Préstamo created: {Prestamo.objects.filter(usuario=self.aprendiz).exists()}")
        print(f"[DIAG4] Sanción fecha_fin: {date.today() - timedelta(days=5)} (past)")
        print(f"[DIAG4] Sanción estado: Activa")

    def test_diag_5_edit_cantidad_total_string(self):
        """Does edit store cantidad_total as string (no int conversion)?"""
        self.client.login(username="diag_admin", password="Password123*")
        # Edit via POST to inventario_list
        self.client.post('/inventario/', {
            'accion': 'editar_elemento',
            'codigo_elemento': self.elemento.id,
            'nombre_elemento': 'Balón Editado',
            'cantidad_total': '99',
            'estado_general': 'Regular',
        })
        self.elemento.refresh_from_db()
        print(f"\n[DIAG5] cantidad_total type after edit: {type(self.elemento.cantidad_total).__name__}")
        print(f"[DIAG5] cantidad_total value: {self.elemento.cantidad_total}")

    def test_diag_6_sancion_creation_link(self):
        """Does auto-sancion link devolucion FK?"""
        prestamo = Prestamo.objects.create(
            usuario=self.aprendiz, elemento=self.elemento,
            cantidad_prestada=1, estado_prestamo='Activo', dias_prestamo=1
        )
        self.elemento.cantidad_total = 4
        self.elemento.save()
        self.client.login(username="diag_user", password="Password123*")
        self.client.post('/inventario/devoluciones/', {
            'accion': 'registrar_devolucion',
            'prestamo': prestamo.codigo_prestamo,
            'cantidad_devuelta': 1,
            'tiene_novedad': 'on',
            'estado_elemento_devolucion': 'Dañado',
            'tipo_novedad_devolucion': 'Daño',
            'observaciones_devolucion': 'Test daño'
        })
        sancion = Sancion.objects.filter(usuario=self.aprendiz).first()
        devolucion = Devolucion.objects.first()
        print(f"\n[DIAG6] Sancion devolucion FK: {sancion.devolucion}")
        print(f"[DIAG6] Devolucion: {devolucion}")
        print(f"[DIAG6] Sancion linked to devolucion: {sancion.devolucion == devolucion if sancion else 'N/A'}")

    def test_diag_7_non_staff_access_bloquear_morosos(self):
        """Does non-staff get 403 on bloquear_morosos?"""
        self.client.login(username="diag_user", password="Password123*")
        resp = self.client.post('/inventario/reportes/bloquear-morosos/', {
            'usuario_id': self.aprendiz.id
        })
        print(f"\n[DIAG7] Response status: {resp.status_code}")

    def test_diag_8_admin_cannot_create_prestamo(self):
        """Is admin blocked from creating préstamos?"""
        self.client.login(username="diag_admin", password="Password123*")
        resp = self.client.post('/inventario/', {
            'accion': 'crear_prestamo',
            'elemento': self.elemento.id,
            'cantidad_prestada': 1,
            'dias_prestamo': 3,
        })
        print(f"\n[DIAG8] Response status: {resp.status_code}")
        print(f"[DIAG8] Préstamo created for admin: {Prestamo.objects.filter(usuario=self.admin).exists()}")

    def test_diag_9_partial_return_over_restore(self):
        """Can you return items multiple times, over-restoring stock?"""
        prestamo = Prestamo.objects.create(
            usuario=self.aprendiz, elemento=self.elemento,
            cantidad_prestada=3, estado_prestamo='Activo', dias_prestamo=1
        )
        self.elemento.cantidad_total = 2  # borrowed 3, stock now 2
        self.elemento.save()
        self.client.login(username="diag_user", password="Password123*")
        # First return: 2 items
        self.client.post('/inventario/devoluciones/', {
            'accion': 'registrar_devolucion',
            'prestamo': prestamo.codigo_prestamo,
            'cantidad_devuelta': 2,
        })
        self.elemento.refresh_from_db()
        print(f"\n[DIAG9] Stock after first return (2 of 3): {self.elemento.cantidad_total}")
        print(f"[DIAG9] Préstamo estado: {prestamo.estado_prestamo}")
        # Préstamo still Active (not fully returned) - can we return again?
        # Note: the view filters by estado_prestamo='Activo' so second return should work
        # Second return: 2 items again (but only 1 was actually borrowed... wait, 3 was borrowed, 2 returned, 1 left)
        self.client.post('/inventario/devoluciones/', {
            'accion': 'registrar_devolucion',
            'prestamo': prestamo.codigo_prestamo,
            'cantidad_devuelta': 1,  # returning 1 more = total 3 returned
        })
        self.elemento.refresh_from_db()
        print(f"[DIAG9] Stock after second return (1 more): {self.elemento.cantidad_total}")
        # Now try to return 2 again (3 total borrowed so far, all returned)
        # prestamo still Active? Let's check
        prestamo.refresh_from_db()
        print(f"[DIAG9] Préstamo estado after 2nd return: {prestamo.estado_prestamo}")

    def test_diag_10_invalid_usuario_id_sancion(self):
        """Does creating sancion with invalid usuario_id crash?"""
        self.client.login(username="diag_admin", password="Password123*")
        try:
            resp = self.client.post('/inventario/sanciones/', {
                'accion': 'crear_sancion',
                'usuario_id': '99999',
                'tipo_sancion': 'Prueba',
                'fecha_inicio_sancion': date.today().strftime('%Y-%m-%d'),
                'fecha_fin_sancion': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'descripcion_sancion': 'Test'
            })
            print(f"\n[DIAG10] Response status: {resp.status_code}")
        except Exception as e:
            print(f"\n[DIAG10] CRASH: {type(e).__name__}: {e}")
