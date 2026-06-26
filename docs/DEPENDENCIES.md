# Identificación de Dependencias y Librerías Externas

Este documento lista y justifica el uso de cada una de las librerías de terceros especificadas en el archivo [requirements.txt](file:///c:/Users/varga/OneDrive/Desktop/Django/requirements.txt) del proyecto **Sport-Max**.

---

## 📦 Dependencias Declaradas

| Dependencia / Paquete | Versión Declarada | Categoría | Propósito en el Proyecto |
|---|---|---|---|
| **Django** | `6.0.4` | Framework Web | Framework principal del backend. Provee el enrutador de URLs, motor ORM, gestión de plantillas HTML y sistema de seguridad y administración. |
| **asgiref** | `3.11.1` | Concurrencia | Provee soporte para interfaces de servidor asíncronas ASGI (usado internamente por Django para peticiones asíncronas). |
| **pillow** | `12.2.0` | Procesamiento de Imágenes | Permite cargar, validar y procesar imágenes de perfil de los usuarios (`foto_perfil` en `Usuario`) y fotos de los elementos deportivos (`imagen` en `ElementoDeportivo`). |
| **sqlparse** | `0.5.5` | Utilidad SQL | Permite formatear, parsear y analizar sentencias SQL generadas por el ORM de Django durante la depuración. |
| **tzdata** | `2026.1` | Localización | Base de datos de zonas horarias de la IANA, necesaria para la gestión y validación correcta del tiempo local colombiano (`America/Bogota`). |
| **flask** | *Última estable* | API e Inteligencia Artificial | Microframework web utilizado para construir el servidor API local e independiente que ejecuta el motor de Inteligencia Artificial Tux (puerto 5001). |
| **flask-cors** | *Última estable* | API y Seguridad | Habilita peticiones cruzadas (CORS) permitiendo que las peticiones REST provenientes de Django (puerto 8000) sean procesadas de manera segura por el servidor de Flask (puerto 5001). |
| **scikit-learn** | *Última estable* | Machine Learning / NLP | Biblioteca matemática que implementa los algoritmos de clasificación de textos (clasificador Naive Bayes y vectorizador TF-IDF) para deducir la intención y módulo al que pertenece la pregunta del usuario en el chatbot. |
| **numpy** | *Última estable* | Cálculo Matemático | Biblioteca para realizar operaciones de álgebra lineal y matrices numéricas que sirve como base para el entrenamiento y clasificación en Scikit-Learn. |

---

## 🛠️ Instalación y Mantenimiento

Para instalar todas las dependencias en un entorno de desarrollo limpio, active su entorno virtual y ejecute:
```bash
pip install -r requirements.txt
```

Para registrar una nueva dependencia y asegurar que el equipo la tenga disponible, instale la librería y actualice el archivo con:
```bash
pip freeze > requirements.txt
```
*Asegurarse de mantener las versiones acotadas para evitar incompatibilidades en la compilación o despliegue del proyecto.*
