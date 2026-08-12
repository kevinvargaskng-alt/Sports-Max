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
