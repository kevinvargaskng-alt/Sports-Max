import os
import sys
import django
import random
from datetime import date, timedelta
from django.utils import timezone

# Add the project root to sys.path since this script will be in the 'scripts' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from usuarios.models import Usuario, Sugerencia
from inventario.models import ElementoDeportivo, Prestamo
from gimnasio.models import Reserva
from interfichas.models import TorneoInterfichas, EquipoInterfichas, Disciplina
def poblar_datos():
    print("🚀 Iniciando la población de la base de datos...")

    # 1. Crear Usuarios (Admins, Instructores, Aprendices)
    programas = [
        'ADSO', 'MINERIA', 'SST', 'QUIMICA', 'TOPOGRAFIA', 
        'VIAL', 'SANEAMIENTO', 'MAQUINARIA_PESADA', 'MANTENIMIENTO_EQUIPO'
    ]
    
    # 1. Crear Admin principal
    admin_user, admin_created = Usuario.objects.get_or_create(
        username="0000000000",
        defaults={
            'email': "admin_principal@sena.edu.co",
            'first_name': "Admin",
            'last_name': "Principal",
            'numero_documento': "0000000000",
            'tipo_documento': 'CC',
            'telefono': "3000000000",
            'ficha': "N/A",
            'programa_formacion': 'ADSO',
            'rol': 'admin',
            'estado': 'activo',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if admin_created:
        admin_user.set_password('@dmin123')
        admin_user.save()
    usuarios_creados = [admin_user]

    # Crear Usuarios adicionales (Instructores, Aprendices)
    for i in range(1, 15):
        username = f"1000000{i}"
        rol = 'instructor' if i <= 5 else 'aprendiz'
        user, created = Usuario.objects.get_or_create(
            username=username,
            defaults={
                'email': f"usuario{i}@sena.edu.co",
                'first_name': f"Nombre{i}",
                'last_name': f"Apellido{i}",
                'numero_documento': username,
                'tipo_documento': 'CC',
                'telefono': f"31000000{i:02d}",
                'ficha': f"2670{i:02d}",
                'programa_formacion': random.choice(programas),
                'rol': rol,
                'estado': 'activo',
                'is_staff': False,
            }
        )
        if created:
            user.set_password('Sena1234')
            user.save()
        usuarios_creados.append(user)
    print(f"✅ {len(usuarios_creados)} Usuarios listos.")

    # 2. Disciplinas
    nombres_disciplinas = ["Fútbol", "Baloncesto", "Voleibol", "Tenis de Mesa", "Ajedrez", "Atletismo", "Natación", "Fútbol Sala", "Taekwondo", "Billar"]
    disciplinas_objs = []
    for nombre in nombres_disciplinas:
        d, _ = Disciplina.objects.get_or_create(nombre_disciplina=nombre)
        disciplinas_objs.append(d)
    print("✅ Disciplinas creadas.")

    # 3. Elementos Deportivos (Inventario)
    elementos_nombres = ["Balón de Fútbol", "Mesa de Ping Pong", "Mesa de Billar", "Pesa 10kg", "Colchoneta", "Balón Baloncesto", "Net de Voleibol", "Cronómetro", "Cinta Métrica", "Set de Ajedrez"]
    elementos_objs = []
    for i, nombre in enumerate(elementos_nombres):
        e, _ = ElementoDeportivo.objects.get_or_create(
            tipo_maquina=nombre,
            defaults={
                'cantidad_total': random.randint(5, 20),
                'estado_general': random.choice(['Bueno', 'Regular']),
                'usuario_responsable': random.choice(usuarios_creados) if usuarios_creados else None
            }
        )
        elementos_objs.append(e)
    print("✅ Inventario poblado.")

    # 4. Torneos Interfichas
    for i in range(1, 11):
        t, _ = TorneoInterfichas.objects.get_or_create(
            nombre_torneo=f"Torneo Interfichas {random.choice(nombres_disciplinas)} Q{i}",
            defaults={
                'fecha_torneo_fichas': date.today() + timedelta(days=i*7),
                'lugar': "Cancha Principal Centro Minero",
                'disciplina': random.choice(disciplinas_objs),
                'estado': 'activo'
            }
        )
        # Crear Equipos para este torneo
        for j in range(1, 5):
            EquipoInterfichas.objects.get_or_create(
                torneo=t,
                nombre_equipo=f"Equipo {t.pk}-{j}",
                defaults={
                    'capitan': f"Aprendiz Lider {j}",
                    'ficha': f"27{random.randint(100,999)}",
                    'programa': random.choice(programas),
                    'disciplina': t.disciplina,
                    'usuario_registra': random.choice(usuarios_creados)
                }
            )
    print("✅ Torneos Interfichas y Equipos creados.")

    from inventario.models import DetallePrestamo
    # 6. Préstamos
    for i in range(1, 11):
        p = Prestamo.objects.create(
            usuario=random.choice(usuarios_creados),
            dias_prestamo=2,
            estado_prestamo='Activo'
        )
        DetallePrestamo.objects.create(
            prestamo=p,
            elemento=random.choice(elementos_objs),
            fecha_devolucion_prevista=date.today() + timedelta(days=2),
            estado='Pendiente'
        )
    print("✅ Préstamos registrados.")

    # 7. Reservas Gimnasio
    from datetime import time
    for i in range(1, 11):
        u = random.choice(usuarios_creados)
        fecha_reserva = date.today() + timedelta(days=i)
        Reserva.objects.get_or_create(
            usuario_solicitante=u,
            fecha_entrada=fecha_reserva,
            hora_entrada=time(8, 0),
            defaults={
                'fecha_salida': fecha_reserva,
                'hora_salida': time(9, 0),
                'tiempo_permanencia': 60,
                'estado': 'Pendiente'
            }
        )
    print("✅ Reservas de gimnasio creadas.")

    # 8. Sugerencias
    tipos_sug = ['Mejora', 'Queja', 'Felicitación']
    for i in range(1, 11):
        anon = random.choice([True, False])
        Sugerencia.objects.create(
            usuario=None if anon else random.choice(usuarios_creados),
            tipo=random.choice(tipos_sug),
            comentario=f"Sugerencia de prueba número {i} sobre las instalaciones.",
            anonimo=anon,
            fecha=timezone.now()
        )
    print("✅ Sugerencias creadas.")

    print("\n✨ ¡Base de datos poblada con éxito!")

if __name__ == '__main__':
    poblar_datos()