
import os
import re
import json
import pickle
import math
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from rank_bm25 import BM25Okapi
    BM25_DISPONIBLE = True
except ImportError:
    BM25_DISPONIBLE = False


# ============================================================
# SINÓNIMOS Y EXPANSIÓN DE CONSULTAS
# ============================================================
SINONIMOS = {
    # Módulos
    "gimansio": "gimnasio", "gym": "gimnasio", "ejercicio": "gimnasio",
    "pesas": "gimnasio", "maquinas": "gimnasio inventario",
    "inventario": "inventario implementos", "implemento": "inventario elemento",
    "elemento": "inventario implemento", "equipo": "equipo torneo",
    "interfichas": "interfichas torneo ficha", "fichas": "interfichas torneo",
    "intercentros": "intercentros competencia centro", "centros": "intercentros",
    # Acciones
    "reservar": "reserva gimnasio", "reservacion": "reserva gimnasio",
    "pedir": "prestamo solicitar", "solicitar": "prestamo solicitar",
    "prestar": "prestamo solicitar", "devolver": "devolucion prestamo",
    "inscribir": "inscripcion equipo torneo", "inscripcion": "inscripcion equipo",
    "postular": "postulacion intercentros", "postularse": "postulacion intercentros",
    "anotar": "inscripcion registrar",
    # Estados
    "abierto": "abierto estado gimnasio", "cerrado": "cerrado estado gimnasio",
    "pendiente": "pendiente reserva aprobacion", "activo": "activo estado",
    "sancionado": "sancion penalizado", "sancion": "sancion penalizado prestamo",
    # Números
    "cuantos": "cantidad total numero", "cuantas": "cantidad total numero",
    "cuanto": "cantidad total", "total": "total cantidad numero",
    "hay": "hay cantidad disponible", "tiene": "tiene cantidad",
    # Misc
    "hoy": "hoy fecha actual", "ahora": "ahora estado actual",
    "resultado": "resultado marcador partido", "marcador": "resultado marcador",
    "tabla": "tabla posiciones clasificacion",
}


# ============================================================
# CONOCIMIENTO BASE — ampliado
# ============================================================
CONOCIMIENTO_BASE = [
    # ── MÓDULOS ─────────────────────────────────────────────
    {
        "pregunta": "qué es el gimnasio módulo gimnasio para qué sirve gimnasio gym ejercicio pesas",
        "respuesta": (
            "El módulo de **Gimnasio** administra las instalaciones deportivas del SENA Centro Minero. "
            "Con él puedes:\n"
            "• Gestionar **reservas de ingreso** (crear, aprobar, rechazar)\n"
            "• Controlar el **estado** del gimnasio: abierto, cerrado o en mantenimiento\n"
            "• Configurar **horarios** de apertura y cierre\n"
            "• Establecer la **capacidad máxima** de usuarios simultáneos\n"
            "Solo los administradores pueden cambiar el estado y aprobar reservas."
        ),
        "modulo": "gimnasio",
    },
    {
        "pregunta": "qué es inventario módulo inventario implementos deportivos elementos equipo materiales stock",
        "respuesta": (
            "El módulo de **Inventario** controla todos los implementos deportivos del Centro Minero. "
            "Permite:\n"
            "• **Registrar** elementos con cantidad, estado y docente responsable\n"
            "• **Gestionar préstamos** activos y devoluciones\n"
            "• **Aplicar sanciones** por daños o pérdidas\n"
            "• Consultar el **stock disponible** en tiempo real"
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "qué son las interfichas módulo interfichas torneos entre fichas ficha aprendices disciplina",
        "respuesta": (
            "El módulo de **Interfichas** organiza torneos deportivos entre las fichas de aprendices del SENA. "
            "Funcionalidades:\n"
            "• Crear **torneos por disciplina** (fútbol, baloncesto, voleibol, etc.)\n"
            "• **Inscribir equipos** por número de ficha y programa\n"
            "• Registrar **partidos por fases**: grupos, cuartos, semifinal, final\n"
            "• Consultar la **tabla de posiciones** actualizada automáticamente"
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "qué son los intercentros módulo intercentros competencias entre centros regional nacional representar",
        "respuesta": (
            "El módulo de **Intercentros** gestiona competencias entre diferentes centros del SENA a nivel regional/nacional. "
            "Permite:\n"
            "• Ver **torneos activos** por disciplina\n"
            "• **Postularse** como aprendiz para representar al Centro Minero\n"
            "• Confirmar **asistencia a entrenamientos**\n"
            "• Ver los seleccionados para cada competencia"
        ),
        "modulo": "intercentros",
    },

    # ── GIMNASIO ─────────────────────────────────────────────
    {
        "pregunta": "cómo hago una reserva gimnasio reservar reserva pendiente aprobación cuándo puedo ir",
        "respuesta": (
            "Para **reservar en el gimnasio**:\n"
            "1. Ve al módulo **Gimnasio**\n"
            "2. Completa el formulario: nombre, fecha, hora de entrada y hora de salida\n"
            "3. Tu reserva queda en estado **'Pendiente'** esperando aprobación\n"
            "4. Un administrador la aprueba o rechaza — puedes ver el estado en tu perfil\n\n"
            "⚠️ Solo puedes reservar si el gimnasio está **abierto** y hay cupos disponibles."
        ),
        "modulo": "gimnasio",
    },
    {
        "pregunta": "estado gimnasio abierto cerrado horario reservas pendientes cuántas apertura cierre capacidad",
        "respuesta": (
            "El estado actual del gimnasio y sus reservas pendientes dependen de la configuración en tiempo real. "
            "Usa el botón **🏋️ Gimnasio** para obtener los datos más recientes, o visita el módulo directamente."
        ),
        "modulo": "gimnasio",
    },
    {
        "pregunta": "quién puede aprobar reserva gimnasio administrador encargado rechazar",
        "respuesta": (
            "Solo los usuarios con rol **Administrador** pueden aprobar o rechazar reservas del gimnasio. "
            "Si tu reserva lleva mucho tiempo en 'Pendiente', contacta al encargado deportivo del Centro Minero."
        ),
        "modulo": "gimnasio",
    },

    # ── INVENTARIO ───────────────────────────────────────────
    {
        "pregunta": "cómo pedir préstamo implemento deportivo solicitar préstamo elemento balón cancha",
        "respuesta": (
            "Para **pedir un préstamo** de implemento deportivo:\n"
            "1. Ve al módulo **Inventario**\n"
            "2. Selecciona el **elemento disponible**\n"
            "3. Indica la **cantidad** y la **fecha de devolución**\n"
            "4. El préstamo quedará **activo** inmediatamente\n\n"
            "⚠️ Recuerda devolver a tiempo para evitar sanciones. Si tienes una sanción activa no podrás hacer nuevos préstamos."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "sanción sancionado qué pasa si no devuelvo implemento penalizado restriccion",
        "respuesta": (
            "Si no devuelves un implemento a tiempo o lo devuelves dañado:\n"
            "• El sistema registra una **sanción** con fecha de inicio y fin\n"
            "• Mientras la sanción esté activa, **no puedes solicitar nuevos préstamos**\n"
            "• Consulta tu estado en **Inventario → Sanciones**\n\n"
            "Para resolver una sanción, contacta al docente responsable del inventario."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "cuántos implementos hay inventario elementos deportivos disponibles stock cantidad total",
        "respuesta": (
            "Los datos del inventario se actualizan en tiempo real. "
            "Usa el botón **📦 Inventario** para ver la lista completa con cantidades y estados actuales."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "devolver implemento como devolver prestamo activo devolución",
        "respuesta": (
            "Para **devolver un implemento** prestado:\n"
            "1. Ve a **Inventario → Mis Préstamos**\n"
            "2. Selecciona el préstamo activo\n"
            "3. Confirma la devolución\n\n"
            "Si el implemento tiene daños, el sistema puede registrar una observación. "
            "Siempre devuelve en el mismo estado en que lo recibiste."
        ),
        "modulo": "inventario",
    },

    # ── INTERFICHAS ──────────────────────────────────────────
    {
        "pregunta": "cómo inscribir equipo torneo interfichas inscripción equipo ficha programa aprendices",
        "respuesta": (
            "Para **inscribir un equipo** en Interfichas:\n"
            "1. Ve al módulo **Interfichas**\n"
            "2. Selecciona el **torneo activo**\n"
            "3. Ingresa: número de ficha, nombre del programa, nombre del equipo, capitán y jugadores\n"
            "4. El equipo queda en estado **'Inscrito'** automáticamente\n\n"
            "Asegúrate de que todos los jugadores sean aprendices activos de la ficha indicada."
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "resultado partido marcador goles puntos sets tabla posiciones clasificacion fase grupo",
        "respuesta": (
            "Los **resultados de partidos** Interfichas se registran en el módulo por cada fase del torneo:\n"
            "• **Fase de grupos** → resultados por jornada\n"
            "• **Eliminatorias** → cuartos, semifinal y final\n\n"
            "El marcador varía por disciplina: goles (fútbol), puntos (baloncesto), sets (voleibol). "
            "La **tabla de posiciones** se actualiza automáticamente con cada resultado registrado."
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "cuántos torneos interfichas activos equipos partidos jugados disciplinas",
        "respuesta": (
            "Los datos de torneos activos, equipos y partidos se actualizan en tiempo real. "
            "Usa el botón **📋 Interfichas** para ver el resumen actual del sistema."
        ),
        "modulo": "interfichas",
    },

    # ── INTERCENTROS ─────────────────────────────────────────
    {
        "pregunta": "cómo postularme intercentros postulación aprendiz participar competencia regional seleccionado",
        "respuesta": (
            "Para **postularte a Intercentros**:\n"
            "1. Ve al módulo **Intercentros**\n"
            "2. Busca el torneo activo en tu disciplina\n"
            "3. Completa el formulario: documento, nombres, apellidos, ficha y programa\n"
            "4. Confirma tu **asistencia a entrenamientos** cuando sean programados\n\n"
            "La selección final la realiza el docente encargado según rendimiento en entrenamientos."
        ),
        "modulo": "intercentros",
    },
    {
        "pregunta": "cuántos torneos intercentros activos postulaciones aprendices inscritos competencias",
        "respuesta": (
            "Los datos de torneos Intercentros y postulaciones se actualizan en tiempo real. "
            "Visita el módulo **Intercentros** para ver los torneos activos y el estado de tu postulación."
        ),
        "modulo": "intercentros",
    },

    # ── GENERAL / AYUDA ──────────────────────────────────────
    {
        "pregunta": "hola buenos días buenas tardes ayuda cómo estás bienvenido saludo",
        "respuesta": (
            "¡Hola! 🐱 Soy **Tux**, tu asistente del Sistema de Gestión Deportiva del SENA Centro Minero.\n\n"
            "Puedo ayudarte con:\n"
            "• 🏋️ **Gimnasio** — reservas, horarios, estado\n"
            "• 📦 **Inventario** — implementos, préstamos, sanciones\n"
            "• 📋 **Interfichas** — torneos, equipos, resultados\n"
            "• 🏆 **Intercentros** — competencias, postulaciones\n\n"
            "También puedo consultar **datos en tiempo real** de la base de datos. ¿En qué te ayudo?"
        ),
        "modulo": "general",
    },
    {
        "pregunta": "gracias perfecto listo excelente ok chao hasta luego",
        "respuesta": (
            "¡Con gusto! 😊 Si tienes más preguntas sobre el sistema deportivo del SENA, aquí estaré. "
            "Recuerda que puedo consultar datos actuales del gimnasio, inventario, torneos y competencias."
        ),
        "modulo": "general",
    },
    {
        "pregunta": "qué puedes hacer qué sabes funciones capacidades módulos sistema",
        "respuesta": (
            "Soy **Tux** y puedo ayudarte con todo el Sistema de Gestión Deportiva:\n\n"
            "📊 **Consultas en tiempo real:**\n"
            "• Estado y reservas del gimnasio\n"
            "• Stock del inventario deportivo\n"
            "• Torneos y equipos de Interfichas\n"
            "• Competencias de Intercentros\n\n"
            "📚 **Guías de uso:**\n"
            "• Cómo hacer reservas\n"
            "• Cómo solicitar préstamos\n"
            "• Cómo inscribir equipos\n"
            "• Cómo postularse a Intercentros\n\n"
            "También puedo escuchar tus preguntas por **voz** 🎤 — presiona el micrófono para hablar."
        ),
        "modulo": "general",
    },
    {
        "pregunta": "quién eres nombre asistente bot ia tux",
        "respuesta": (
            "Soy **Tux** 🐱, el asistente de inteligencia artificial del Sistema de Gestión Deportiva del SENA Centro Minero. "
            "Estoy construido con un motor de IA propio (sin APIs externas) que aprende directamente "
            "de los datos de la base de datos del sistema. ¡Pregúntame lo que necesites!"
        ),
        "modulo": "general",
    },
    {
        "pregunta": "disciplina deportiva fútbol baloncesto voleibol atletismo natación deporte",
        "respuesta": (
            "El sistema gestiona múltiples **disciplinas deportivas** en los módulos de Interfichas e Intercentros. "
            "Las más comunes en el Centro Minero incluyen fútbol, baloncesto, voleibol y atletismo. "
            "Consulta los torneos activos en el módulo correspondiente para ver qué disciplinas están disponibles actualmente."
        ),
        "modulo": "general",
    },
]


# ============================================================
# CLASE MOTOR IA
# ============================================================
class MotorIA:
    """
    Motor de IA con TF-IDF + BM25 híbrido.
    Aprende de los datos reales de la BD Django.
    Soporta contexto multi-turno y expansión de sinónimos.
    """

    RUTA_MODELO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ia_model.pkl")

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),       # unigramas, bigramas y trigramas
            min_df=1,
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w+\b",
        )
        self.conocimiento = []
        self.matriz_tfidf = None
        self._bm25 = None
        self._entrenado = False
        self.ultima_actualizacion = None

    # ── ENTRENAMIENTO ────────────────────────────────────────
    def entrenar(self, datos_bd: dict):
        self.conocimiento = list(CONOCIMIENTO_BASE)

        self._agregar_docs_inventario(datos_bd)
        self._agregar_docs_gimnasio(datos_bd)
        self._agregar_docs_interfichas(datos_bd)
        self._agregar_docs_intercentros(datos_bd)

        # Corpus = pregunta + respuesta (más contexto semántico)
        corpus = [
            self._limpiar(doc["pregunta"] + " " + doc.get("respuesta", ""))
            for doc in self.conocimiento
        ]
        self.matriz_tfidf = self.vectorizer.fit_transform(corpus)

        # BM25 sobre tokens del corpus
        if BM25_DISPONIBLE:
            tokenized = [c.split() for c in corpus]
            self._bm25 = BM25Okapi(tokenized)

        self._entrenado = True
        self.ultima_actualizacion = datetime.now().isoformat()
        self._guardar()
        return len(self.conocimiento)

    def _agregar_docs_inventario(self, datos_bd):
        elementos = datos_bd.get("inventario", [])
        prestamos = datos_bd.get("prestamos_activos", 0)
        if elementos:
            lista = ", ".join(
                f"{e['nombre']} ({e['cantidad']} uds, {e['estado']})"
                for e in elementos
            )
            self.conocimiento.append({
                "pregunta": "cuántos implementos hay inventario elementos deportivos disponibles stock cantidad total lista",
                "respuesta": (
                    f"📦 **Inventario deportivo actual:**\n{lista}\n\n"
                    f"Préstamos activos en este momento: **{prestamos}**."
                ),
                "modulo": "inventario",
            })
            for e in elementos:
                self.conocimiento.append({
                    "pregunta": f"{e['nombre'].lower()} cantidad estado implemento inventario disponible",
                    "respuesta": (
                        f"El elemento **'{e['nombre']}'** tiene **{e['cantidad']} unidades** en total. "
                        f"Estado: {e['estado']}. "
                        f"Responsable: {e.get('responsable', 'no registrado')}."
                    ),
                    "modulo": "inventario",
                })

    def _agregar_docs_gimnasio(self, datos_bd):
        reservas = datos_bd.get("reservas_pendientes", 0)
        config = datos_bd.get("config_gimnasio", {})
        estado = config.get("estado", "no disponible")
        apertura = config.get("apertura", "07:00")
        cierre = config.get("cierre", "17:00")
        capacidad = config.get("capacidad", 40)

        estado_emoji = {"abierto": "🟢", "cerrado": "🔴", "mantenimiento": "🟡"}.get(
            estado.lower(), "⚪"
        )

        self.conocimiento.append({
            "pregunta": "estado gimnasio abierto cerrado horario reservas pendientes cuántas apertura cierre capacidad gym",
            "respuesta": (
                f"🏋️ **Estado del Gimnasio:**\n"
                f"{estado_emoji} Estado actual: **{estado}**\n"
                f"🕐 Horario: {apertura} – {cierre}\n"
                f"👥 Capacidad máxima: {capacidad} personas\n"
                f"📋 Reservas pendientes de aprobación: **{reservas}**"
            ),
            "modulo": "gimnasio",
        })

    def _agregar_docs_interfichas(self, datos_bd):
        torneos = datos_bd.get("torneos_interfichas", [])
        equipos_total = datos_bd.get("equipos_interfichas", 0)
        partidos = datos_bd.get("partidos_jugados", 0)

        for t in torneos:
            self.conocimiento.append({
                "pregunta": f"torneo {t['nombre'].lower()} interfichas disciplina equipos fecha lugar estado inscrito",
                "respuesta": (
                    f"📋 **Torneo Interfichas: {t['nombre']}**\n"
                    f"🏅 Disciplina: {t.get('disciplina', 'no especificada')}\n"
                    f"📌 Estado: {t.get('estado', 'activo')}\n"
                    f"📅 Fecha: {t.get('fecha', 'por definir')}\n"
                    f"📍 Lugar: {t.get('lugar', 'por definir')}\n"
                    f"👥 Equipos inscritos: {t.get('num_equipos', 0)}"
                ),
                "modulo": "interfichas",
            })

        resumen = ", ".join(t["nombre"] for t in torneos) if torneos else "ninguno activo por el momento"
        self.conocimiento.append({
            "pregunta": "cuántos torneos interfichas activos equipos partidos jugados resumen total fichas",
            "respuesta": (
                f"📋 **Resumen Interfichas:**\n"
                f"Torneos activos: {resumen}\n"
                f"Total de equipos inscritos: **{equipos_total}**\n"
                f"Partidos jugados hasta ahora: **{partidos}**"
            ),
            "modulo": "interfichas",
        })

    def _agregar_docs_intercentros(self, datos_bd):
        torneos = datos_bd.get("torneos_intercentros", [])
        postulaciones = datos_bd.get("postulaciones", 0)

        for t in torneos:
            self.conocimiento.append({
                "pregunta": f"torneo {t['nombre'].lower()} intercentros disciplina postulaciones competencia regional",
                "respuesta": (
                    f"🏆 **Torneo Intercentros: {t['nombre']}**\n"
                    f"🏅 Disciplina: {t.get('disciplina', '?')}\n"
                    f"📌 Estado: {t.get('estado', 'activo')}\n"
                    f"📅 Fecha: {t.get('fecha', 'por definir')}\n"
                    f"📍 Lugar: {t.get('lugar', 'por definir')}"
                ),
                "modulo": "intercentros",
            })

        resumen = ", ".join(t["nombre"] for t in torneos) if torneos else "ninguno activo por el momento"
        self.conocimiento.append({
            "pregunta": "cuántos torneos intercentros activos postulaciones aprendices inscritos competencias regional",
            "respuesta": (
                f"🏆 **Resumen Intercentros:**\n"
                f"Torneos activos: {resumen}\n"
                f"Total de postulaciones registradas: **{postulaciones}**"
            ),
            "modulo": "intercentros",
        })

    # ── INFERENCIA ───────────────────────────────────────────
    def responder(self, pregunta: str, historial: list = None) -> dict:
        if not self._entrenado:
            return {
                "respuesta": "⚠️ El motor IA aún no ha sido entrenado. Ejecuta `python ia_trainer.py` primero.",
                "confianza": 0.0,
                "modulo": "error",
            }

        pregunta_limpia = self._limpiar(self._expandir_sinonimos(pregunta))

        # Contexto: últimas 2 preguntas del usuario
        contexto = ""
        if historial:
            msgs_usuario = [
                self._limpiar(m["content"])
                for m in historial[-6:]
                if m.get("role") == "user"
            ]
            contexto = " ".join(msgs_usuario[-2:]) + " "

        query = contexto + pregunta_limpia

        # ── Score TF-IDF ──
        vec_query = self.vectorizer.transform([query])
        sim_tfidf = cosine_similarity(vec_query, self.matriz_tfidf)[0]

        # ── Score BM25 (si disponible) ──
        if BM25_DISPONIBLE and self._bm25:
            tokens_query = query.split()
            scores_bm25 = np.array(self._bm25.get_scores(tokens_query))
            # Normalizar BM25 a [0,1]
            max_bm25 = scores_bm25.max()
            if max_bm25 > 0:
                scores_bm25 = scores_bm25 / max_bm25
            # Combinar: 60% TF-IDF + 40% BM25
            scores_finales = 0.6 * sim_tfidf + 0.4 * scores_bm25
        else:
            scores_finales = sim_tfidf

        idx_mejor = int(np.argmax(scores_finales))
        confianza = float(scores_finales[idx_mejor])

        # Confianza mínima
        if confianza < 0.04:
            return {
                "respuesta": (
                    "🤔 No encontré información exacta sobre eso en el sistema. "
                    "Puedo ayudarte con:\n"
                    "• 🏋️ Gimnasio (reservas, horarios)\n"
                    "• 📦 Inventario (implementos, préstamos)\n"
                    "• 📋 Interfichas (torneos, equipos)\n"
                    "• 🏆 Intercentros (competencias, postulaciones)\n\n"
                    "¿Puedes reformular tu pregunta?"
                ),
                "confianza": round(confianza, 4),
                "modulo": "desconocido",
            }

        doc = self.conocimiento[idx_mejor]
        return {
            "respuesta": doc["respuesta"],
            "confianza": round(confianza, 4),
            "modulo": doc.get("modulo", "general"),
        }

    # ── PERSISTENCIA ─────────────────────────────────────────
    def _guardar(self):
        with open(self.RUTA_MODELO, "wb") as f:
            pickle.dump({
                "vectorizer": self.vectorizer,
                "conocimiento": self.conocimiento,
                "matriz_tfidf": self.matriz_tfidf,
                "bm25": self._bm25,
                "ultima_actualizacion": self.ultima_actualizacion,
            }, f)

    @classmethod
    def cargar(cls):
        motor = cls()
        if os.path.exists(cls.RUTA_MODELO):
            try:
                with open(cls.RUTA_MODELO, "rb") as f:
                    datos = pickle.load(f)
                motor.vectorizer = datos["vectorizer"]
                motor.conocimiento = datos["conocimiento"]
                motor.matriz_tfidf = datos["matriz_tfidf"]
                motor._bm25 = datos.get("bm25")
                motor.ultima_actualizacion = datos.get("ultima_actualizacion")
                motor._entrenado = True
            except Exception as e:
                print(f"[MotorIA] Error cargando modelo: {e}. Se creará uno nuevo al entrenar.")
        return motor

    # ── UTILIDADES ───────────────────────────────────────────
    @staticmethod
    def _limpiar(texto: str) -> str:
        texto = texto.lower().strip()
        texto = re.sub(r"[¿?¡!.,;:\"'()\[\]{}\*#]", " ", texto)
        texto = re.sub(r"\s+", " ", texto)
        reemplazos = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
        }
        for src, dst in reemplazos.items():
            texto = texto.replace(src, dst)
        return texto.strip()

    @staticmethod
    def _expandir_sinonimos(texto: str) -> str:
        palabras = texto.lower().split()
        expandido = []
        for p in palabras:
            expandido.append(p)
            if p in SINONIMOS:
                expandido.append(SINONIMOS[p])
        return " ".join(expandido)