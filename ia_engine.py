"""
ia_engine.py — Motor de IA propio para Gestión Deportiva SENA
--------------------------------------------------------------
Sin APIs externas. Usa TF-IDF + cosine similarity de scikit-learn.
Aprende de los datos reales de tu base de datos Django.
"""

import os
import re
import json
import pickle
import math
from datetime import datetime

# ── scikit-learn (pip install scikit-learn) ──────────────────────
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ============================================================
# CONOCIMIENTO BASE (definiciones fijas del sistema)
# ============================================================
CONOCIMIENTO_BASE = [
    {
        "pregunta": "qué es el gimnasio módulo gimnasio para qué sirve gimnasio",
        "respuesta": (
            "El módulo de Gimnasio permite administrar el uso de las instalaciones deportivas del SENA Centro Minero. "
            "Puedes gestionar reservas de ingreso, controlar el estado (abierto, cerrado, mantenimiento), "
            "configurar horarios de apertura y cierre, y establecer la capacidad máxima de usuarios simultáneos."
        ),
        "modulo": "gimnasio",
    },
    {
        "pregunta": "qué es inventario módulo inventario implementos deportivos para qué sirve inventario",
        "respuesta": (
            "El módulo de Inventario controla todos los implementos deportivos del Centro Minero. "
            "Permite registrar elementos con su cantidad, estado y docente responsable, "
            "gestionar préstamos activos, registrar devoluciones y aplicar sanciones por daños o pérdidas."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "qué son las interfichas módulo interfichas torneos entre fichas para qué sirve interfichas",
        "respuesta": (
            "El módulo de Interfichas organiza torneos deportivos entre las fichas de aprendices del SENA. "
            "Puedes crear torneos por disciplina (fútbol, baloncesto, voleibol…), inscribir equipos, "
            "registrar partidos por fases (grupos, cuartos, semifinal, final) y llevar la tabla de posiciones."
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "qué son los intercentros módulo intercentros competencias entre centros para qué sirve intercentros",
        "respuesta": (
            "El módulo de Intercentros gestiona competencias deportivas entre diferentes centros del SENA "
            "a nivel regional o nacional. Los aprendices pueden postularse, asistir a entrenamientos y "
            "ser seleccionados para representar al SENA Centro Minero en estas competencias."
        ),
        "modulo": "intercentros",
    },
    {
        "pregunta": "cómo hago una reserva gimnasio reservar reserva pendiente aprobación",
        "respuesta": (
            "Para hacer una reserva en el gimnasio: ve al módulo Gimnasio, completa el formulario con tu nombre, "
            "fecha de entrada, hora de entrada y hora de salida. La reserva queda en estado 'Pendiente' "
            "hasta que un administrador la aprueba. Puedes consultar el estado en tu perfil."
        ),
        "modulo": "gimnasio",
    },
    {
        "pregunta": "cómo pedir préstamo implemento deportivo solicitar préstamo elemento",
        "respuesta": (
            "Para pedir un préstamo de implemento: ve al módulo Inventario, selecciona el elemento disponible, "
            "indica la cantidad y la fecha de devolución. El préstamo quedará activo. "
            "Recuerda devolver a tiempo para evitar sanciones."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "cómo inscribir equipo torneo interfichas inscripción equipo ficha programa",
        "respuesta": (
            "Para inscribir un equipo en un torneo Interfichas: ve al módulo Interfichas, selecciona el torneo activo, "
            "ingresa el número de ficha, nombre del programa, nombre del equipo, capitán y los jugadores. "
            "El equipo quedará en estado 'Inscrito' automáticamente."
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "cómo postularme intercentros postulación aprendiz participar competencia",
        "respuesta": (
            "Para postularte a un evento Intercentros: ve al módulo Intercentros, busca el torneo activo en tu disciplina "
            "y completa el formulario con tu número de documento, nombres, apellidos, ficha y programa. "
            "Podrás ver los entrenamientos programados y confirmar tu asistencia."
        ),
        "modulo": "intercentros",
    },
    {
        "pregunta": "sanción sancionado qué pasa si no devuelvo implemento",
        "respuesta": (
            "Si no devuelves un implemento a tiempo o lo devuelves en mal estado, el sistema puede registrar una sanción. "
            "Las sanciones tienen fecha de inicio y fin, y mientras estén activas puedes tener restricciones "
            "para solicitar nuevos préstamos. Consulta el módulo Inventario > Sanciones para ver tu estado."
        ),
        "modulo": "inventario",
    },
    {
        "pregunta": "resultado partido marcador goles puntos sets tabla posiciones",
        "respuesta": (
            "Los resultados de los partidos Interfichas se registran en el módulo correspondiente por cada fase del torneo. "
            "Dependiendo de la disciplina, el marcador puede ser goles, puntos o sets. "
            "La tabla de posiciones se actualiza automáticamente con los resultados registrados."
        ),
        "modulo": "interfichas",
    },
    {
        "pregunta": "hola buenos días buenas tardes ayuda cómo estás",
        "respuesta": (
            "¡Hola! 🐱 Soy Tux, tu asistente del Sistema de Gestión Deportiva del SENA Centro Minero. "
            "Puedo ayudarte con información sobre los módulos de Gimnasio, Inventario, Interfichas e Intercentros, "
            "y también consultarte datos actuales de la base de datos. ¿En qué te ayudo?"
        ),
        "modulo": "general",
    },
    {
        "pregunta": "gracias perfecto listo excelente ok",
        "respuesta": (
            "¡Con gusto! 😊 Si tienes más preguntas sobre el sistema deportivo del SENA, aquí estaré. "
            "Recuerda que puedo mostrarte datos actuales del gimnasio, inventario, torneos y mucho más."
        ),
        "modulo": "general",
    },
]


# ============================================================
# CLASE MOTOR IA
# ============================================================
class MotorIA:
    """
    Motor de IA con TF-IDF que aprende de los datos de la BD.
    Se puede serializar (pickle) para persistir entre reinicios.
    """

    RUTA_MODELO = os.path.join(os.path.dirname(__file__), "ia_model.pkl")

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),      # unigramas y bigramas
            min_df=1,
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w+\b",
        )
        self.conocimiento = []        # lista de dicts {pregunta, respuesta, modulo, datos_db}
        self.matriz_tfidf = None      # np array (n_docs, n_features)
        self._entrenado = False
        self.ultima_actualizacion = None

    # ── ENTRENAMIENTO ────────────────────────────────────────
    def entrenar(self, datos_bd: dict):
        """
        Combina el conocimiento base con los datos reales de la BD
        y ajusta el vectorizador TF-IDF.

        datos_bd = {
            "inventario": [...],
            "prestamos_activos": int,
            "reservas_pendientes": int,
            "torneos_interfichas": [...],
            "equipos_interfichas": int,
            "torneos_intercentros": [...],
            "postulaciones": int,
            "partidos_jugados": int,
        }
        """
        self.conocimiento = list(CONOCIMIENTO_BASE)

        # ── Documentos dinámicos generados desde la BD ──
        self._agregar_docs_inventario(datos_bd)
        self._agregar_docs_gimnasio(datos_bd)
        self._agregar_docs_interfichas(datos_bd)
        self._agregar_docs_intercentros(datos_bd)

        # ── Ajustar vectorizador ──
        corpus = [doc["pregunta"] + " " + doc.get("respuesta", "") for doc in self.conocimiento]
        self.matriz_tfidf = self.vectorizer.fit_transform(corpus)
        self._entrenado = True
        self.ultima_actualizacion = datetime.now().isoformat()

        # Persistir modelo
        self._guardar()
        return len(self.conocimiento)

    def _agregar_docs_inventario(self, datos_bd):
        elementos = datos_bd.get("inventario", [])
        if elementos:
            lista = ", ".join(
                f"{e['nombre']} ({e['cantidad']} uds, estado: {e['estado']})"
                for e in elementos
            )
            prestamos = datos_bd.get("prestamos_activos", 0)
            self.conocimiento.append({
                "pregunta": "cuántos implementos hay inventario elementos deportivos disponibles stock",
                "respuesta": (
                    f"Actualmente el inventario registra estos elementos: {lista}. "
                    f"Hay {prestamos} préstamo(s) activo(s) en este momento."
                ),
                "modulo": "inventario",
            })
            for e in elementos:
                self.conocimiento.append({
                    "pregunta": f"{e['nombre'].lower()} cantidad estado implemento",
                    "respuesta": (
                        f"El elemento '{e['nombre']}' tiene {e['cantidad']} unidades en total, "
                        f"estado: {e['estado']}. Responsable: {e.get('responsable', 'no registrado')}."
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
        self.conocimiento.append({
            "pregunta": "estado gimnasio abierto cerrado horario reservas pendientes cuántas",
            "respuesta": (
                f"El gimnasio está actualmente en estado: {estado}. "
                f"Horario: {apertura} a {cierre}. Capacidad máxima: {capacidad} personas. "
                f"Hay {reservas} reserva(s) pendiente(s) de aprobación."
            ),
            "modulo": "gimnasio",
        })

    def _agregar_docs_interfichas(self, datos_bd):
        torneos = datos_bd.get("torneos_interfichas", [])
        equipos_total = datos_bd.get("equipos_interfichas", 0)
        partidos = datos_bd.get("partidos_jugados", 0)
        if torneos:
            for t in torneos:
                self.conocimiento.append({
                    "pregunta": f"torneo {t['nombre'].lower()} interfichas disciplina equipos fecha lugar",
                    "respuesta": (
                        f"El torneo '{t['nombre']}' de {t.get('disciplina', 'disciplina no especificada')} "
                        f"está {t.get('estado', 'activo')}. "
                        f"Fecha: {t.get('fecha', 'por definir')}. Lugar: {t.get('lugar', 'por definir')}. "
                        f"Equipos inscritos: {t.get('num_equipos', 0)}."
                    ),
                    "modulo": "interfichas",
                })
        resumen = ", ".join(t["nombre"] for t in torneos) if torneos else "ninguno activo"
        self.conocimiento.append({
            "pregunta": "cuántos torneos interfichas activos equipos partidos jugados",
            "respuesta": (
                f"Torneos Interfichas activos: {resumen}. "
                f"Total de equipos inscritos en el sistema: {equipos_total}. "
                f"Partidos jugados: {partidos}."
            ),
            "modulo": "interfichas",
        })

    def _agregar_docs_intercentros(self, datos_bd):
        torneos = datos_bd.get("torneos_intercentros", [])
        postulaciones = datos_bd.get("postulaciones", 0)
        if torneos:
            for t in torneos:
                self.conocimiento.append({
                    "pregunta": f"torneo {t['nombre'].lower()} intercentros disciplina postulaciones",
                    "respuesta": (
                        f"El torneo Intercentros '{t['nombre']}' de {t.get('disciplina', '?')} "
                        f"está {t.get('estado', 'activo')}. "
                        f"Fecha: {t.get('fecha', 'por definir')}. Lugar: {t.get('lugar', 'por definir')}."
                    ),
                    "modulo": "intercentros",
                })
        resumen = ", ".join(t["nombre"] for t in torneos) if torneos else "ninguno activo"
        self.conocimiento.append({
            "pregunta": "cuántos torneos intercentros activos postulaciones aprendices inscritos",
            "respuesta": (
                f"Torneos Intercentros activos: {resumen}. "
                f"Total de postulaciones registradas: {postulaciones}."
            ),
            "modulo": "intercentros",
        })

    # ── INFERENCIA ───────────────────────────────────────────
    def responder(self, pregunta: str, historial: list = None) -> dict:
        """
        Devuelve la mejor respuesta para la pregunta del usuario.
        historial = [{"role": "user"|"assistant", "content": str}, ...]
        """
        if not self._entrenado:
            return {
                "respuesta": "El motor IA aún no ha sido entrenado. Llama a /ia/entrenar/ primero.",
                "confianza": 0.0,
                "modulo": "error",
            }

        pregunta_limpia = self._limpiar(pregunta)

        # Enriquecer con contexto del historial (última pregunta del usuario)
        contexto = ""
        if historial:
            for msg in reversed(historial[-4:]):
                if msg.get("role") == "user":
                    contexto = self._limpiar(msg["content"]) + " "
                    break
        query = contexto + pregunta_limpia

        vec_query = self.vectorizer.transform([query])
        similitudes = cosine_similarity(vec_query, self.matriz_tfidf)[0]
        idx_mejor = int(np.argmax(similitudes))
        confianza = float(similitudes[idx_mejor])

        doc = self.conocimiento[idx_mejor]

        # Si la confianza es muy baja, respuesta genérica
        if confianza < 0.05:
            return {
                "respuesta": (
                    "No encontré información exacta sobre eso en el sistema. "
                    "Puedo ayudarte con información sobre los módulos de "
                    "Gimnasio, Inventario, Interfichas e Intercentros del SENA Centro Minero. "
                    "¿Puedes reformular tu pregunta?"
                ),
                "confianza": confianza,
                "modulo": "desconocido",
            }

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
                "ultima_actualizacion": self.ultima_actualizacion,
            }, f)

    @classmethod
    def cargar(cls):
        motor = cls()
        if os.path.exists(cls.RUTA_MODELO):
            with open(cls.RUTA_MODELO, "rb") as f:
                datos = pickle.load(f)
            motor.vectorizer = datos["vectorizer"]
            motor.conocimiento = datos["conocimiento"]
            motor.matriz_tfidf = datos["matriz_tfidf"]
            motor.ultima_actualizacion = datos.get("ultima_actualizacion")
            motor._entrenado = True
        return motor

    # ── UTILIDADES ───────────────────────────────────────────
    @staticmethod
    def _limpiar(texto: str) -> str:
        texto = texto.lower().strip()
        texto = re.sub(r"[¿?¡!.,;:\"'()\[\]{}]", " ", texto)
        texto = re.sub(r"\s+", " ", texto)
        # Normalizar caracteres especiales comunes en español
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "ü": "u", "ñ": "n",
        }
        for src, dst in replacements.items():
            texto = texto.replace(src, dst)
        return texto.strip()