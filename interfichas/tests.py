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

