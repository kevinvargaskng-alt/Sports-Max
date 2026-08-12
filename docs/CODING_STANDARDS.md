# Estándares de Codificación y Nomenclatura

Este documento establece las reglas de estilo y nomenclatura que todo desarrollador debe seguir en el proyecto **Sport-Max** para garantizar un código limpio, legible y fácil de mantener.

---

## 🐍 1. Estándares en Python (Backend y Django)

Se sigue la guía de estilo oficial de la comunidad de Python, **PEP 8**, con las siguientes precisiones:

### 1.1 Nomenclatura
* **Clases:** CamelCase (ej. `ElementoDeportivo`, `TorneoInterfichas`).
* **Funciones y Métodos:** snake_case (ej. `calcular_imc`, `registrar_prestamo`).
* **Variables y Atributos:** snake_case (ej. `codigo_prestamo`, `fecha_entrada`).
* **Constantes:** UPPER_CASE (ej. `IA_SERVER_URL`, `TIPO_DOC`).
* **Nombres de Archivos:** Todo en minúscula, utilizando guiones bajos si es necesario (ej. `context_processors.py`).

### 1.2 Importaciones
Las importaciones deben agruparse en el siguiente orden, separadas por una línea en blanco:
1. **Librerías estándar de Python:** (ej. `os`, `sys`, `json`, `datetime`).
2. **Librerías externas de terceros:** (ej. `django`, `flask`, `dotenv`).
3. **Módulos locales del proyecto:** (ej. `from usuarios.models import Usuario`).

*Evitar importaciones absolutas con asterisco (`from modulo import *`). Importar clases o funciones explícitamente.*

### 1.3 Comentarios y Docstrings
* Toda clase compleja o función de negocio debe documentarse con un **docstring** descriptivo detallando su funcionalidad, argumentos y retorno.
  ```python
  def calcular_imc(self):
      """
      Calcula el índice de masa corporal (IMC) del usuario.
      Retorna float (redondeado a 2 decimales) o None si no hay datos de peso/estatura.
      """
      ...
  ```
* Usar comentarios en línea (`#`) con moderación para explicar el "por qué" de una línea de código compleja, no el "qué hace".

---

## 🗄️ 2. Estándares en Bases de Datos (Modelos y Campos)

* **Nombres de Modelos:** Singular y en CamelCase (ej. `Sancion`, `Reserva`).
* **Nombres de Campos:** Minúscula y en snake_case (ej. `numero_documento`).
* **Claves Primarias:** Por defecto, Django asigna `id` de forma automática. Sin embargo, para mayor claridad en el MER de Sport-Max se pueden definir claves primarias explícitas utilizando `models.AutoField` (ej. `codigo_prestamo = models.AutoField(primary_key=True)`).
* **Claves Foráneas (Relaciones):** Siempre definir el comportamiento ante eliminaciones (`on_delete=models.CASCADE` o `on_delete=models.SET_NULL`).

---

## 🌐 3. Estándares en Frontend (HTML, CSS y Javascript)

### 3.1 Plantillas HTML (Templates)
* Formateo semántico (HTML5) usando etiquetas como `<header>`, `<main>`, `<section>`, `<footer>`.
* Los IDs y Clases de elementos CSS deben nombrarse en minúsculas y separados por guiones (kebab-case) (ej. `id="chat-box"`, `class="btn-primary"`).
* Los archivos de plantillas deben guardarse dentro de carpetas organizadas por aplicación (ej. `templates/usuarios/login.html`).

### 3.2 Hojas de Estilo CSS
* Utilizar un archivo central (`index.css` o `style.css`) con variables de CSS globales para mantener una paleta de colores uniforme y consistencia visual en fuentes y espaciados.

### 3.3 Javascript
* Nombres de variables y funciones en camelCase (ej. `chatHistory`, `sendMessage`).
* Manejar estrictamente la separación de la lógica del HTML: no incrustar scripts inline en el HTML. Usar detectores de eventos (`addEventListener`) en archivos `.js` externos.
