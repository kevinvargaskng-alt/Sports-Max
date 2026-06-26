# Documento de Especificaciones Técnicas (Stack Tecnológico)

Este documento detalla la selección y justificación del stack tecnológico utilizado en el desarrollo y propuesto para la producción del proyecto **Sport-Max**.

---

## 💻 1. Resumen del Stack Tecnológico

El sistema adopta una arquitectura desacoplada donde el servidor web principal corre sobre **Django** (Python) y se integra internamente con un microservicio de Inteligencia Artificial que ejecuta **Flask** (Python) con bibliotecas de Machine Learning local.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INTERFAZ DE USUARIO (HTML5)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Peticiones HTTP
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       SERVIDOR PRINCIPAL (DJANGO)                      │
│            • Lógica de Negocio              • Base de Datos SQLite/Postgres │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Consulta Interna REST
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       MOTOR DE INTELIGENCIA ARTIFICIAL                 │
│            • Flask API                      • Scikit-Learn / Numpy     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 2. Justificación de Tecnologías (Desarrollo)

### 2.1 Backend: Django 6.0.4 & Python
* **Justificación:** Django es un framework web de alto nivel ("con baterías incluidas") que promueve el desarrollo rápido y el diseño limpio. 
* **Ventajas clave:**
  * **Seguridad por defecto:** Protección integrada contra inyecciones SQL, Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF) y secuestro de clics.
  * **ORM Potente:** Permite mapear modelos de datos en Python y portarlos fácilmente a cualquier motor relacional sin escribir código SQL directo.
  * **Panel de Administración integrado:** Provee una interfaz lista para que instructores y administradores gestionen usuarios, inventario y aforos.

### 2.2 Motor de Inteligencia Artificial: Flask, Scikit-Learn y Numpy
* **Justificación:** El asistente de conversación Tux procesa intenciones en lenguaje natural y sugiere respuestas automáticas.
* **Ventajas clave:**
  * **Procesamiento Local:** Scikit-Learn y Numpy ejecutan un clasificador Naive Bayes con vectorización TF-IDF que corre en memoria. Esto evita costes de APIs externas de pago (como OpenAI o Anthropic) y protege los datos personales.
  * **Servidor Flask Independiente:** Flask es un microframework extremadamente rápido y ligero, idóneo para exponer el motor de IA como un microservicio interno en el puerto 5001.

### 2.3 Base de Datos: SQLite3
* **Justificación:** Para el entorno de desarrollo, SQLite3 es una base de datos local en disco que no requiere instalación de software de servidor (como Postgres o MySQL), facilitando la portabilidad del proyecto.

---

## 🚀 3. Especificaciones y Recomendaciones para Producción

Para el despliegue del sistema en un entorno productivo real, se definen las siguientes especificaciones:

### 3.1 Base de Datos de Producción: PostgreSQL (Recomendado)
* **Justificación:** SQLite3 bloquea la base de datos completa durante las operaciones de escritura. En producción, la concurrencia de reservas de gimnasio y préstamos simultáneos causaría errores de bloqueo. PostgreSQL ofrece aislamiento de transacciones de alta velocidad y concurrencia real.

### 3.2 Servidor de Aplicación (WSGI / ASGI)
* **Django:** Utilizar **Gunicorn** como servidor de aplicaciones WSGI para manejar procesos concurrentes de Django detrás de un proxy.
* **Flask IA:** Utilizar **Gunicorn** o **Waitress** para servir la API de Flask de forma estable y con múltiples hilos de ejecución.

### 3.3 Proxy Inverso: Nginx
* **Justificación:** Nginx debe actuar como la puerta de entrada para todas las peticiones externas. Se encarga de:
  * Servir archivos estáticos (`/static/`) y multimedia (`/media/`) con un alto rendimiento de caché.
  * Redireccionar peticiones dinámicas a Gunicorn (Django) en el puerto 8000.
  * Cifrar las conexiones mediante certificados SSL/TLS (HTTPS obligatorio).

### 3.4 Seguridad de Producción en `settings.py`
Al desplegar en producción, es obligatorio realizar las siguientes modificaciones de configuración:
```python
# settings.py (Producción)
DEBUG = False
ALLOWED_HOSTS = ['midominio.sena.edu.co']

# Cargar variables de entorno reales
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
```
