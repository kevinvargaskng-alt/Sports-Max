import json
import urllib.request
import urllib.error
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# URL del servidor IA - Asegúrate de que termine sin barra diagonal
IA_SERVER_URL = "http://127.0.0.1:5001"

# Importación de modelos reales (SENA Proyecto ADSO)
from gimnasio.models import Reserva
from intercentros.models import TorneoIntercentros, EquipoIntercentros, Postulacion
from interfichas.models import TorneoInterfichas, EquipoInterfichas, JugadorEquipo
from inventario.models import ElementoDeportivo, Prestamo, Sancion

@csrf_exempt
def chat_tux_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    
    try:
        # 1. Leer datos del frontend
        data = json.loads(request.body)
        mensaje = data.get("message", "").strip()
        historial = data.get("history", [])
        
        if not mensaje:
            return JsonResponse({"error": "El mensaje está vacío."}, status=400)
        
        # 2. Preparar petición para Flask
        payload = json.dumps({"message": mensaje, "history": historial}).encode("utf-8")
        
        # IMPORTANTE: La ruta debe ser EXACTAMENTE /ia/chat como en Flask
        req = urllib.request.Request(
            f"{IA_SERVER_URL}/ia/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        # 3. Llamada al motor con timeout para evitar que Django se cuelgue
        with urllib.request.urlopen(req, timeout=10) as resp:
            resultado = json.loads(resp.read().decode("utf-8"))
        
        return JsonResponse({
            "reply": resultado.get("reply", "Sin respuesta del motor IA."),
            "modulo": resultado.get("modulo", "general"),
            "confianza": resultado.get("confianza", 0)
        })
        
    except urllib.error.URLError as e:
        # Este es el error 503 que estabas viendo
        return JsonResponse({
            "error": "El Motor IA no responde. Verifica que ia_server.py esté activo en el puerto 5001."
        }, status=503)
        
    except Exception as e:
        return JsonResponse({"error": f"Error interno en Django: {str(e)}"}, status=500)