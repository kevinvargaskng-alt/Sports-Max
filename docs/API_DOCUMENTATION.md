# Documentación de Puntos de Integración (APIs y Endpoints)

Este documento detalla los puntos de integración y endpoints JSON que utiliza el frontend y servicios internos para comunicarse con el backend de **Sport-Max**.

---

## 🤖 1. Chatbot Asistente Inteligente TUX

El chatbot inteligente utiliza un servidor Flask local independiente (puerto 5001) que procesa el lenguaje natural y se comunica con Django mediante peticiones internas.

### 1.1 Endpoint de Chat (Acceso Público Autorizado)
* **URL:** `/api/chat-tux/`
* **Método:** `POST`
* **Tipo de Contenido:** `application/json`
* **Descripción:** Endpoint público que utiliza el frontend (mediante llamadas fetch/AJAX) para enviar preguntas al asistente inteligente.
* **Cuerpo de la Petición (Payload):**
  ```json
  {
    "message": "¿Cuáles son las reglas del voleibol?",
    "history": [
      {"user": "Hola", "bot": "¡Hola! Soy el asistente inteligente TUX. ¿En qué puedo ayudarte?"}
    ]
  }
  ```
* **Respuesta Exitosa (HTTP 200 OK):**
  ```json
  {
    "reply": "En el voleibol, cada equipo tiene un máximo de 3 toques para pasar el balón al campo contrario...",
    "modulo": "interfichas"
  }
  ```
* **Respuesta de Error de Disponibilidad (HTTP 503 Service Unavailable):**
  ```json
  {
    "error": "El Motor IA no está disponible. Asegúrate de que ia_server.py esté corriendo en el puerto 5001."
  }
  ```

---

## 🔒 2. Gestión de Usuarios e Integración Administrativa

Estas rutas son llamadas desde el frontend de administración (`gestionar_usuarios.html`) para realizar operaciones asíncronas de base de datos sin recargar la página completa.

### 2.1 Cambiar Estado Activo/Inactivo de un Usuario
* **URL:** `/perfil/toggle/<int:user_id>/`
* **Método:** `POST`
* **Restricción:** Solo accesible por usuarios administradores (`is_staff = True`).
* **Descripción:** Cambia el estado del usuario entre `activo` e `inactivo` para suspender temporalmente el acceso de un aprendiz.
* **Respuesta Exitosa (HTTP 302 Redirect o JSON según cliente):**
  * Redirecciona de vuelta a la interfaz de gestión con un mensaje `messages.success`.

### 2.2 Modificar el Rol de un Usuario
* **URL:** `/perfil/rol/<int:user_id>/`
* **Método:** `POST`
* **Restricción:** Solo accesible por usuarios administradores.
* **Cuerpo de la Petición (Form Data):**
  * `rol`: Cadena de texto (ej. `aprendiz`, `instructor`, `gestor_deportivo`, `administrador`).
* **Descripción:** Cambia el perfil de permisos del usuario seleccionado.
* **Respuesta Exitosa (HTTP 302 Redirect):**
  * Redirecciona de vuelta a la interfaz de gestión.

---

## ⚙️ 3. Integración Interna de IA (Django a Flask)

El servidor Django llama internamente al servidor Flask para consultar y reentrenar el motor de lenguaje.

### 3.1 Consulta de Similitud Semántica
* **URL:** `http://127.0.0.1:5001/ia/chat`
* **Método:** `POST`
* **Cuerpo de la Petición (JSON):**
  ```json
  {
    "message": "pregunta del usuario",
    "history": []
  }
  ```
* **Respuesta (HTTP 200 OK):**
  ```json
  {
    "reply": "respuesta del motor",
    "confianza": 0.88,
    "modulo": "nombre_modulo"
  }
  ```

### 3.2 Sincronización y Reentrenamiento
* **URL:** `http://127.0.0.1:5001/ia/entrenar`
* **Método:** `POST`
* **Descripción:** Envía datos consolidados de la base de datos de Django (elementos, torneos, aforos) al motor Flask para reentrenar los clasificadores de IA locales.
