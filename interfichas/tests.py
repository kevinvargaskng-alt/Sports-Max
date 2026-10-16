from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from .models import Disciplina, TorneoInterfichas, EquipoInterfichas, JugadorEquipo, PartidoInterfichas

class InterfichasAppTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="aprendiz_torneo",
            password="password123",
            email="torneo@sena.edu.co",
            numero_documento="77776666"
        )
        self.disciplina = Disciplina.objects.create(
            nombre_disciplina="Microfútbol",
            tipo_marcador="goles",
            reglas="Dos tiempos de 20 minutos cada uno."
        )
        self.torneo = TorneoInterfichas.objects.create(
            nombre_torneo="Torneo Relámpago Fútsal Centro Minero",
            fecha_torneo_fichas=date.today(),
            lugar="Cancha Sintética Principal",
            disciplina=self.disciplina,
            estado="activo"
        )

    def test_creacion_disciplina_y_torneo(self):
        """Prueba que la disciplina y el torneo se registren correctamente."""
        self.assertEqual(self.disciplina.nombre_disciplina, "Microfútbol")
        self.assertEqual(self.torneo.nombre_torneo, "Torneo Relámpago Fútsal Centro Minero")

    def test_inscripcion_equipo_y_jugadores(self):
        """Prueba que se pueda crear un equipo y añadir jugadores."""
        equipo = EquipoInterfichas.objects.create(
            ficha=2721445,
            programa="Análisis y Desarrollo de Software",
            nombre_equipo="ADSO 445 FC",
            capitan="Juan Pérez",
            torneo=self.torneo,
            disciplina=self.disciplina,
            usuario_registra=self.usuario,
            estado="Inscrito"
        )
        jugador = JugadorEquipo.objects.create(
            nombre_completo="Juan Pérez",
            equipo=equipo
        )
        self.assertEqual(equipo.nombre_equipo, "ADSO 445 FC")
        self.assertEqual(jugador.equipo, equipo)

    def test_registro_partido_y_resultado(self):
        """Prueba la creación de un partido y el cálculo automático de puntos."""
        eq1 = EquipoInterfichas.objects.create(
            ficha=11111,
            programa="Mantenimiento",
            nombre_equipo="Mecánicos FC",
            capitan="Carlos",
            torneo=self.torneo,
            disciplina=self.disciplina
        )
        eq2 = EquipoInterfichas.objects.create(
            ficha=22222,
            programa="Topografía",
            nombre_equipo="Topos FC",
            capitan="Luis",
            torneo=self.torneo,
            disciplina=self.disciplina
        )
        partido = PartidoInterfichas.objects.create(
            torneo=self.torneo,
            fase="grupo",
            equipo_local=eq1,
            equipo_visitante=eq2,
            fecha_partido=date.today(),
            goles_local=3,
            goles_visitante=1,
            jugado=True
        )
        self.assertEqual(partido.puntos_local(), 3)
        self.assertEqual(partido.puntos_visitante(), 0)
        self.assertEqual(partido.tipo_marcador, "goles")

    def test_cp20_registro_torneo_por_instructor_y_persistencia_estado_inicial(self):
        """CP-20: Validar registro de torneos y persistencia de estado inicial por parte de un Instructor."""
        instructor = self.User.objects.create_user(
            username="instructor_deportes",
            password="password123",
            email="instructor@sena.edu.co",
            numero_documento="55443322",
            rol="instructor"
        )
        self.client.login(username="instructor_deportes", password="password123")

        fecha_torneo = date.today().isoformat()
        resp = self.client.post('/interfichas/', {
            'accion_tipo': 'crear_torneo',
            'nombre': 'Torneo Voleibol Interfichas 2026',
            'disciplina_id': self.disciplina.pk,
            'fecha': fecha_torneo,
            'horario': '09:00',
            'lugar': 'Coliseo Polideportivo',
            'estado': 'programado'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['nombre'], 'Torneo Voleibol Interfichas 2026')
        self.assertEqual(data['estado'], 'programado')

        # Validar persistencia en modelo relacional
        torneo_db = TorneoInterfichas.objects.get(pk=data['torneo_id'])
        self.assertEqual(torneo_db.nombre_torneo, 'Torneo Voleibol Interfichas 2026')
        self.assertEqual(str(torneo_db.fecha_torneo_fichas), fecha_torneo)
        self.assertEqual(torneo_db.estado, 'programado')
        self.assertEqual(torneo_db.disciplina, self.disciplina)
        self.assertEqual(torneo_db.lugar, 'Coliseo Polideportivo')

    def test_gestionar_torneo_con_grupos_y_calculo_tabla(self):
        """Prueba que la vista gestionar_torneo y _calcular_tabla funcionen correctamente con equipos y grupos."""
        from .models import GrupoInterfichas
        admin = self.User.objects.create_user(
            username="admin_torneo",
            password="password123",
            email="admin_torneo@sena.edu.co",
            numero_documento="11223344",
            rol="admin",
            is_staff=True
        )
        eq1 = EquipoInterfichas.objects.create(
            ficha=3001,
            programa="ADSO",
            nombre_equipo="Team 1",
            capitan="Capitan 1",
            torneo=self.torneo,
            disciplina=self.disciplina
        )
        eq2 = EquipoInterfichas.objects.create(
            ficha=3002,
            programa="ADSO",
            nombre_equipo="Team 2",
            capitan="Capitan 2",
            torneo=self.torneo,
            disciplina=self.disciplina
        )
        grupo = GrupoInterfichas.objects.create(torneo=self.torneo, nombre_grupo="A")
        grupo.equipos.add(eq1, eq2)

        PartidoInterfichas.objects.create(
            torneo=self.torneo,
            grupo=grupo,
            fase="grupo",
            equipo_local=eq1,
            equipo_visitante=eq2,
            fecha_partido=date.today(),
            goles_local=2,
            goles_visitante=1,
            jugado=True
        )

        self.client.login(username="admin_torneo", password="password123")
        resp = self.client.get(f'/interfichas/torneo/{self.torneo.pk}/')
        self.assertEqual(resp.status_code, 200)
        # Verificar que el atributo id/pk funcione en la plantilla y en la lógica
        self.assertEqual(eq1.id, eq1.pk)
        self.assertEqual(self.torneo.id, self.torneo.pk)

    def test_interfichas_list_render_admin_y_aprendiz(self):
        """Verifica que /interfichas/ cargue correctamente tanto para admin como para aprendiz sin UnboundLocalError."""
        # Usuario aprendiz
        self.client.login(username="aprendiz_torneo", password="password123")
        resp_user = self.client.get('/interfichas/')
        self.assertEqual(resp_user.status_code, 200)
        self.assertIn('total_equipos_inscritos', resp_user.context)

        # Usuario admin
        admin = self.User.objects.create_user(
            username="admin_list_test",
            password="password123",
            email="admin_list@sena.edu.co",
            numero_documento="99887766",
            rol="admin",
            is_staff=True
        )
        self.client.login(username="admin_list_test", password="password123")
        resp_admin = self.client.get('/interfichas/')
        self.assertEqual(resp_admin.status_code, 200)
        self.assertIn('total_equipos_inscritos', resp_admin.context)


class TestInterfichasQAQC(TestCase):
    """Batería de Pruebas QA/QC para el Módulo de Torneos y Juegos Interfichas."""

    def setUp(self):
        self.User = get_user_model()
        self.aprendiz = self.User.objects.create_user(
            username="aprendiz_torneos_qa",
            password="Password123*",
            email="torneos_qa@sena.edu.co",
            numero_documento="88776655",
            rol="aprendiz"
        )
        self.disciplina_futbol = Disciplina.objects.create(
            nombre_disciplina="Fútbol 8",
            tipo_marcador="goles"
        )
        self.disciplina_volei = Disciplina.objects.create(
            nombre_disciplina="Voleibol Mixto",
            tipo_marcador="sets"
        )
        self.torneo = TorneoInterfichas.objects.create(
            nombre_torneo="Copa Integración SENA 2026",
            fecha_torneo_fichas=date.today(),
            lugar="Cancha Múltiple Centro Minero",
            disciplina=self.disciplina_futbol,
            estado="activo"
        )

    def test_cp_int_01_inscripcion_equipo_con_ficha(self):
        """CP-INT-01 (Positivo): Registro de equipo con número de ficha, programa y capitán."""
        equipo = EquipoInterfichas.objects.create(
            ficha=2849102,
            programa="Gestión de Seguridad y Salud en el Trabajo",
            nombre_equipo="Seguridad Titanes FC",
            capitan="Carlos Rincón",
            torneo=self.torneo,
            disciplina=self.disciplina_futbol,
            usuario_registra=self.aprendiz,
            estado="Inscrito"
        )
        self.assertEqual(equipo.ficha, 2849102)
        self.assertEqual(equipo.estado, 'Inscrito')
        self.assertEqual(equipo.usuario_registra, self.aprendiz)
        self.assertEqual(str(equipo), "Seguridad Titanes FC - Ficha: 2849102")

    def test_cp_int_02_calculo_marcador_empate_y_victorias(self):
        """CP-INT-02 (Límite & QC Lógica): Validación de cálculo de puntos en caso de victoria (3-0) y empate (1-1)."""
        eq_a = EquipoInterfichas.objects.create(ficha=101, programa="ADSO", nombre_equipo="Equipo A", capitan="Cap A", torneo=self.torneo, disciplina=self.disciplina_futbol)
        eq_b = EquipoInterfichas.objects.create(ficha=102, programa="SST", nombre_equipo="Equipo B", capitan="Cap B", torneo=self.torneo, disciplina=self.disciplina_futbol)

        # Caso 1: Partido con empate 0 - 0 (Límite inferior de goles)
        partido_empate = PartidoInterfichas.objects.create(
            torneo=self.torneo,
            equipo_local=eq_a,
            equipo_visitante=eq_b,
            goles_local=0,
            goles_visitante=0,
            jugado=True
        )
        self.assertEqual(partido_empate.puntos_local(), 1)
        self.assertEqual(partido_empate.puntos_visitante(), 1)

        # Caso 2: Victoria Local
        partido_empate.goles_local = 3
        partido_empate.goles_visitante = 1
        partido_empate.save()
        self.assertEqual(partido_empate.puntos_local(), 3)
        self.assertEqual(partido_empate.puntos_visitante(), 0)

        # Caso 3: Victoria Visitante
        partido_empate.goles_local = 1
        partido_empate.goles_visitante = 2
        partido_empate.save()
        self.assertEqual(partido_empate.puntos_local(), 0)
        self.assertEqual(partido_empate.puntos_visitante(), 3)

    def test_cp_int_03_sets_voleibol_y_formato_resultado(self):
        """CP-INT-03 (Funcional): Registro y representación formateada de parciales por sets en Voleibol."""
        torneo_volei = TorneoInterfichas.objects.create(
            nombre_torneo="Torneo Voleibol Centro Minero",
            fecha_torneo_fichas=date.today(),
            lugar="Coliseo",
            disciplina=self.disciplina_volei
        )
        eq_v1 = EquipoInterfichas.objects.create(ficha=201, programa="Topografía", nombre_equipo="Topos Voley", capitan="Cap T", torneo=torneo_volei, disciplina=self.disciplina_volei)
        eq_v2 = EquipoInterfichas.objects.create(ficha=202, programa="Minería", nombre_equipo="Mineros Voley", capitan="Cap M", torneo=torneo_volei, disciplina=self.disciplina_volei)

        partido_volei = PartidoInterfichas.objects.create(
            torneo=torneo_volei,
            equipo_local=eq_v1,
            equipo_visitante=eq_v2,
            sets_local=[25, 23, 15],
            sets_visitante=[20, 25, 10],
            jugado=True
        )
        self.assertEqual(partido_volei.tipo_marcador, 'sets')
        self.assertEqual(partido_volei.sets_str, '25-20, 23-25, 15-10')



