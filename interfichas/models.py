from django.db import models
from django.conf import settings

# 1. MODELO DE DISCIPLINAS
class Disciplina(models.Model):
    nombre_disciplina = models.CharField(max_length=50, unique=True)
    icono = models.CharField(max_length=60, default='fa-medal')
    reglas = models.TextField(blank=True, default='')

    def __str__(self):
        return self.nombre_disciplina


# 2. MODELO DE TORNEOS
class TorneoInterfichas(models.Model):
    codigo_torneo_fichas = models.AutoField(primary_key=True)
    nombre_torneo = models.CharField(max_length=100)
    fecha_torneo_fichas = models.DateField()
    horario_torneo_fichas = models.TimeField(default='08:00')
    lugar = models.CharField(max_length=100)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True, related_name='torneos')
    estado = models.CharField(max_length=20, default='activo')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_torneo} ({self.disciplina})"


# 3. MODELO DE EQUIPOS
class EquipoInterfichas(models.Model):
    codigo_equipo_interfichas = models.AutoField(primary_key=True)
    ficha = models.IntegerField()
    programa = models.CharField(max_length=150)
    nombre_equipo = models.CharField(max_length=100)
    capitan = models.CharField(max_length=100)
    torneo = models.ForeignKey(TorneoInterfichas, on_delete=models.CASCADE, related_name='equipos')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True)
    usuario_registra = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_inscripcion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Inscrito')

    def __str__(self):
        return f"{self.nombre_equipo} - Ficha: {self.ficha}"


# 4. MODELO DE JUGADORES
class JugadorEquipo(models.Model):
    nombre_completo = models.CharField(max_length=150)
    equipo = models.ForeignKey(EquipoInterfichas, on_delete=models.CASCADE, related_name='jugadores')

    def __str__(self):
        return self.nombre_completo


# 5. MODELO DE GRUPOS
class GrupoInterfichas(models.Model):
    torneo = models.ForeignKey(TorneoInterfichas, on_delete=models.CASCADE, related_name='grupos')
    nombre_grupo = models.CharField(max_length=10)  # "A", "B", "C", "D"
    equipos = models.ManyToManyField(EquipoInterfichas, related_name='grupos')

    def __str__(self):
        return f"Grupo {self.nombre_grupo} - {self.torneo.nombre_torneo}"


# 6. MODELO DE PARTIDOS
FASE_CHOICES = [
    ('grupo', 'Fase de Grupos'),
    ('cuartos', 'Cuartos de Final'),
    ('semifinal', 'Semifinal'),
    ('final', 'Final'),
]

class PartidoInterfichas(models.Model):
    torneo = models.ForeignKey(TorneoInterfichas, on_delete=models.CASCADE, related_name='partidos')
    grupo = models.ForeignKey(GrupoInterfichas, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos')
    fase = models.CharField(max_length=20, choices=FASE_CHOICES, default='grupo')

    equipo_local = models.ForeignKey(EquipoInterfichas, on_delete=models.CASCADE, related_name='partidos_local')
    equipo_visitante = models.ForeignKey(EquipoInterfichas, on_delete=models.CASCADE, related_name='partidos_visitante')

    fecha_partido = models.DateField(null=True, blank=True)
    hora_partido = models.TimeField(null=True, blank=True)

    goles_local = models.IntegerField(null=True, blank=True)
    goles_visitante = models.IntegerField(null=True, blank=True)
    jugado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.equipo_local} vs {self.equipo_visitante} ({self.fase})"

    def puntos_local(self):
        if not self.jugado:
            return 0
        if self.goles_local > self.goles_visitante:
            return 3
        elif self.goles_local == self.goles_visitante:
            return 1
        return 0

    def puntos_visitante(self):
        if not self.jugado:
            return 0
        if self.goles_visitante > self.goles_local:
            return 3
        elif self.goles_local == self.goles_visitante:
            return 1
        return 0


# 7. RESULTADOS DE TORNEOS
class ResultadoTorneo(models.Model):
    torneo = models.OneToOneField('TorneoInterfichas', on_delete=models.CASCADE, related_name='resultado')
    ganador = models.ForeignKey('EquipoInterfichas', on_delete=models.SET_NULL, null=True, related_name='torneos_ganados')
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    archivado = models.BooleanField(default=False)

    def __str__(self):
        return f"Resultado de {self.torneo.nombre_torneo}"