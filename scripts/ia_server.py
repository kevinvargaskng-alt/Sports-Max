"""
ia_server.py — Servidor Flask del Motor IA propio
--------------------------------------------------
Corre independiente de Django en el puerto 5001.
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

# Cambio clave: Permitir CORS de forma más flexible para desarrollo local
CORS(app, resources={r"/ia/*": {"origins": "*"}})

# ── Cargar o crear el motor ───────────────────────────────
log.info("Cargando motor IA...")
motor = MotorIA.cargar()
if motor._entrenado:
    log.info(f"Modelo cargado. Última actualización: {motor.ultima_actualizacion}")
    log.info(f"Documentos en conocimiento: {len(motor.conocimiento)}")
else:
    log.warning("Motor sin entrenar. Llama a POST /ia/entrenar para inicializarlo.")

# ============================================================
# RUTAS
# ============================================================

@app.route("/ia/chat", methods=["POST"])
def chat():
    try:
        # force=True ayuda si el content-type llega ligeramente mal
        data = request.get_json(force=True)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])

        if not mensaje:
            return jsonify({"error": "El campo 'message' está vacío."}), 400

        resultado = motor.responder(mensaje, historial)

        log.info(f"Pregunta: '{mensaje[:60]}' | Módulo: {resultado['modulo']} | Confianza: {resultado['confianza']}")

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
    return jsonify({
        "entrenado": motor._entrenado,
        "documentos": len(motor.conocimiento) if motor._entrenado else 0,
        "ultima_actualizacion": motor.ultima_actualizacion,
        "modelo_existe": os.path.exists(MotorIA.RUTA_MODELO),
    })

if __name__ == "__main__":
    PORT = int(os.environ.get("IA_PORT", 5001))
    log.info(f"Motor IA iniciando en http://127.0.0.1:{PORT}")
    # threaded=True permite manejar varias peticiones de Django a la vez
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)