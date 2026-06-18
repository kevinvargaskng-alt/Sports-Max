from inventario.models import ElementoDeportivo, Prestamo, Sancion
from interfichas.models import TorneoInterfichas, EquipoInterfichas, JugadorEquipo
from gimnasio.models import Reserva
import json
import urllib.request
import urllib.error
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# URL del servidor IA
IA_SERVER_URL = "http://127.0.0.1:5001"

# Importación de modelos reales


@csrf_exempt
def chat_tux_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    try:
        data = json.loads(request.body)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])
        if not mensaje:
            return JsonResponse({"error": "El mensaje está vacío."}, status=400)
        payload = json.dumps(
            {"message": mensaje, "history": historial}).encode("utf-8")
        req = urllib.request.Request(
            f"{IA_SERVER_URL}/ia/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resultado = json.loads(resp.read().decode("utf-8"))
        return JsonResponse({
            "reply": resultado.get("reply", "Sin respuesta del motor IA."),
            "modulo": resultado.get("modulo", "general"),
        })
    except urllib.error.URLError:
        return JsonResponse({
            "error": "El Motor IA no está disponible. Asegúrate de que ia_server.py esté corriendo en el puerto 5001."
        }, status=503)
    except Exception as e:
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)
