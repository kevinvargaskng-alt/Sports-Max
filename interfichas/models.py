from django.db import models

class Disciplina(models.Model):
    nombre_disciplina = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre_disciplina

class TorneoInterfichas(models.Model):
    codigo_torneo_fichas = models.AutoField(primary_key=True)
    nombre_torneo = models.CharField(max_length=100)
    fecha_torneo_fichas = models.DateField()
    horario_torneo_fichas = models.TimeField()
    lugar = models.CharField(max_length=100)
    # CAMBIO: Relación con el modelo Disciplina
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, default='Activo')

    def __str__(self):
        return self.nombre_torneo

class EquipoInterfichas(models.Model):
    codigo_equipo_interfichas = models.AutoField(primary_key=True)
    # 0 para pasantes, o el número de ficha
    ficha = models.IntegerField() 
    # NUEVO: Para guardar el nombre del programa (ADSO, Minería, etc.)
    programa = models.CharField(max_length=100, null=True, blank=True)
    nombre_equipo = models.CharField(max_length=100)
    capitan = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='Inscrito')
    # CAMBIO: Relación con Disciplina
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True)
    torneo = models.ForeignKey(TorneoInterfichas, on_delete=models.CASCADE, related_name='equipos')

    def __str__(self):
        return f"{self.nombre_equipo} ({self.ficha})"

# NUEVO MODELO: Para guardar los nombres que agregas en la lista dinámica del JS
class JugadorEquipo(models.Model):
    nombre_completo = models.CharField(max_length=150)
    equipo = models.ForeignKey(EquipoInterfichas, on_delete=models.CASCADE, related_name='jugadores')

    def __str__(self):
        return self.nombre_completo