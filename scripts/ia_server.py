"""
ia_server.py — Servidor Flask del Motor IA propio
--------------------------------------------------
Corre independiente de Django en el puerto 5001.
Django lo llama internamente, sin exponer nada al frontend.

Arrancar:
    python ia_server.py

Rutas:
    POST /ia/chat        — responder pregunta
    POST /ia/entrenar    — (re)entrenar con datos frescos de la BD
    GET  /ia/estado      — ver estado del motor
"""

import os
import sys
import json
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

# Motor IA propio (mismo directorio)
from ia_engine import MotorIA

# ── Configuración de logging ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ia_server")

# ── App Flask ─────────────────────────────────────────────
app = Flask(__name__)

# Solo aceptar llamadas desde localhost (Django)
CORS(app, origins=["http://127.0.0.1:8000", "http://localhost:8000"])

# ── Cargar o crear el motor ───────────────────────────────
log.info("Cargando motor IA...")
motor = MotorIA.cargar()
if motor._entrenado:
    log.info(
        f"Modelo cargado. Última actualización: {motor.ultima_actualizacion}")
    log.info(f"Documentos en conocimiento: {len(motor.conocimiento)}")
else:
    log.warning(
        "Motor sin entrenar. Llama a POST /ia/entrenar para inicializarlo.")


# ============================================================
# RUTAS
# ============================================================

@app.route("/ia/chat", methods=["POST"])
def chat():
    """
    Recibe: { "message": str, "history": [...] }
    Devuelve: { "reply": str, "confianza": float, "modulo": str }
    """
    try:
        data = request.get_json(force=True)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])

        if not mensaje:
            return jsonify({"error": "El campo 'message' está vacío."}), 400

        resultado = motor.responder(mensaje, historial)

        log.info(
            f"Pregunta: '{mensaje[:60]}' | Módulo: {resultado['modulo']} | Confianza: {resultado['confianza']}")

        return jsonify({
            "reply": resultado["respuesta"],
            "confianza": resultado["confianza"],
            "modulo": resultado["modulo"],
        })

    except Exception as e:
        log.error(f"Error en /ia/chat: {e}", exc_info=True)
        return jsonify({"error": f"Error interno del motor IA: {str(e)}"}), 500


@app.route("/ia/entrenar", methods=["POST"])
def entrenar():
    """
    Recibe los datos de la base de datos Django y reentrena el modelo.
    Llamado automáticamente desde ia_trainer.py o manualmente.

    Body esperado:
    {
        "inventario": [{"nombre": str, "cantidad": int, "estado": str, "responsable": str}],
        "prestamos_activos": int,
        "config_gimnasio": {"estado": str, "apertura": str, "cierre": str, "capacidad": int},
        "reservas_pendientes": int,
        "torneos_interfichas": [{"nombre": str, "disciplina": str, "estado": str, "fecha": str, "lugar": str, "num_equipos": int}],
        "equipos_interfichas": int,
        "partidos_jugados": int,
        "torneos_intercentros": [{"nombre": str, "disciplina": str, "estado": str, "fecha": str, "lugar": str}],
        "postulaciones": int,
    }
    """
    try:
        datos_bd = request.get_json(force=True)
        n_docs = motor.entrenar(datos_bd)
        log.info(f"Motor reentrenado con {n_docs} documentos.")
        return jsonify({
            "ok": True,
            "documentos": n_docs,
            "actualizado_en": motor.ultima_actualizacion,
        })
    except Exception as e:
        log.error(f"Error en /ia/entrenar: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/ia/estado", methods=["GET"])
def estado():
    """Devuelve el estado actual del motor."""
    return jsonify({
        "entrenado": motor._entrenado,
        "documentos": len(motor.conocimiento) if motor._entrenado else 0,
        "ultima_actualizacion": motor.ultima_actualizacion,
        "modelo_existe": os.path.exists(MotorIA.RUTA_MODELO),
    })


# ============================================================
# ARRANQUE
# ============================================================
if __name__ == "__main__":
    PORT = int(os.environ.get("IA_PORT", 5001))
    log.info(f"Motor IA iniciando en http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
