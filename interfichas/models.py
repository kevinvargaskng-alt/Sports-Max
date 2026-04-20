from django.db import models
from django.conf import settings

# 1. MODELO DE DISCIPLINAS
# Almacena los nombres: Fútbol, Baloncesto, etc.
class Disciplina(models.Model):
    nombre_disciplina = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre_disciplina


# 2. MODELO DE TORNEOS
# Representa el evento deportivo principal
class TorneoInterfichas(models.Model):
    codigo_torneo_fichas = models.AutoField(primary_key=True)
    nombre_torneo = models.CharField(max_length=100)
    fecha_torneo_fichas = models.DateField()
    horario_torneo_fichas = models.TimeField(default='08:00')
    lugar = models.CharField(max_length=100)
    
    # Relación con Disciplina
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True, related_name='torneos')
    
    estado = models.CharField(max_length=20, default='activo')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_torneo} ({self.disciplina})"
    


# 3. MODELO DE EQUIPOS
# Representa la inscripción de una ficha a un torneo específico
class EquipoInterfichas(models.Model):
    codigo_equipo_interfichas = models.AutoField(primary_key=True)
    
    # Datos de la Ficha y el Programa
    ficha = models.IntegerField() 
    programa = models.CharField(max_length=150) # ADSO, Minería, etc.
    nombre_equipo = models.CharField(max_length=100)
    
    # Campo de Capitán (Responsable del equipo)
    capitan = models.CharField(max_length=100)
    
    # Relaciones
    torneo = models.ForeignKey(TorneoInterfichas, on_delete=models.CASCADE, related_name='equipos')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True)
    
    # Quién realizó la inscripción (Aprendiz/Admin logueado)
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


# 4. MODELO DE JUGADORES (NÓMINA)
# Almacena la lista dinámica de aprendices por equipo
class JugadorEquipo(models.Model):
    nombre_completo = models.CharField(max_length=150)
    equipo = models.ForeignKey(EquipoInterfichas, on_delete=models.CASCADE, related_name='jugadores')

    def __str__(self):
        return self.nombre_completo
    
#resultados de los torneos, con relación uno a uno con el torneo para almacenar el ganador y fecha de cierre
class ResultadoTorneo(models.Model):
    torneo = models.OneToOneField('TorneoInterfichas', on_delete=models.CASCADE, related_name='resultado')
    ganador = models.ForeignKey('EquipoInterfichas', on_delete=models.SET_NULL, null=True, related_name='torneos_ganados')
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    archivado = models.BooleanField(default=False)

    def __str__(self):
        return f"Resultado de {self.torneo.nombre_torneo}"
    