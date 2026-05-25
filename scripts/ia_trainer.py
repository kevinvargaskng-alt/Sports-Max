"""
ia_trainer.py — Entrena el motor IA directamente (sin HTTP)
------------------------------------------------------------
Llama al motor IA en memoria, sin necesitar que ia_server.py
esté corriendo. Ideal para Windows donde el firewall bloquea
conexiones locales entre procesos.

Ejecutar:
    python ia_trainer.py
"""

import os
import sys
import logging

# ── Configurar Django ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

# ── Importar modelos Django ───────────────────────────────
from gimnasio.models import Reserva, GimnasioConfig
from inventario.models import ElementoDeportivo, Prestamo
from interfichas.models import TorneoInterfichas, EquipoInterfichas, PartidoInterfichas
from intercentros.models import TorneoIntercentros, Postulacion

# ── Importar motor IA directamente ───────────────────────
from ia_engine import MotorIA

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ia_trainer")


def recopilar_datos() -> dict:
    datos = {}

    # Inventario
    elementos = ElementoDeportivo.objects.all()[:100]
    datos["inventario"] = [
        {
            "nombre": str(e.tipo_maquina),
            "cantidad": int(e.cantidad_total),
            "estado": str(e.estado_general),
            "responsable": str(e.docente_responsable),
        }
        for e in elementos
    ]
    datos["prestamos_activos"] = Prestamo.objects.filter(
        estado_prestamo__iexact="Activo"
    ).count()

    # Gimnasio
    try:
        config = GimnasioConfig.get_config()
        datos["config_gimnasio"] = {
            "estado": config.estado,
            "apertura": str(config.horario_apertura),
            "cierre": str(config.horario_cierre),
            "capacidad": config.capacidad_maxima,
        }
    except Exception:
        datos["config_gimnasio"] = {
            "estado": "no disponible",
            "apertura": "07:00",
            "cierre": "17:00",
            "capacidad": 40,
        }
    datos["reservas_pendientes"] = Reserva.objects.filter(
        estado__iexact="Pendiente"
    ).count()

    # Interfichas
    torneos_fichas = TorneoInterfichas.objects.select_related("disciplina").all()[:20]
    datos["torneos_interfichas"] = []
    for t in torneos_fichas:
        datos["torneos_interfichas"].append({
            "nombre": str(t.nombre_torneo),
            "disciplina": str(t.disciplina) if t.disciplina else "Sin disciplina",
            "estado": str(t.estado),
            "fecha": str(t.fecha_torneo_fichas),
            "lugar": str(t.lugar),
            "num_equipos": t.equipos.count(),
        })
    datos["equipos_interfichas"] = EquipoInterfichas.objects.count()
    datos["partidos_jugados"] = PartidoInterfichas.objects.filter(jugado=True).count()

    # Intercentros
    torneos_centros = TorneoIntercentros.objects.all()[:20]
    datos["torneos_intercentros"] = [
        {
            "nombre": str(t.nombre_torneo),
            "disciplina": str(t.disciplina),
            "estado": str(t.estado),
            "fecha": str(t.fecha_torneo),
            "lugar": str(t.lugar),
        }
        for t in torneos_centros
    ]
    datos["postulaciones"] = Postulacion.objects.count()

    return datos


def main():
    log.info("Recopilando datos de la base de datos Django...")
    datos = recopilar_datos()

    log.info(
        f"Datos recopilados: {len(datos.get('inventario', []))} elementos inventario, "
        f"{len(datos.get('torneos_interfichas', []))} torneos interfichas, "
        f"{len(datos.get('torneos_intercentros', []))} torneos intercentros."
    )

    log.info("Entrenando motor IA directamente en memoria...")
    motor = MotorIA.cargar()
    n_docs = motor.entrenar(datos)

    log.info(f"✅ Motor IA entrenado con {n_docs} documentos.")
    log.info(f"   Modelo guardado en: {MotorIA.RUTA_MODELO}")
    log.info("   Ahora ia_server.py lo cargará automáticamente al arrancar.")


if __name__ == "__main__":
    main()