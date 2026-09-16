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
from django.views.decorators.csrf import csrf_exempt

security_logger = logging.getLogger('security')


# ============================================================
#  RECOPILACIÓN DE CONTEXTO SEGÚN ROL Y ESTADO
# ============================================================

def _obtener_contexto_bd(user=None) -> str:
    """
    Consulta los módulos de la BD y genera un bloque de texto
    con datos reales contextualizados según el rol del usuario:
    - Anónimo: Resumen informativo general del centro.
    - Aprendiz: Datos personales (sus préstamos, reservas, torneos y normas).
    - Administrador: Métricas operativas, stock crítico, reservas por aprobar y control.
    """
    lineas = []
    from django.utils import timezone
    from datetime import timedelta
    ahora_date = timezone.localdate()

    # ── CASO 1: USUARIO NO AUTENTICADO (VISITANTE) ─────────
    if not user or not getattr(user, 'is_authenticated', False):
        lineas.append("=== MODO VISITANTE (NO AUTENTICADO) ===")
        try:
            from gimnasio.models import GimnasioConfig
            config = GimnasioConfig.get_config()
            lineas.append(
                f"- Gimnasio SENA Centro Minero: Estado actual '{config.estado}'. "
                f"Horario: {config.horario_apertura} a {config.horario_cierre}. Capacidad: {config.capacidad_maxima} personas."
            )
        except Exception:
            pass

        try:
            torneos = TorneoInterfichas.objects.filter(estado='activo')[:10]
            if torneos.exists():
                torneo_nombres = [f"{t.nombre_torneo} ({t.disciplina})" for t in torneos]
                lineas.append(f"- Torneos activos abiertos a la comunidad SENA: {', '.join(torneo_nombres)}")
        except Exception:
            pass

        lineas.append(
            "- Acceso a servicios: Para reservar en el gimnasio, solicitar préstamos de inventario o inscribir equipos, "
            "el aprendiz o instructor debe registrarse con su número de documento/carnet e iniciar sesión."
        )
        return "\n".join(lineas)

    # ── CASO 2: USUARIO ADMINISTRADOR ──────────────────────
    if user.is_staff or getattr(user, 'rol', '') == 'admin':
        lineas.append(f"=== MODO ADMINISTRADOR: PANEL DE CONTROL OPERATIVO ===")
        
        # Gimnasio Admin
        try:
            from gimnasio.models import GimnasioConfig
            config = GimnasioConfig.get_config()
            reservas_pend = Reserva.objects.filter(estado__iexact="Pendiente").count()
            reservas_aprobadas = Reserva.objects.filter(estado__iexact="Aprobada").count()
            lineas.append(
                f"• GIMNASIO: Estado '{config.estado}', Capacidad: {config.capacidad_maxima}. "
                f"Reservas PENDIENTES de aprobación: {reservas_pend} | Aprobadas activas: {reservas_aprobadas}."
            )
        except Exception as e:
            lineas.append(f"• GIMNASIO: {e}")

        # Inventario crítico y préstamos
        try:
            stock_critico = ElementoDeportivo.objects.filter(cantidad_total__lte=3)[:15]
            prestamos_activos = Prestamo.objects.filter(estado_prestamo__iexact="Activo")
            total_activos = prestamos_activos.count()
            
            # Préstamos vencidos
            vencidos = 0
            for p in prestamos_activos:
                if p.fecha_prestamo and (p.fecha_prestamo + timedelta(days=p.dias_prestamo)) < ahora_date:
                    vencidos += 1
            
            sanciones_activas = Sancion.objects.filter(estado_sancion='Activa').count()
            
            criticos_str = ", ".join([f"{e.tipo_maquina} ({e.cantidad_total} uds)" for e in stock_critico]) if stock_critico else "Ninguno con stock bajo"
            lineas.append(
                f"• INVENTARIO CRÍTICO (<= 3 uds): {criticos_str}.\n"
                f"• PRÉSTAMOS ACTIVOS: {total_activos} (de los cuales {vencidos} superaron la fecha límite de devolución).\n"
                f"• SANCIONES ACTIVAS VIGENTES: {sanciones_activas} aprendices sancionados."
            )
        except Exception as e:
            lineas.append(f"• INVENTARIO: {e}")

        # Torneos y equipos
        try:
            torneos_act = TorneoInterfichas.objects.filter(estado='activo').count()
            equipos_tot = EquipoInterfichas.objects.count()
            partidos_pendientes = PartidoInterfichas.objects.filter(jugado=False).count()
            lineas.append(
                f"• TORNEOS INTERFICHAS: {torneos_act} activos, {equipos_tot} equipos inscritos en total, "
                f"{partidos_pendientes} partidos pendientes de jugar."
            )
        except Exception as e:
            lineas.append(f"• TORNEOS: {e}")

        # Usuarios
        try:
            from usuarios.models import Usuario
            tot_usr = Usuario.objects.count()
            bloqueados = Usuario.objects.filter(bloqueado_hasta__isnull=False).count()
            lineas.append(f"• USUARIOS DEL SISTEMA: {tot_usr} registrados (Cuentas temporalmente bloqueadas: {bloqueados}).")
        except Exception:
            pass

        return "\n".join(lineas)

    # ── CASO 3: USUARIO APRENDIZ / COMÚN ───────────────────
    lineas.append(f"=== MODO APRENDIZ PERSONALIZADO: {user.get_full_name()} (Doc: {user.numero_documento}) ===")
    
    # 1. Préstamos personales
    try:
        mis_prestamos = Prestamo.objects.filter(usuario=user, estado_prestamo='Activo').select_related('elemento')
        if mis_prestamos.exists():
            lineas.append("• TUS IMPLEMENTOS EN PRÉSTAMO:")
            for p in mis_prestamos:
                elem_nom = p.elemento.tipo_maquina if p.elemento else "Implemento"
                limite = p.fecha_prestamo + timedelta(days=p.dias_prestamo)
                dias_rest = (limite - ahora_date).days
                if dias_rest < 0:
                    estado_p = f"⚠️ VENCIDO (hace {abs(dias_rest)} días, debiste entregarlo el {limite.strftime('%d/%m/%Y')})"
                elif dias_rest == 0:
                    estado_p = "⏰ VENCE HOY. Debes entregarlo antes del cierre"
                else:
                    estado_p = f"✅ Al día (te quedan {dias_rest} días, límite: {limite.strftime('%d/%m/%Y')})"
                lineas.append(f"  - {p.cantidad_prestada}x {elem_nom}: {estado_p}")
        else:
            lineas.append("• TUS PRÉSTAMOS: No tienes implementos deportivos prestados actualmente. ¡Estás al día!")
    except Exception as e:
        lineas.append(f"• PRÉSTAMOS: Error al consultar ({e})")

    # 2. Reservas de gimnasio del usuario
    try:
        mis_reservas = Reserva.objects.filter(usuario_solicitante=user).order_by('-codigo_reserva')[:3]
        if mis_reservas.exists():
            lineas.append("• TUS ÚLTIMAS RESERVAS EN EL GIMNASIO:")
            for r in mis_reservas:
                lineas.append(f"  - Reserva #{r.codigo_reserva}: Fecha {r.fecha_reserva} a las {r.hora_reserva} | Estado: {r.estado_reserva}")
        else:
            lineas.append("• TUS RESERVAS EN GIMNASIO: No has realizado reservas recientes.")
    except Exception:
        pass

    # 3. Sanciones del usuario
    try:
        mis_sanciones = Sancion.objects.filter(usuario=user, estado_sancion='Activa')
        if mis_sanciones.exists():
            lineas.append("• ⚠️ TIENES SANCIONES ACTIVAS QUE BLOQUEAN NUEVOS PRÉSTAMOS:")
            for s in mis_sanciones:
                lineas.append(f"  - Motivo: {s.tipo_sancion} | Vigente hasta: {s.fecha_fin_sancion}")
        else:
            lineas.append("• SANCIONES: Tu historial disciplinario está limpio (Sin sanciones).")
    except Exception:
        pass

    # 4. Equipos y Torneos
    try:
        mis_equipos = EquipoInterfichas.objects.filter(usuario_registra=user).select_related('torneo')
        if mis_equipos.exists():
            lineas.append("• TUS EQUIPOS INSCRITOS EN TORNEOS:")
            for eq in mis_equipos:
                lineas.append(f"  - Equipo '{eq.nombre_equipo}' en Torneo '{eq.torneo.nombre_torneo}' (Ficha: {eq.ficha})")
        else:
            lineas.append("• TORNEOS INTERFICHAS: No has inscrito equipos actualmente.")
    except Exception:
        pass

    # 5. Reglamentos clave para el aprendiz
    lineas.append(
        "• REGLAMENTO RÁPIDO:\n"
        "  - Los préstamos de implementos se autorizan por un máximo de 15 días.\n"
        "  - La no entrega oportuna o el deterioro/pérdida genera sanción automática que bloquea nuevos préstamos.\n"
        "  - El gimnasio requiere reserva previa y aprobación por parte del administrador."
    )

    return "\n".join(lineas)


# ============================================================
#  CONSTRUCCIÓN DINÁMICA DEL SYSTEM PROMPT SEGÚN ROL
# ============================================================

def _construir_system_prompt(user, contexto_bd: str) -> str:
    """
    Construye el system prompt específico adaptado al rol del usuario:
    - Anónimo: Introductorio, informativo, institucional.
    - Aprendiz: Personalizado, enfocado en sus reservas, préstamos y normas.
    - Administrador: Técnico, analítico, resúmenes de inventario y control.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        rol_instrucciones = """## DIRECTIVA DE ROL: VISITANTE / USUARIO NO AUTENTICADO
- El usuario que te habla NO ha iniciado sesión (es un visitante o aprendiz explorando la plataforma).
- Bríndale respuestas amables, formativas, genéricas y de nivel introductorio sobre los servicios del SENA Centro Minero.
- Oriéntalo sobre cómo usar el sistema, cómo registrarse con su carnet o documento para poder reservar o pedir implementos, y los horarios generales.
- NO expongas métricas internas de control, listas de usuarios ni inventario privado de administración."""
    elif user.is_staff or getattr(user, 'rol', '') == 'admin':
        rol_instrucciones = f"""## DIRECTIVA DE ROL: ADMINISTRADOR DEL SISTEMA ({user.get_full_name()})
- El usuario que te habla es un ADMINISTRADOR del sistema deportivo.
- Bríndale respuestas analíticas, técnicas, ejecutivas y orientadas a la toma de decisiones.
- Proporciónale resúmenes operativos detallados, alertas de stock crítico en inventario, préstamos vencidos que requieren seguimiento, reservas de gimnasio pendientes por aprobar y control de usuarios.
- Puedes sugerir acciones de gestión administrativa y auditoría con tono profesional y resolutivo."""
    else:
        rol_instrucciones = f"""## DIRECTIVA DE ROL: APRENDIZ / USUARIO REGISTRADO ({user.get_full_name()} - Ficha: {getattr(user, 'ficha', 'N/A')})
- El usuario que te habla es un APRENDIZ del SENA autenticado en su cuenta.
- Adapta tus respuestas de manera personalizada enfocándote en sus reservas activas, el estado de sus implementos prestados, sus fechas límites de devolución para evitar sanciones, y el estado de sus equipos en torneos interfichas.
- Motívalo a practicar deporte y a cumplir estrictamente los reglamentos de entrega de material y turnos de entrenamiento."""

    prompt = f"""Eres **Tux** 🐱, el asistente de inteligencia artificial del Sistema de Gestión Deportiva del SENA Centro Minero (Colombia).

## Tu personalidad
- Eres amable, servicial, entusiasta y profesional.
- Usas emojis con moderación para hacer las respuestas más dinámicas y amenas.
- Respondes siempre en español colombiano.

{rol_instrucciones}

## Módulos del sistema que conoces perfectamente
1. **🏋️ Gimnasio**: Reservas de turnos, horarios de apertura/cierre, estado y capacidad.
2. **📦 Inventario Deportivo**: Implementos, balones, elementos de entrenamiento, préstamos y devoluciones.
3. **📋 Interfichas**: Torneos deportivos entre fichas de aprendices, inscripciones, fases de grupos y llaves finales.
4. **🏆 Intercentros**: Competencias regionales y nacionales del SENA.
5. **🍏 Hábitos Saludables**: Rutinas de entrenamiento físico, nutrición deportiva y bienestar integral.
6. **👤 Perfil y Seguridad**: Gestión de cuenta, roles y control de acceso.

## CAPACIDAD MULTIMODAL Y RECONOCIMIENTO DEL SISTEMA
- Puedes VER y ANALIZAR imágenes que te envíe el usuario mediante archivos o pegadas con Ctrl+V.
- **Si el usuario te envía una CAPTURA DE PANTALLA de este sistema web** (cualquier vista, formulario, botón, tabla o modal):
  1. **Identifica la pantalla o sección exacta**: (ej. *Formulario de Login/Registro*, *Catálogo de Inventario Deportivo*, *Módulo de Préstamos y Devoluciones*, *Reservas del Gimnasio*, *Torneos Interfichas / Modal de Nómina con OCR*, *Llaves de Torneos*, *Hábitos Saludables / Rutinas / Nutrición* o *Panel de Administración*).
  2. **Explica para qué sirve**: Describe de forma clara y amigable el propósito de esa pantalla o función dentro del Centro Minero.
  3. **Guía de uso paso a paso**: Indica qué acciones puede realizar ahí (qué campos diligenciar, qué botones cliquear, cómo subir documentos/consentimientos, etc.).
  4. **Condiciones o reglas**: Menciona requisitos clave si aplican (ej. iniciar sesión con carnet/documento, préstamo máximo por 15 días, ausencia de sanciones, cupo y turnos del gimnasio).
- **Si es una foto de una máquina de gimnasio, implemento deportivo o ejercicio**: Identifícalo, explica qué músculo o deporte trabaja, cómo se ejecuta con buena técnica y las normas de uso en el SENA.

## VELOCIDAD Y CONCISIÓN (RESPUESTAS RÁPIDAS)
- Responde de forma ágil, estructurada y directa al grano (usa viñetas y negritas para que sea muy fácil de leer).
- Evita saludos o despedidas redundantes en cada turno.

## LÍMITE DE TEMAS
SOLO puedes responder sobre el Sistema Deportivo del SENA Centro Minero, deportes, fitness, entrenamiento físico y nutrición/bienestar. Si preguntan sobre otros temas ajenos, declina cortésmente recordando tu función como Tux.

## DATOS EN TIEMPO REAL DEL SISTEMA (BASE DE DATOS ACTUALIZADA)
{contexto_bd}
"""
    return prompt


# ============================================================
#  CONSULTA A GEMINI API — Motor principal (Multimodal)
# ============================================================

def _consultar_gemini_api(mensaje: str, historial: list, user, contexto_bd: str, imagen_data: dict = None):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent?key=" + api_key
        )

        system_instruction = _construir_system_prompt(user, contexto_bd)

        contents = []
        # Conservar últimos 6 mensajes del historial para agilizar procesamiento
        for h in historial[-6:]:
            role = "user" if h.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})

        user_parts = []
        # Si se adjuntó o pegó imagen con Ctrl+V, incorporarla en formato inline_data
        if imagen_data and imagen_data.get('data') and imagen_data.get('mime_type'):
            user_parts.append({
                "inline_data": {
                    "mime_type": imagen_data['mime_type'],
                    "data": imagen_data['data']
                }
            })

        texto_usuario = (mensaje or "").strip()
        if not texto_usuario and imagen_data:
            texto_usuario = (
                "Por favor analiza detalladamente esta imagen. Si es una captura del sistema deportivo del SENA, "
                "identifica qué pantalla o módulo es, explícame para qué sirve y qué debo hacer en ella. "
                "Si es un implemento, máquina o ejercicio, dime qué es y cómo usarlo correctamente."
            )

        user_parts.append({"text": texto_usuario})
        contents.append({"role": "user", "parts": user_parts})

        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.35,
                "maxOutputTokens": 650,
                "topP": 0.90,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=22) as response:
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

@csrf_exempt
@require_POST
def chat_tux_api(request):
    # Endpoint de chat público (visitantes y autenticados) con soporte multimodal (texto e imágenes)

    try:
        data = json.loads(request.body)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])
        imagen_raw = data.get("image")

        imagen_data = None
        if imagen_raw and isinstance(imagen_raw, dict):
            b64 = imagen_raw.get("data", "")
            mime = imagen_raw.get("mime_type", "image/jpeg")
            if b64:
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                # Limitar tamaño razonable (~10 MB)
                if len(b64) <= 14 * 1024 * 1024:
                    imagen_data = {
                        "data": b64,
                        "mime_type": mime if mime.startswith("image/") else "image/jpeg"
                    }

        if not mensaje and not imagen_data:
            return JsonResponse({"error": "El mensaje o la imagen están vacíos."}, status=400)

        # 1. Obtener contexto real de BD (datos en tiempo real adaptados al rol)
        try:
            contexto_bd = _obtener_contexto_bd(request.user)
        except Exception as e:
            contexto_bd = f"(No se pudo obtener contexto de BD: {e})"

        # 2. Gemini como motor PRINCIPAL con contexto completo del proyecto y visión multimodal
        gemini_reply = _consultar_gemini_api(mensaje, historial, request.user, contexto_bd, imagen_data=imagen_data)
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

        # 3b. Fallback: servidor Flask ia_server.py (puerto 5001) si está activo
        try:
            from django.conf import settings
            ia_url = getattr(settings, 'IA_SERVER_URL', 'http://127.0.0.1:5001') + '/ia/chat'
            req_ia = urllib.request.Request(
                ia_url,
                data=json.dumps({"message": mensaje, "history": historial}).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req_ia, timeout=3) as resp_ia:
                data_ia = json.loads(resp_ia.read().decode('utf-8'))
                if "reply" in data_ia:
                    return JsonResponse({
                        "reply": data_ia["reply"],
                        "modulo": data_ia.get("modulo", "ia_server")
                    })
        except Exception:
            pass

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

@csrf_exempt
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


