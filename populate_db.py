import os
import random
import django
from datetime import timedelta, time
from django.utils import timezone

# 1. Configurar el entorno de Django para usar modelos desde un script externo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. Importar los modelos
from usuarios.models import Usuario
from gimnasio.models import Reserva
from interfichas.models import (
    Disciplina, TorneoInterfichas, EquipoInterfichas, JugadorEquipo
)
from inventario.models import Prestamo
from core.constants import LISTA_PROGRAMAS
from django.apps import apps

# Intentar importar Elemento asumiendo su existencia por el HTML de inventario
try:
    Elemento = apps.get_model('inventario', 'Elemento')
except LookupError:
    print("Advertencia: No se encontró el modelo Elemento en la app inventario.")
    Elemento = None


def run_population():
    print("==== INICIANDO POBLAMIENTO DE BASE DE DATOS ====\n")

    # ==========================================
    # 1. TABLAS INDEPENDIENTES (BASES)
    # ==========================================
    
    # --- CREAR USUARIOS ---
    print("-> Creando 10 Usuarios (Aprendices)...")
    usuarios_creados = []
    for i in range(1, 12):
        doc = f"1000000{i}"
        if not Usuario.objects.filter(numero_documento=doc).exists():
            user = Usuario(
                username=doc,
                numero_documento=doc,
                email=f"aprendiz{i}@sena.edu.co",
                first_name=f"NombreAprendiz{i}",
                last_name=f"ApellidoAprendiz{i}",
                tipo_documento="CC",
                telefono=f"30000000{i:02d}",
                ficha="3196477",
                programa_formacion=random.choice(LISTA_PROGRAMAS),
                rol="aprendiz",
                estado="activo"
            )
            user.set_password("Sena2026*")
            user.save()
            usuarios_creados.append(user)
        else:
            usuarios_creados.append(Usuario.objects.get(numero_documento=doc))

    # --- CREAR DISCIPLINAS ---
    print("-> Creando 10 Disciplinas Deportivas...")
    nombres_disciplinas = [
        "Fútbol", "Baloncesto", "Voleibol", "Tenis de Mesa", "Ajedrez", 
        "Atletismo", "Natación", "Ciclismo", "Boxeo", "Taekwondo"
    ]
    disciplinas_creadas = []
    for nombre in nombres_disciplinas:
        disciplina, created = Disciplina.objects.get_or_create(nombre_disciplina=nombre)
        disciplinas_creadas.append(disciplina)

    # --- CREAR ELEMENTOS DE INVENTARIO ---
    elementos_creados = []
    if Elemento:
        print("-> Creando 10 Elementos de Inventario...")
        nombres_elementos = ["Balón de Fútbol", "Balón de Baloncesto", "Red de Voleibol", "Raquetas", 
                             "Pesas 5kg", "Lazo para saltar", "Colchoneta", "Aro", "Cronómetro", "Conos de Entrenamiento"]
        for i, nombre in enumerate(nombres_elementos):
            elemento, created = Elemento.objects.get_or_create(
                tipo_maquina=nombre,
                defaults={
                    'cantidad_total': random.randint(5, 20),
                    'estado_general': random.choice(['Bueno', 'Regular']),
                    'docente_responsable': "Instructor de Deportes",
                    'fecha_adquisicion': timezone.now().date() - timedelta(days=random.randint(10, 300)),
                    'descripcion': f"{nombre} en buen estado para los aprendices."
                }
            )
            elementos_creados.append(elemento)

    # ==========================================
    # 2. TABLAS DEPENDIENTES (CON CLAVES FORÁNEAS)
    # ==========================================
    
    # --- CREAR RESERVAS DEL GIMNASIO ---
    print("-> Creando 10 Reservas de Gimnasio...")
    for i in range(10):
        usuario_al_azar = random.choice(usuarios_creados)
        nombre_completo = f"{usuario_al_azar.first_name} {usuario_al_azar.last_name}"
        ahora = timezone.localtime(timezone.now())
        Reserva.objects.create(
            usuario_solicitante=nombre_completo,
            fecha_entrada=ahora.date() - timedelta(days=i),
            hora_entrada=time(random.randint(7, 16), 0),
            hora_prestamo=time(random.randint(7, 16), 0),
            fecha_permanencia=ahora.date() - timedelta(days=i),
            hora_salida=time(random.randint(8, 17), 30),
            fecha_salida=ahora.date() - timedelta(days=i),
            estado='Activo' if i == 0 else 'Finalizado'
        )

    # --- CREAR TORNEOS INTERFICHAS ---
    print("-> Creando 10 Torneos Interfichas...")
    torneos_creados = []
    for i in range(10):
        torneo = TorneoInterfichas.objects.create(
            nombre_torneo=f"Copa Interfichas {2026} - Edición {i+1}",
            fecha_torneo_fichas=timezone.now().date() + timedelta(days=random.randint(5, 60)),
            lugar=f"Cancha Principal {random.randint(1, 3)}",
            disciplina=random.choice(disciplinas_creadas)
        )
        torneos_creados.append(torneo)

    # --- CREAR EQUIPOS DE TORNEOS ---
    print("-> Creando 4 Equipos por Torneo (40 en total) y asignando Jugadores...")
    for torneo in torneos_creados:
        for i in range(4):
            usuario_lider = random.choice(usuarios_creados)
            
            equipo = EquipoInterfichas.objects.create(
                torneo=torneo,
                nombre_equipo=f"Equipo {i+1} - {torneo.nombre_torneo}"[:50],
                capitan=f"{usuario_lider.first_name} {usuario_lider.last_name}",
                ficha=usuario_lider.ficha,
                programa=usuario_lider.programa_formacion,
                disciplina=torneo.disciplina,
                usuario_registra=usuario_lider
            )

            # Agregar 5 jugadores por equipo
            for j in range(5):
                JugadorEquipo.objects.create(
                    nombre_completo=f"Jugador {j+1} - {equipo.nombre_equipo}"[:50],
                    equipo=equipo
                )

    # --- CREAR PRÉSTAMOS DE INVENTARIO ---
    if elementos_creados:
        print("-> Creando 10 Préstamos de Inventario...")
        for i in range(10):
            Prestamo.objects.create(
                usuario=random.choice(usuarios_creados),
                elemento=random.choice(elementos_creados),
                cantidad_prestada=random.randint(1, 3),
                fecha_devolucion=timezone.now().date() + timedelta(days=random.randint(1, 5)),
                estado_prestamo=random.choice(['Activo', 'Devuelto'])
            )

    print("\n==== POBLAMIENTO COMPLETADO EXITOSAMENTE ====")

if __name__ == '__main__':
    run_population()