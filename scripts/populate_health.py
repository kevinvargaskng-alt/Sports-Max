# populate_health.py - Poblado de datos de Hábitos Saludables
import os
import sys
import django

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from habitos_saludables.models import HabitoSaludable, RutinaFisica, MaterialApoyo, PiramideNutricional

def populate():
    print("Iniciando poblado de Hábitos Saludables...")

    # 1. Eliminar datos existentes para limpiar
    HabitoSaludable.objects.all().delete()
    RutinaFisica.objects.all().delete()
    MaterialApoyo.objects.all().delete()
    
    # 2. Crear Hábitos Saludables
    habitos_data = [
        {
            'titulo': 'Hidratación Diaria',
            'categoria': 'hidratacion',
            'descripcion': (
                'El agua es esencial para todas las funciones del organismo. Mantenerse bien hidratado '
                'mejora el rendimiento físico, la concentración mental, ayuda a regular la temperatura corporal '
                'y facilita la digestión y eliminación de toxinas.'
            ),
            'consejos': (
                'Toma al menos 2-3 litros de agua al día.\n'
                'Lleva contigo siempre un termo de agua reutilizable a las aulas y gimnasio.\n'
                'Bebe agua antes, durante y después de cualquier actividad física.\n'
                'No esperes a tener sed para beber agua; la sed es un síntoma temprano de deshidratación.'
            ),
            'imagen': 'habitos/imagenes/hydration.png',
            'icono_css': 'bi-droplet-half'
        },
        {
            'titulo': 'Higiene y Calidad del Sueño',
            'categoria': 'sueno',
            'descripcion': (
                'El sueño reparador de calidad es fundamental para la recuperación muscular, '
                'la consolidación de la memoria y la salud del sistema inmunitario. No dormir lo suficiente '
                'está asociado a menor productividad, fatiga crónica y mayor nivel de estrés.'
            ),
            'consejos': (
                'Duerme entre 7 y 8 horas continuas todas las noches.\n'
                'Establece un horario fijo para acostarte y levantarte, incluso los fines de semana.\n'
                'Mantén tu habitación completamente oscura, silenciosa y a una temperatura agradable.\n'
                'Evita usar teléfonos móviles, tabletas o computadores al menos 1 hora antes de dormir.'
            ),
            'imagen': 'habitos/imagenes/sleep.png',
            'icono_css': 'bi-moon-stars'
        },
        {
            'titulo': 'Nutrición Balanceada',
            'categoria': 'alimentacion',
            'descripcion': (
                'Una alimentación saludable proporciona los nutrientes necesarios para el correcto funcionamiento '
                'de nuestro cuerpo. Priorizar alimentos frescos y naturales nos protege contra enfermedades '
                'crónicas no transmisibles y mejora la vitalidad.'
            ),
            'consejos': (
                'Asegúrate de incluir una porción de proteína magra, verduras y frutas en tus comidas principales.\n'
                'Reduce al mínimo el consumo de alimentos ultraprocesados, gaseosas y azúcares añadidos.\n'
                'Planifica tus porciones diarias según tu nivel de entrenamiento y actividad física.'
            ),
            'imagen': 'habitos/imagenes/nutrition.png',
            'icono_css': 'bi-egg-fried'
        },
        {
            'titulo': 'Salud Mental y Manejo de Estrés',
            'categoria': 'mental',
            'descripcion': (
                'La salud mental es tan importante como la física. Aprender a gestionar el estrés académico '
                'y laboral previene trastornos como la ansiedad y el agotamiento mental (burnout), '
                'mejorando nuestras relaciones y bienestar general.'
            ),
            'consejos': (
                'Dedica al menos 10 minutos al día a respirar profundamente o realizar meditación guiada.\n'
                'Mantén un equilibrio saludable entre el tiempo de estudio, la actividad deportiva y el ocio.\n'
                'Habla abiertamente sobre tus emociones con amigos, familiares o psicólogos si te sientes abrumado.'
            ),
            'icono_css': 'bi-emoji-smile'
        }
    ]

    for h in habitos_data:
        HabitoSaludable.objects.create(**h)
    print("[OK] Habitos Saludables creados con exito.")

    # 3. Crear Rutinas Físicas
    rutinas_data = [
        {
            'nombre': 'Rutina de Cardio y Quema de Grasa',
            'nivel': 'principiante',
            'objetivo': 'cardio',
            'descripcion': (
                'Rutina dinámica diseñada para activar el metabolismo, mejorar la resistencia cardiovascular '
                'y promover el gasto calórico de forma sencilla sin equipamiento.'
            ),
            'duracion_minutos': 20,
            'ejercicios': (
                'Jumping Jacks (3 series de 30 segundos)\n'
                'Sentadillas libres con el peso corporal (3 series de 15 repeticiones)\n'
                'Rodillas al pecho / Skip medio (3 series de 30 segundos)\n'
                'Flexiones de rodillas / Escaladores (3 series de 20 segundos)\n'
                'Descanso de 1 minuto entre cada serie completa.'
            ),
            'imagen': 'rutinas/imagenes/cardio.png'
        },
        {
            'nombre': 'Rutina de Calistenia y Fuerza Corporal',
            'nivel': 'intermedio',
            'objetivo': 'fuerza',
            'descripcion': (
                'Rutina enfocada en desarrollar fuerza funcional y tono muscular utilizando únicamente '
                'la resistencia del propio peso del cuerpo.'
            ),
            'duracion_minutos': 30,
            'ejercicios': (
                'Flexiones de pecho estándar / Push-ups (4 series de 12 repeticiones)\n'
                'Sentadillas con salto / Jump Squats (4 series de 15 repeticiones)\n'
                'Zancadas alternadas hacia atrás (4 series de 10 repeticiones por pierna)\n'
                'Fondos en silla o banco / Tricep Dips (4 series de 12 repeticiones)\n'
                'Plancha abdominal clásica (4 series de 45 segundos).'
            ),
            'imagen': 'rutinas/imagenes/strength.png'
        },
        {
            'nombre': 'Rutina de Flexibilidad y Postura',
            'nivel': 'principiante',
            'objetivo': 'flexibilidad',
            'descripcion': (
                'Rutina de estiramientos orientada a aliviar tensiones musculares acumuladas por estar '
                'sentado durante las clases, mejorando la postura y la movilidad articular.'
            ),
            'duracion_minutos': 15,
            'ejercicios': (
                'Estiramiento de isquiotibiales sentado (2 series de 30 segundos)\n'
                'Estiramiento de flexores de cadera en zancada (2 series de 30 segundos por lado)\n'
                'Estiramiento de pecho y hombros contra pared (2 series de 30 segundos)\n'
                'Postura del niño / Child\'s pose (Estiramiento lumbar - mantener 2 minutos)\n'
                'Rotaciones espinales tumbado (1 minuto por cada lado).'
            )
        }
    ]

    for r in rutinas_data:
        RutinaFisica.objects.create(**r)
    print("[OK] Rutinas Fisicas creadas con exito.")

    # 4. Crear Materiales de Apoyo
    materiales_data = [
        {
            'titulo': 'Guía de Nutrición Deportiva SENA',
            'tipo_contenido': 'pdf',
            'descripcion': 'Manual técnico con recomendaciones nutricionales específicas para aprendices deportistas.',
            'activo': True
        },
        {
            'titulo': 'Manual de Higiene del Sueño',
            'tipo_contenido': 'pdf',
            'descripcion': 'Documento con consejos prácticos para optimizar el descanso nocturno y rendir mejor en la formación.',
            'activo': True
        },
        {
            'titulo': 'Infografía de Pausas Activas',
            'tipo_contenido': 'infografia',
            'descripcion': 'Ejercicios de estiramiento y movilidad rápida recomendados durante las horas de estudio.',
            'activo': True
        }
    ]

    for m in materiales_data:
        MaterialApoyo.objects.create(**m)
    print("[OK] Materiales de Apoyo creados con exito.")

if __name__ == '__main__':
    populate()
    print("¡Poblado completo!")
