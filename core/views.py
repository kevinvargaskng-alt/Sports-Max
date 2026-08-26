from inventario.models import ElementoDeportivo, Prestamo, Sancion
from interfichas.models import TorneoInterfichas, EquipoInterfichas, JugadorEquipo, PartidoInterfichas
from gimnasio.models import Reserva
import json
import logging
import urllib.request
import urllib.error
import os
import base64
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

security_logger = logging.getLogger('security')


# ============================================================
#  RECOPILACIÓN DE CONTEXTO REAL DE LA BD
# ============================================================

def _obtener_contexto_bd() -> str:
    """
    Consulta todos los módulos de la BD y genera un bloque de texto
    con datos reales para inyectarlo al system prompt de Gemini.
    """
    lineas = []

    # ── GIMNASIO ────────────────────────────────────────────
    try:
        from gimnasio.models import GimnasioConfig
        config = GimnasioConfig.get_config()
        reservas_pend = Reserva.objects.filter(estado__iexact="Pendiente").count()
        reservas_aprobadas = Reserva.objects.filter(estado__iexact="Aprobada").count()
        lineas.append(
            f"=== GIMNASIO ===\n"
            f"Estado actual: {config.estado}\n"
            f"Horario apertura: {config.horario_apertura}\n"
            f"Horario cierre: {config.horario_cierre}\n"
            f"Capacidad máxima: {config.capacidad_maxima} personas\n"
            f"Reservas pendientes de aprobación: {reservas_pend}\n"
            f"Reservas aprobadas activas: {reservas_aprobadas}\n"
        )
    except Exception as e:
        lineas.append(f"=== GIMNASIO ===\nNo disponible: {e}\n")

    # ── INVENTARIO ──────────────────────────────────────────
    try:
        elementos = ElementoDeportivo.objects.all()[:80]
        prestamos_activos = Prestamo.objects.filter(estado_prestamo__iexact="Activo").count()
        try:
            sanciones_activas = Sancion.objects.filter(activa=True).count()
        except Exception:
            sanciones_activas = Sancion.objects.count()
        lineas.append("=== INVENTARIO DEPORTIVO ===")
        for e in elementos:
            resp = e.usuario_responsable.get_full_name() if e.usuario_responsable else "No asignado"
            lineas.append(
                f"- {e.tipo_maquina}: {e.cantidad_total} uds, estado: {e.estado_general}, responsable: {resp}"
            )
        lineas.append(f"Préstamos activos en este momento: {prestamos_activos}")
        lineas.append(f"Sanciones activas: {sanciones_activas}\n")
    except Exception as e:
        lineas.append(f"=== INVENTARIO ===\nNo disponible: {e}\n")

    # ── INTERFICHAS ─────────────────────────────────────────
    try:
        torneos = TorneoInterfichas.objects.select_related("disciplina").all()[:20]
        equipos_total = EquipoInterfichas.objects.count()
        partidos_jugados = PartidoInterfichas.objects.filter(jugado=True).count()
        lineas.append("=== TORNEOS INTERFICHAS ===")
        for t in torneos:
            n_equipos = t.equipos.count()
            lineas.append(
                f"- Torneo: {t.nombre_torneo} | Disciplina: {t.disciplina} | "
                f"Estado: {t.estado} | Fecha: {t.fecha_torneo_fichas} | "
                f"Lugar: {t.lugar} | Equipos inscritos: {n_equipos}"
            )
        lineas.append(f"Total equipos inscritos (todos los torneos): {equipos_total}")
        lineas.append(f"Partidos jugados: {partidos_jugados}\n")
    except Exception as e:
        lineas.append(f"=== INTERFICHAS ===\nNo disponible: {e}\n")

    # ── INTERCENTROS ────────────────────────────────────────
    try:
        from interfichas.models import TorneoIntercentros, PostulacionIntercentros
        torneos_ic = TorneoIntercentros.objects.all()[:20]
        postulaciones = PostulacionIntercentros.objects.count()
        lineas.append("=== TORNEOS INTERCENTROS ===")
        for t in torneos_ic:
            lineas.append(
                f"- Torneo: {t.nombre_torneo} | Disciplina: {getattr(t, 'disciplina', '?')} | "
                f"Estado: {getattr(t, 'estado', '?')} | Lugar: {getattr(t, 'lugar', '?')}"
            )
        lineas.append(f"Total postulaciones registradas: {postulaciones}\n")
    except Exception as e:
        lineas.append(f"=== INTERCENTROS ===\nSin datos o no disponible.\n")

    # ── HÁBITOS SALUDABLES ──────────────────────────────────
    try:
        from habitos_saludables.models import HabitoSaludable, RutinaFisica, MaterialApoyo
        habitos = HabitoSaludable.objects.filter(activo=True)[:30]
        rutinas = RutinaFisica.objects.filter(activo=True)[:20]
        materiales = MaterialApoyo.objects.filter(activo=True)[:20]
        lineas.append("=== HÁBITOS SALUDABLES ===")
        for h in habitos:
            lineas.append(f"- {h.titulo} ({h.categoria}): {str(h.descripcion)[:120]}")
        lineas.append("=== RUTINAS FÍSICAS ===")
        for r in rutinas:
            ejercicios = r.get_ejercicios_lista() if hasattr(r, 'get_ejercicios_lista') else []
            lineas.append(
                f"- {r.nombre} | Nivel: {r.nivel} | Objetivo: {r.objetivo} | "
                f"Duración: {r.duracion_minutos} min | Ejercicios: {', '.join(ejercicios[:5])}"
            )
        lineas.append("=== MATERIALES DE APOYO ===")
        for m in materiales:
            lineas.append(f"- {m.titulo} ({m.tipo_contenido}): {str(m.descripcion)[:80]}")
        lineas.append("")
    except Exception as e:
        lineas.append(f"=== HÁBITOS ===\nNo disponible: {e}\n")

    # ── USUARIOS ────────────────────────────────────────────
    try:
        from usuarios.models import Usuario
        total_usuarios = Usuario.objects.count()
        admins = Usuario.objects.filter(is_staff=True).count()
        lineas.append(
            f"=== USUARIOS DEL SISTEMA ===\n"
            f"Total usuarios registrados: {total_usuarios}\n"
            f"Administradores: {admins}\n"
        )
    except Exception as e:
        lineas.append(f"=== USUARIOS ===\nNo disponible: {e}\n")

    return "\n".join(lineas)


# ============================================================
#  SYSTEM PROMPT PRINCIPAL DE TUX
# ============================================================

SYSTEM_PROMPT_BASE = """Eres **Tux** 🐱, el asistente de inteligencia artificial del Sistema de Gestión Deportiva del SENA Centro Minero (Colombia).

## Tu personalidad
- Eres amable, servicial, entusiasta y profesional.
- Usas emojis con moderación para hacer las respuestas más amigables.
- Respondes siempre en español colombiano.

## Módulos del sistema que conoces perfectamente
1. **🏋️ Gimnasio**: Reservas, horarios, estado (abierto/cerrado/mantenimiento), capacidad, aprobación de reservas.
   - Para reservar: ir al módulo Gimnasio, llenar el formulario (nombre, fecha, hora entrada/salida). La reserva queda Pendiente y un admin la aprueba.
   - Solo admins pueden aprobar/rechazar reservas y cambiar el estado del gimnasio.
2. **📦 Inventario Deportivo**: Elementos deportivos, préstamos, devoluciones, sanciones.
   - Para pedir préstamo: ir a Inventario, seleccionar elemento, indicar cantidad y fecha devolución.
   - Si no devuelves a tiempo o devuelves dañado → sanción activa que bloquea nuevos préstamos.
3. **📋 Interfichas**: Torneos deportivos entre fichas de aprendices del SENA.
   - Para inscribir equipo: Interfichas → torneo activo → formulario con número de ficha, programa, nombre equipo, capitán y jugadores.
   - La tabla de posiciones se actualiza automáticamente con cada resultado.
4. **🏆 Intercentros**: Competencias entre centros del SENA a nivel regional/nacional.
   - Para postularse: Intercentros → torneo activo → formulario con documento, nombres, ficha y programa.
5. **🍏 Hábitos Saludables**: Consejos de salud, nutrición, hábitos, rutinas físicas, biblioteca de materiales.
6. **👤 Usuarios y Perfil**: Gestión de cuenta, cambio de contraseña, foto de perfil, roles.

## REGLA MÁS IMPORTANTE — Límite de temas
**SOLO puedes responder preguntas relacionadas con:**
- El Sistema de Gestión Deportiva del SENA Centro Minero y sus módulos
- Deportes en general (fútbol, baloncesto, voleibol, atletismo, etc.)
- Fitness, entrenamiento físico, rutinas de ejercicio
- Nutrición, hábitos saludables y bienestar físico
- Cómo usar cualquier funcionalidad del sistema

**Si el usuario pregunta sobre cualquier otro tema** (política, historia, geografía, matemáticas, noticias, entretenimiento, programación, tecnología general, u otro tema que NO sea el sistema o deportes/salud), debes responder EXACTAMENTE así (adapta solo los emojis o el tono según el contexto):

"¡Hola! 🐱 Esa pregunta está fuera de mi área. Soy **Tux**, el asistente del Sistema Deportivo del SENA Centro Minero, y solo puedo ayudarte con temas relacionados con:

• 🏋️ **Gimnasio** — reservas, horarios y estado
• 📦 **Inventario** — implementos deportivos y préstamos  
• 📋 **Interfichas** — torneos entre fichas de aprendices
• 🏆 **Intercentros** — competencias regionales/nacionales
• 🍏 **Hábitos saludables** — nutrición y rutinas físicas
• 👤 **Perfil** — gestión de tu cuenta

¿En qué te puedo ayudar dentro del sistema? 😊"

## Instrucciones de formato
- Usa **negrillas** para términos clave, listas y emojis para mayor claridad.
- Cuando el usuario pregunte sobre datos actuales (horarios, inventario, torneos, etc.), usa los datos de la sección "DATOS ACTUALES DEL SISTEMA" para responder con información precisa.
- Sé conciso: máximo 4-5 párrafos salvo que se pida detalle.

## DATOS ACTUALES DEL SISTEMA (base de datos en tiempo real)
{contexto_bd}
"""


# ============================================================
#  CONSULTA A GEMINI API — Motor principal
# ============================================================

def _consultar_gemini_api(mensaje: str, historial: list, contexto_bd: str):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent?key=" + api_key
        )

        system_instruction = SYSTEM_PROMPT_BASE.format(contexto_bd=contexto_bd)

        contents = []
        for h in historial[-10:]:
            role = "user" if h.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": mensaje}]})

        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.45,
                "maxOutputTokens": 900,
                "topP": 0.92,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=18) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            reply = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return reply

    except Exception as e:
        print(f"[Tux] Error al consultar Gemini API: {e}")
        return None


# ============================================================
#  MOTOR IA LOCAL — Fallback cuando Gemini no responde
# ============================================================

_motor_ia_local = None


def _get_motor_ia_local():
    global _motor_ia_local
    if _motor_ia_local is None:
        try:
            from scripts.ia_engine import MotorIA
            _motor_ia_local = MotorIA.cargar()
        except Exception as e:
            print(f"[Tux] Error al cargar MotorIA local: {e}")
    return _motor_ia_local


# ============================================================
#  ENDPOINT PRINCIPAL: /api/chat-tux/
# ============================================================

@login_required
@require_POST
def chat_tux_api(request):
    # Método ya restringido por @require_POST

    try:
        data = json.loads(request.body)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])

        if not mensaje:
            return JsonResponse({"error": "El mensaje está vacío."}, status=400)

        # 1. Obtener contexto real de BD (datos en tiempo real)
        try:
            contexto_bd = _obtener_contexto_bd()
        except Exception as e:
            contexto_bd = f"(No se pudo obtener contexto de BD: {e})"

        # 2. Gemini como motor PRINCIPAL con contexto completo del proyecto
        gemini_reply = _consultar_gemini_api(mensaje, historial, contexto_bd)
        if gemini_reply:
            return JsonResponse({
                "reply": gemini_reply,
                "modulo": "gemini"
            })

        # 3. Fallback: motor TF-IDF local si Gemini falla
        motor = _get_motor_ia_local()
        if motor and motor._entrenado:
            res = motor.responder(mensaje, historial)
            return JsonResponse({
                "reply": res.get("respuesta"),
                "modulo": res.get("modulo", "local")
            })

        # 4. Respuesta de emergencia
        return JsonResponse({
            "reply": (
                "⚠️ Estoy teniendo problemas para conectarme al servidor. "
                "Por favor intenta de nuevo en unos segundos. "
                "Puedo ayudarte con el gimnasio, inventario, torneos interfichas, "
                "intercentros y hábitos saludables."
            ),
            "modulo": "error"
        })

    except Exception as e:
        security_logger.exception("Error en chat_tux_api: %s", e)
        return JsonResponse({"error": "Error interno del asistente. Intenta de nuevo."}, status=500)


# ============================================================
#  ENDPOINT: /api/transcribe-voice/
# ============================================================

@login_required
@require_POST
def transcribe_voice_api(request):
    """Recibe audio grabado por el usuario y lo transcribe usando Gemini API"""
    # Método ya restringido por @require_POST

    if not request.FILES or 'audio' not in request.FILES:
        return JsonResponse({"error": "No se recibió archivo de audio."}, status=400)

    try:
        audio_file = request.FILES['audio']
        # Limitar tamaño de audio a 10 MB para prevenir agotamiento de memoria
        if audio_file.size > 10 * 1024 * 1024:
            return JsonResponse({"error": "El archivo de audio no puede superar los 10 MB."}, status=400)

        audio_bytes = audio_file.read()

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            security_logger.error("GEMINI_API_KEY no configurada para transcripción")
            return JsonResponse({"error": "Servicio de transcripción temporalmente no disponible."}, status=503)

        mime_type = audio_file.content_type
        if not mime_type or 'audio' not in mime_type:
            mime_type = "audio/webm"

        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent?key=" + api_key
        )

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": audio_b64
                        }
                    },
                    {
                        "text": (
                            "Transcribe exactamente el audio en español. Si no hay voz o hay silencio total, "
                            "responde con una cadena vacía. No agregues saludos, explicaciones, comentarios, "
                            "puntuación innecesaria ni marcas de tiempo. Solo devuelve la transcripción directa."
                        )
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.0
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))

        try:
            transcripcion = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        except (KeyError, IndexError):
            transcripcion = ""

        return JsonResponse({"text": transcripcion})

    except Exception as e:
        security_logger.exception("Error en transcribe_voice_api: %s", e)
        return JsonResponse({"error": "Error al procesar el audio. Intenta de nuevo."}, status=500)


