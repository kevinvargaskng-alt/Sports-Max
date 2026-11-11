import os
import sys
import django
import random
from datetime import date, time, timedelta
from django.utils import timezone

# Configurar encoding para evitar fallos de charmap en consolas de Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 1. CONFIGURACIÓN DEL ENTORNO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. IMPORTS DE MODELOS
from usuarios.models import Usuario, Sugerencia, HistorialAccion, Notificacion
from interfichas.models import (
    Disciplina, TorneoInterfichas, EquipoInterfichas,
    JugadorEquipo, GrupoInterfichas, PartidoInterfichas, ResultadoTorneo
)
from gimnasio.models import (
    Reserva as ReservaGimnasio, FranjaHoraria, GimnasioConfig,
    FechaIngreso, Maquina, Machine
)
from inventario.models import (
    ElementoDeportivo, Prestamo, DetallePrestamo,
    Devolucion, Revision, Sancion
)
from habitos_saludables.models import (
    HabeasDataConsent, HabitoSaludable, RutinaFisica,
    PiramideNutricional, MaterialApoyo, SeguimientoSalud,
    RecetaSaludable, RegistroHabitoUsuario, RegistroSueno, RegistroSesionRutina
)


def poblar_datos():
    print("[*] Iniciando la poblacion completa de la base de datos SportMax...")

    programas = [
        'ADSO', 'MINERIA', 'SST', 'QUIMICA', 'TOPOGRAFIA',
        'VIAL', 'SANEAMIENTO', 'MAQUINARIA_PESADA', 'MANTENIMIENTO_EQUIPO'
    ]

    # ─────────────────────────────────────────────────────────────
    # 1. USUARIOS
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Usuarios...")
    admin_user, admin_created = Usuario.objects.get_or_create(
        username="0000000000",
        defaults={
            'email': "admin_principal@sena.edu.co",
            'first_name': "Admin",
            'last_name': "Principal",
            'numero_documento': "0000000000",
            'tipo_documento': 'CC',
            'telefono': "3001234567",
            'ficha': "",
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

    # Crear Instructores y Aprendices
    for i in range(1, 16):
        username = f"1000000{i:02d}"
        email_cand = f"usuario{i}@sena.edu.co"
        rol = 'instructor' if i <= 5 else 'aprendiz'
        is_staff = (rol == 'instructor')
        user = Usuario.objects.filter(username=username).first() or Usuario.objects.filter(email=email_cand).first()
        if not user:
            user = Usuario.objects.create(
                username=username,
                email=email_cand,
                first_name=f"Usuario{i}",
                last_name=f"Sena{i}",
                numero_documento=username,
                tipo_documento='CC',
                telefono=f"31012345{i:02d}",
                ficha=f"26700{i:02d}" if rol == 'aprendiz' else "",
                programa_formacion=random.choice(programas),
                rol=rol,
                estado='activo',
                is_staff=is_staff,
            )
            user.set_password('Sena1234')
            user.save()
        usuarios_creados.append(user)
    print(f"[OK] {len(usuarios_creados)} Usuarios listos.")

    # ─────────────────────────────────────────────────────────────
    # 2. AUDITORÍA (HISTORIAL DE ACCIONES) Y NOTIFICACIONES
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Historial de Acciones y Notificaciones...")
    modulos = ['Usuarios', 'Inventario', 'Torneos', 'Gimnasio', 'Salud']
    acciones = ['CREAR', 'ACTUALIZAR', 'CONSULTAR', 'APROBAR']
    for u in usuarios_creados[:6]:
        HistorialAccion.objects.get_or_create(
            usuario=u,
            modulo=random.choice(modulos),
            accion=random.choice(acciones),
            defaults={
                'descripcion': f'Operacion de registro o modificacion realizada por {u.get_full_name()}.',
                'ip_origen': '127.0.0.1'
            }
        )

        Notificacion.objects.get_or_create(
            usuario=u,
            titulo=f"Bienvenido a SportMax, {u.first_name}",
            defaults={
                'mensaje': 'Tu cuenta se encuentra activa en el sistema de gestion deportiva institucional.',
                'tipo': 'info',
                'icono': 'fa-bell',
                'leida': random.choice([True, False]),
                'enlace': '/perfil/'
            }
        )
    print("[OK] Historial y Notificaciones configurados.")

    # ─────────────────────────────────────────────────────────────
    # 3. DISCIPLINAS
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Disciplinas...")
    disciplinas_data = [
        ("Fútbol", "fa-futbol", "Reglamento oficial FIFA de fútbol campo.", "goles"),
        ("Fútbol Sala", "fa-futbol", "Reglamento oficial AMF de microfútbol/fútsal.", "goles"),
        ("Baloncesto", "fa-basketball-ball", "Reglamento oficial FIBA de baloncesto.", "puntos"),
        ("Voleibol", "fa-volleyball-ball", "Reglamento FIVB con formato por sets.", "sets"),
        ("Tenis de Mesa", "fa-table-tennis", "Reglamento ITTF con parciales por sets.", "sets"),
        ("Ajedrez", "fa-chess", "Reglamento FIDE de ajedrez rápido.", "no_aplica"),
        ("Atletismo", "fa-running", "Pruebas de pista y velocidad.", "no_aplica"),
        ("Taekwondo", "fa-hand-rock", "Combates reglamentarios WT.", "puntos"),
        ("Billar", "fa-dot-circle", "Modalidad pool bola 8 y libre.", "puntos"),
    ]
    disciplinas_objs = []
    for nom, ico, reg, marc in disciplinas_data:
        d, _ = Disciplina.objects.get_or_create(
            nombre_disciplina=nom,
            defaults={'icono': ico, 'reglas': reg, 'tipo_marcador': marc}
        )
        disciplinas_objs.append(d)
    print("[OK] Disciplinas registradas.")

    # ─────────────────────────────────────────────────────────────
    # 4. ELEMENTOS DEPORTIVOS (INVENTARIO)
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Inventario de Elementos Deportivos...")
    elementos_info = [
        ("Balón de Fútbol Golty N° 5", "balones", "Estante A1", 15),
        ("Balón de Baloncesto Molten", "balones", "Estante A2", 10),
        ("Balón de Voleibol Mikasa", "balones", "Estante A3", 12),
        ("Set de Raquetas y Pelotas Ping Pong", "raquetas", "Gaveta B1", 8),
        ("Colchoneta Gimnasia Alta Densidad", "colchonetas", "Zona Colchonetas", 20),
        ("Set de Pesas Mancuernas 10kg", "pesas", "Rack de Fuerza", 6),
        ("Cinta Métrica Profesional 50m", "medicion", "Gaveta C1", 4),
        ("Cronómetro Digital Deportivo", "medicion", "Gaveta C2", 8),
        ("Juego de Ajedrez Profesional con Tablero", "juegos_mesa", "Armario D1", 10),
        ("Red de Voleibol Reglamentaria", "redes", "Estante E1", 3),
    ]
    elementos_objs = []
    usuarios_staff = [u for u in usuarios_creados if u.is_staff]
    hoy = timezone.localdate()

    for nom, cat, ubi, cant in elementos_info:
        # Fecha de adquisición: válida, menor o igual a hoy y como máximo 1 año atrás
        dias_adq = random.randint(10, 300)
        fecha_adq = hoy - timedelta(days=dias_adq)
        e, _ = ElementoDeportivo.objects.get_or_create(
            tipo_maquina=nom,
            defaults={
                'cantidad_total': cant,
                'estado_general': 'Buen estado',
                'categoria': cat,
                'ubicacion': ubi,
                'habilitado': True,
                'fecha_adquisicion': fecha_adq,
                'descripcion': f'Implemento deportivo oficial: {nom}. Apto para entrenamientos y torneos interfichas.',
                'usuario_responsable': random.choice(usuarios_staff) if usuarios_staff else admin_user
            }
        )
        elementos_objs.append(e)
    print(f"[OK] {len(elementos_objs)} Elementos deportivos en inventario listos.")

    # ─────────────────────────────────────────────────────────────
    # 5. PRÉSTAMOS, DETALLES, DEVOLUCIONES, REVISIONES Y SANCIONES
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Prestamos, Devoluciones y Sanciones...")
    aprendices = [u for u in usuarios_creados if not u.is_staff]

    for idx, elem in enumerate(elementos_objs[:6], 1):
        solicitante = aprendices[idx % len(aprendices)]
        fecha_p = hoy - timedelta(days=idx * 2)

        p = Prestamo.objects.create(
            usuario=solicitante,
            elemento=elem,
            cantidad_prestada=1,
            dias_prestamo=2,
            estado_prestamo='Devuelto' if idx <= 4 else 'Activo',
            observacion_prestamo=f'Prestamo de prueba #{idx} para practica deportiva.'
        )
        p.fecha_prestamo = fecha_p
        p.fecha_devolucion = fecha_p + timedelta(days=2)
        p.save(update_fields=['fecha_prestamo', 'fecha_devolucion'])

        DetallePrestamo.objects.create(
            prestamo=p,
            elemento=elem,
            fecha_devolucion_prevista=fecha_p + timedelta(days=2),
            estado='Devuelto' if idx <= 4 else 'Pendiente'
        )

        if idx <= 4:
            con_novedad = (idx == 3)
            dev = Devolucion.objects.create(
                prestamo=p,
                cantidad_devuelta=1,
                tiene_novedad=con_novedad,
                estado_elemento_devolucion='Regular' if con_novedad else 'Bueno',
                tipo_novedad_devolucion='Daño' if con_novedad else None,
                observaciones_devolucion='Se entrego con rasgadura superficial en la costura.' if con_novedad else 'Entrega sin novedades.'
            )

            if con_novedad:
                Revision.objects.create(
                    devolucion=dev,
                    tipo_novedad='Daño',
                    descripcion_detallada='Revision tecnica del implemento para reparacion.',
                    estado_resolucion='En Proceso'
                )
                Sancion.objects.create(
                    usuario=solicitante,
                    devolucion=dev,
                    tipo_sancion='Daño de material deportivo',
                    fecha_inicio_sancion=hoy,
                    fecha_fin_sancion=hoy + timedelta(days=15),
                    estado_sancion='Activa',
                    descripcion_sancion='Sancion temporal por entrega de elemento con daño.'
                )

    # Sancion cerrada para historial
    if len(aprendices) > 1:
        Sancion.objects.create(
            usuario=aprendices[1],
            tipo_sancion='Mora de entrega resuelta',
            fecha_inicio_sancion=hoy - timedelta(days=30),
            fecha_fin_sancion=hoy - timedelta(days=15),
            estado_sancion='Cerrada',
            descripcion_sancion='Sancion previa ya cumplida satisfactoriamente.'
        )
    print("[OK] Prestamos, Devoluciones y Sanciones listos.")

    # ─────────────────────────────────────────────────────────────
    # 6. TORNEOS INTERFICHAS, EQUIPOS, JUGADORES, GRUPOS Y PARTIDOS
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Torneos Interfichas y Equipos...")
    disc_fut = Disciplina.objects.filter(nombre_disciplina__icontains="Fútbol Sala").first() or disciplinas_objs[0]

    # Torneo 1: Activo / En inscripción (futuro)
    torneo_activo, _ = TorneoInterfichas.objects.get_or_create(
        nombre_torneo="Torneo Interfichas SENA 2026 - Apertura",
        defaults={
            'fecha_torneo_fichas': hoy + timedelta(days=14),
            'horario_torneo_fichas': time(8, 30),
            'lugar': "Cancha Polideportiva Centro Minero",
            'disciplina': disc_fut,
            'estado': 'activo'
        }
    )

    # Torneo 2: En curso (iniciado hoy temprano)
    torneo_en_curso, _ = TorneoInterfichas.objects.get_or_create(
        nombre_torneo="Copa Relámpago Microfútbol Interfichas",
        defaults={
            'fecha_torneo_fichas': hoy,
            'horario_torneo_fichas': time(7, 0),
            'lugar': "Coliseo Principal",
            'disciplina': disc_fut,
            'estado': 'En Curso'
        }
    )

    # Torneo 3: Cerrado (pasado)
    torneo_cerrado, _ = TorneoInterfichas.objects.get_or_create(
        nombre_torneo="Campeonato Interfichas 2025 - Clausura",
        defaults={
            'fecha_torneo_fichas': hoy - timedelta(days=60),
            'horario_torneo_fichas': time(8, 0),
            'lugar': "Cancha Sintética",
            'disciplina': disc_fut,
            'estado': 'cerrado'
        }
    )

    equipos_por_torneo = {}
    for t_idx, t in enumerate([torneo_activo, torneo_en_curso, torneo_cerrado], 1):
        equipos_t = []
        for j in range(1, 5):
            eq, _ = EquipoInterfichas.objects.get_or_create(
                torneo=t,
                nombre_equipo=f"Equipo Ficha 27{t_idx}{j:02d} ({t.nombre_torneo[:12]})",
                defaults={
                    'capitan': f"Capitan Ficha {j}",
                    'ficha': int(f"2700{t_idx}{j}"),
                    'programa': programas[j % len(programas)],
                    'disciplina': t.disciplina,
                    'usuario_registra': aprendices[j % len(aprendices)]
                }
            )
            equipos_t.append(eq)

            # Jugadores del equipo
            for k in range(1, 4):
                JugadorEquipo.objects.get_or_create(
                    equipo=eq,
                    nombre_completo=f"Jugador {k} de {eq.nombre_equipo}",
                    defaults={
                        'numero_documento': f"1098{t_idx}{j}{k}"
                    }
                )
        equipos_por_torneo[t.pk] = equipos_t

        # Grupo y partidos para torneos en curso o cerrados
        if t in [torneo_en_curso, torneo_cerrado]:
            grupo, _ = GrupoInterfichas.objects.get_or_create(
                torneo=t,
                nombre_grupo="A"
            )
            grupo.equipos.set(equipos_t)

            # Partidos
            if len(equipos_t) >= 2:
                p1, _ = PartidoInterfichas.objects.get_or_create(
                    torneo=t,
                    grupo=grupo,
                    fase='grupo',
                    equipo_local=equipos_t[0],
                    equipo_visitante=equipos_t[1],
                    defaults={
                        'fecha_partido': t.fecha_torneo_fichas,
                        'hora_partido': time(9, 0),
                        'goles_local': 3,
                        'goles_visitante': 1,
                        'jugado': True
                    }
                )

            if t == torneo_cerrado and len(equipos_t) >= 2:
                ResultadoTorneo.objects.get_or_create(
                    torneo=t,
                    defaults={
                        'ganador': equipos_t[0],
                        'subcampeon': equipos_t[1],
                        'balance_juego_limpio': equipos_t[0]
                    }
                )
    print("[OK] Torneos, Equipos, Jugadores y Partidos creados.")

    # ─────────────────────────────────────────────────────────────
    # 7. GIMNASIO (CONFIGURACIÓN, FRANJAS, MÁQUINAS Y RESERVAS)
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Gimnasio (Franjas, Maquinas y Config)...")
    config_gym = GimnasioConfig.get_config()
    config_gym.estado = 'abierta'
    config_gym.capacidad_maxima = 35
    config_gym.dias_habilitados = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
    config_gym.actualizado_por = admin_user
    config_gym.save()

    franjas_horas = [
        (time(7, 0), time(8, 0)),
        (time(8, 0), time(9, 0)),
        (time(9, 0), time(10, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    franjas_objs = []
    for d in dias[:3]:
        for h_ini, h_fin in franjas_horas[:2]:
            f, _ = FranjaHoraria.objects.get_or_create(
                dia_semana=d,
                hora_inicio=h_ini,
                hora_fin=h_fin,
                defaults={'aforo_maximo': 25, 'habilitada': True}
            )
            franjas_objs.append(f)

    # Máquinas
    maquinas_lista = [
        ("Caminadora Eléctrica Pro", "cardio", "Cardio", "Disponible"),
        ("Bicicleta Estática Profesional", "cardio", "Cardio", "Disponible"),
        ("Prensa de Piernas 45 Grados", "fuerza", "Fuerza", "Disponible"),
        ("Press de Pecho Plano", "fuerza", "Fuerza", "Disponible"),
        ("Multiestación Multifuerza 8 Puestos", "funcional", "Funcional", "Disponible"),
        ("Elíptica Magnética", "cardio", "Cardio", "En Mantenimiento"),
    ]
    for nom_m, cat_m, tip_m, est_m in maquinas_lista:
        Maquina.objects.get_or_create(
            nombre=nom_m,
            defaults={
                'categoria': cat_m,
                'estado': 'disponible' if est_m == 'Disponible' else 'mantenimiento',
                'descripcion': f'Equipo biomecánico para entrenamiento de {cat_m}.'
            }
        )
        Machine.objects.get_or_create(
            nombre=nom_m,
            defaults={
                'tipo': tip_m,
                'estado': est_m,
                'descripcion': f'Máquina para acondicionamiento físico categoría {tip_m}.',
                'fecha_adquisicion': hoy - timedelta(days=random.randint(20, 280))
            }
        )

    # Reservas de gimnasio
    for idx, u in enumerate(aprendices[:6], 1):
        f_res = hoy + timedelta(days=idx)
        franja = franjas_objs[idx % len(franjas_objs)] if franjas_objs else None
        ReservaGimnasio.objects.get_or_create(
            usuario_solicitante=u,
            fecha_entrada=f_res,
            hora_entrada=time(8, 0),
            defaults={
                'fecha_salida': f_res,
                'hora_salida': time(9, 0),
                'tiempo_permanencia': 60,
                'franja_horaria': franja,
                'estado': 'Activa' if idx <= 2 else 'Pendiente'
            }
        )
    print("[OK] Gimnasio poblado.")

    # ─────────────────────────────────────────────────────────────
    # 8. HÁBITOS SALUDABLES, RECETAS, SEGUIMIENTOS Y RUTINAS
    # ─────────────────────────────────────────────────────────────
    print("[-] Poblando Habitos Saludables, Nutricion y Seguimiento...")
    # Habeas Data
    for u in usuarios_creados[:8]:
        HabeasDataConsent.objects.get_or_create(
            usuario=u,
            defaults={
                'acepta': True,
                'direccion_ip': '127.0.0.1',
                'version_politica': '1.0'
            }
        )

    # Hábitos
    habitos = [
        ("Hidratación Óptima", "hidratacion", "Beber agua a lo largo del día mantiene el rendimiento físico y mental.", "2 a 3 litros al día\nLlevar termo propio"),
        ("Higiene del Sueño", "sueno", "Dormir de 7 a 8 horas diarias para reparar fibras musculares.", "Horario fijo\nSin pantallas 1h antes"),
        ("Pausas Activas", "ejercicio", "Estiramientos breves durante las jornadas académicas.", "Cada 2 horas\nEstirar cuello y espalda"),
        ("Alimentación Consciente", "alimentacion", "Incluir porciones adecuadas de vegetales, proteínas y carbohidratos.", "5 porciones de frutas/verduras\nReducir azúcares"),
        ("Salud y Gestión Emocional", "mental", "Prácticas de respiración y descanso activo frente al estrés.", "Técnicas de respiración diafragmática\nEsparcimiento"),
    ]
    habitos_objs = []
    for tit, cat, desc, cons in habitos:
        h, _ = HabitoSaludable.objects.get_or_create(
            titulo=tit,
            defaults={
                'categoria': cat,
                'descripcion': desc,
                'consejos': cons,
                'icono_css': 'bi-heart-pulse'
            }
        )
        habitos_objs.append(h)

    # Pirámide Nutricional
    piramide_items = [
        ("Agua Natural", "agua", 1, "Base fundamental de hidratación celular.", "2 a 3 litros al día", "Agua pura, infusiones sin azúcar"),
        ("Cereales Integrales", "cereales", 1, "Energía de liberación prolongada.", "4 a 6 porciones diarias", "Avena en hojuelas, arroz integral, quinua"),
        ("Frutas y Vegetales", "frutas", 2, "Aporte de micronutrientes, fibra y antioxidantes.", "5 porciones al día", "Manzanas, naranjas, espinacas, zanahorias"),
        ("Proteínas Magras", "proteinas", 3, "Construcción y recuperación de tejido muscular.", "2 a 3 porciones al día", "Pechuga de pollo, huevos, pescado, legumbres"),
        ("Grasas Saludables", "grasas", 4, "Salud cardiovascular y hormonal.", "1 a 2 porciones al día", "Aguacate, frutos secos, aceite de oliva"),
    ]
    for nom, cat, niv, ben, cant, ej in piramide_items:
        PiramideNutricional.objects.get_or_create(
            nombre=nom,
            defaults={
                'categoria': cat,
                'nivel_piramide': niv,
                'beneficios': ben,
                'cantidad_recomendada': cant,
                'ejemplos': ej,
                'color_tarjeta': '#0284c7'
            }
        )

    # Rutinas Físicas
    rutinas = [
        ("Acondicionamiento General", "principiante", "bienestar", "Rutina ideal para aprendices que inician actividad física.", 35, "10 Sentadillas\n10 Flexiones inclinadas\n30s Plancha"),
        ("Fuerza Tren Superior", "intermedio", "fuerza", "Desarrollo de fuerza en pectorales, hombros y brazos.", 45, "15 Flexiones de pecho\n12 Fondos en banca\n12 Dominadas asistidas"),
        ("Cardio HIIT Minero", "avanzado", "cardio", "Entrenamiento de intervalos de alta intensidad para resistencia.", 30, "40s Burpees\n20s Descanso\n40s Jumping Jacks\n20s Descanso"),
    ]
    rutinas_objs = []
    for nom, niv, obj, desc, dur, ejerc in rutinas:
        r, _ = RutinaFisica.objects.get_or_create(
            nombre=nom,
            defaults={
                'nivel': niv,
                'objetivo': obj,
                'descripcion': desc,
                'duracion_minutos': dur,
                'ejercicios': ejerc
            }
        )
        rutinas_objs.append(r)

    # Recetas Saludables
    recetas_data = [
        ("Bowl Energético de Avena y Frutas", "desayuno", "mantenimiento", "Avena en hojuelas cocida con leche descremada, rodajas de banano y frutos secos.", "Avena 50g\nLeche 200ml\n1 Banano\nNueces 15g", "1. Cocinar la avena.\n2. Servir y decorar con fruta.", 10, 1, 380),
        ("Pechuga a la Plancha con Ensalada Tricolor", "almuerzo", "ganancia_muscular", "Pechuga de pollo sazonada con finas hierbas acompañada de vegetales frescos.", "Pechuga de pollo 180g\nLechuga\nTomate\nZanahoria rayada", "1. Asar la pechuga a fuego medio.\n2. Mezclar vegetales y aderezar con limón.", 25, 1, 420),
        ("Batido Verde Revitalizante", "bebida", "bienestar", "Batido natural rico en minerales y antioxidantes para media tarde.", "Espinaca 1 taza\nManzana verde 1 unidad\nAgua 250ml", "1. Licuar todos los ingredientes por 2 minutos.\n2. Servir frío.", 5, 1, 120),
    ]
    for tit, cat, obj, desc, ingr, prep, t_prep, porc, cal in recetas_data:
        RecetaSaludable.objects.get_or_create(
            titulo=tit,
            defaults={
                'categoria': cat,
                'objetivo': obj,
                'descripcion': desc,
                'ingredientes': ingr,
                'preparacion': prep,
                'tiempo_preparacion_min': t_prep,
                'porciones': porc,
                'calorias_por_porcion': cal,
                'autor': admin_user
            }
        )

    # Seguimiento de Salud de Aprendices
    for idx, u in enumerate(aprendices[:5], 1):
        SeguimientoSalud.objects.get_or_create(
            usuario=u,
            fecha_evaluacion=hoy - timedelta(days=idx * 5),
            defaults={
                'peso_kg': 68.0 + idx * 2.5,
                'estatura_cm': 172.0,
                'presion_sistolica': 118,
                'presion_diastolica': 76,
                'frecuencia_cardiaca': 68 + idx,
                'nivel_actividad': 'moderado',
                'horas_sueno': 7.5,
                'vasos_agua': 8,
                'observaciones': 'Evaluación preventiva regular en el área de bienestar.'
            }
        )

        # Registro diario de hábitos y sueño
        if habitos_objs:
            RegistroHabitoUsuario.objects.get_or_create(
                usuario=u,
                habito=habitos_objs[0],
                fecha=hoy,
                defaults={'completado': True, 'nota': 'Meta de 2.5 litros completada.'}
            )

        RegistroSueno.objects.get_or_create(
            usuario=u,
            fecha=hoy,
            defaults={'horas': 7.5, 'calidad': 4, 'nota': 'Descanso reparador.'}
        )

        if rutinas_objs:
            RegistroSesionRutina.objects.get_or_create(
                usuario=u,
                rutina=rutinas_objs[0],
                fecha=hoy,
                defaults={'duracion_real_min': 35, 'completado': True, 'nivel_esfuerzo': 3}
            )

    # Material de Apoyo
    MaterialApoyo.objects.get_or_create(
        titulo="Guía Institucional de Nutrición y Actividad Física SENA",
        defaults={
            'tipo_contenido': 'documento',
            'descripcion': 'Manual completo de buenas prácticas nutricionales para aprendices.',
            'autor': 'Bienestar al Aprendiz SENA',
            'activo': True
        }
    )

    # Sugerencias / Buzón
    tipos_sug = ['Mejora', 'Queja', 'Felicitación']
    for i in range(1, 6):
        anon = (i % 2 == 0)
        Sugerencia.objects.get_or_create(
            comentario=f"Sugerencia de prueba número {i} sobre las instalaciones deportivas y su mantenimiento.",
            defaults={
                'usuario': None if anon else aprendices[i % len(aprendices)],
                'tipo': tipos_sug[i % len(tipos_sug)],
                'anonimo': anon,
                'respuesta': 'Gracias por tu aporte. Se ha remitido al comité de bienestar.' if i <= 2 else None
            }
        )

    print("\n[OK] Base de datos poblada exitosamente con todas las entidades y relaciones!")


if __name__ == '__main__':
    poblar_datos()