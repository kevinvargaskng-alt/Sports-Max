from inventario.models import ElementoDeportivo, Prestamo, Sancion
from interfichas.models import TorneoInterfichas, EquipoInterfichas, JugadorEquipo
from gimnasio.models import Reserva
import json
import urllib.request
import urllib.error
import os
import base64
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


@csrf_exempt
def transcribe_voice_api(request):
    """Recibe un archivo de audio grabado por el usuario y lo transcribe usando Gemini API"""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    
    if not request.FILES or 'audio' not in request.FILES:
        return JsonResponse({"error": "No se recibió archivo de audio."}, status=400)
        
    try:
        audio_file = request.FILES['audio']
        audio_bytes = audio_file.read()
        
        # Obtener la API key de Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return JsonResponse({"error": "Clave API de Gemini no configurada en el servidor."}, status=500)
            
        # Determinar el tipo de contenido del archivo
        mime_type = audio_file.content_type
        if not mime_type or 'audio' not in mime_type:
            mime_type = "audio/webm"  # fallback
            
        # Codificar a base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Llamar a Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
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
            
        # Extraer el texto de la respuesta
        try:
            transcripcion = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        except (KeyError, IndexError):
            transcripcion = ""
            
        return JsonResponse({"text": transcripcion})
        
    except Exception as e:
        return JsonResponse({"error": f"Error al procesar el audio: {str(e)}"}, status=500)

