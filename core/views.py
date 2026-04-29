import json
import os
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# --- IMPORTACIÓN DE TUS MODELOS REALES ---
from gimnasio.models import Entrenamiento, Reserva
from intercentros.models import TorneoIntercentros, EquipoIntercentros, Postulacion
from interfichas.models import TorneoInterfichas, EquipoInterfichas, JugadorEquipo
from inventario.models import ElementoDeportivo, Prestamo, Sancion

@csrf_exempt
def chat_tux_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_usuario = data.get('message', '')

            # --- 1. CONSULTAS A LA BASE DE DATOS EN TIEMPO REAL (AHORA MÁS DETALLADAS) ---
            try:
                # 📦 Inventario: Traemos los nombres y cantidades (limitado a 50 para no saturar la IA)
                elementos_bd = ElementoDeportivo.objects.all()[:50]
                lista_inventario = ", ".join([f"{e.tipo_maquina} ({e.cantidad_total} unidades)" for e in elementos_bd])
                if not lista_inventario:
                    lista_inventario = "Aún no hay elementos registrados."
                
                prestamos_activos = Prestamo.objects.filter(estado_prestamo__iexact='Activo').count()

                # 🏋️‍♂️ Gimnasio:
                reservas_pendientes = Reserva.objects.filter(estado__iexact='Pendiente').count()
                
                # 🏆 Intercentros: Traemos los nombres de los torneos
                torneos_centros_bd = TorneoIntercentros.objects.filter(estado__iexact='Activo')
                nombres_centros = ", ".join([t.nombre_torneo for t in torneos_centros_bd])
                if not nombres_centros:
                    nombres_centros = "No hay torneos activos en este momento."
                
                # 🔄 Interfichas: Traemos los nombres de los torneos
                torneos_fichas_bd = TorneoInterfichas.objects.filter(estado__iexact='activo')
                nombres_fichas = ", ".join([t.nombre_torneo for t in torneos_fichas_bd])
                if not nombres_fichas:
                    nombres_fichas = "No hay torneos activos en este momento."
                
                equipos_fichas = EquipoInterfichas.objects.count()
                
            except Exception as e:
                # En caso de error de base de datos
                lista_inventario = "Error al consultar inventario."
                nombres_centros = "Error al consultar torneos."
                nombres_fichas = "Error al consultar torneos."
                prestamos_activos = reservas_pendientes = equipos_fichas = 0

            # Construimos el texto con los DATOS EXACTOS que leerá Gemini
            contexto_db = f"""
            --- DATOS ACTUALES DE LA BASE DE DATOS ---
            📦 INVENTARIO:
            - Elementos registrados actualmente: {lista_inventario}.
            - Hay {prestamos_activos} préstamos activos.
            
            🏋️‍♂️ GIMNASIO:
            - Hay {reservas_pendientes} reservas pendientes de aprobación.
            
            🏆 INTERCENTROS:
            - Torneos activos actualmente: {nombres_centros}.
            
            🔄 INTERFICHAS:
            - Torneos activos actualmente: {nombres_fichas}.
            - Total de equipos inscritos: {equipos_fichas}.
            """

            # Integramos TUS DEFINICIONES EXACTAS para que la IA sepa qué hace cada módulo
            definiciones_modulos = """
            --- DEFINICIÓN OFICIAL DE LOS MÓDULOS DEL SISTEMA ---
            🏋️‍♂️ Gimnasio
            El módulo de Gimnasio dentro del sistema de gestión deportiva del SENA Centro Minero permite administrar y controlar el uso de este. A través de este apartado, se pueden gestionar registros de ingreso, seguimiento de usuarios y organización de horarios, garantizando un uso adecuado de las instalaciones. 
            
            📦 Inventario
            El módulo de Inventario está diseñado para llevar el control de todos los implementos deportivos disponibles en el Centro Minero. Permite registrar, actualizar y consultar toda la información relacionada con los elementos, como lo es el estado de cada elemento, así optimizando la administración de recursos y evitando pérdidas o mal uso del material deportivo. 
            
            🔄 Interfichas
            El módulo de Interfichas permite la gestión y organización de actividades deportivas entre diferentes fichas o grupos de formación dentro del SENA. A través de este sistema, se pueden programar encuentros, registrar participantes y llevar control de resultados. 
            
            🏆 Intercentros
            El módulo de Intercentros permite la gestión de competencias deportivas entre diferentes centros del SENA a nivel regional o nacional. A través de este apartado, se podrán inscribir los aprendices interesados, informar sobre los horarios de entrenamiento y posteriormente la lista de seleccionados para la conformación de estos equipos que representarán al SENA Centro Minero en estas competiciones.
            """

            # --- 2. CONFIGURAR GEMINI CON TU ARCHIVO .ENV ---
            api_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            
            # --- SELECCIÓN DINÁMICA DE MODELO (A prueba de errores) ---
            modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if not modelos_disponibles:
                return JsonResponse({"error": "La API Key no tiene modelos disponibles."}, status=500)
                
            model = genai.GenerativeModel(modelos_disponibles[0])

            # --- 3. CREAR EL PROMPT MAESTRO (EL CEREBRO DE TUX) ---
            prompt_completo = f"""
            Eres Tux 🐱, el asistente de Inteligencia Artificial del Sistema de Gestión Deportiva.
            
            Tus conocimientos se basan en estas dos fuentes:
            
            {definiciones_modulos}
            
            {contexto_db}
            
            Reglas:
            1. Si el usuario te pregunta "qué es" un módulo, explícaselo basándote en la Definición Oficial.
            2. Si te pregunta "qué hay" o "cuántos", respóndele basándote en los Datos Actuales de la Base de Datos. Menciona los nombres de los torneos o los nombres/cantidades del inventario si te los piden.
            3. Responde siempre en español, de forma amable, clara y muy concisa (máximo 120 palabras).
            
            Mensaje del usuario: {mensaje_usuario}
            """

            # --- 4. GENERAR RESPUESTA ---
            response = model.generate_content(prompt_completo)

            return JsonResponse({"reply": response.text})

        except Exception as e:
            return JsonResponse({"error": f"Error interno en la IA: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido."}, status=405)