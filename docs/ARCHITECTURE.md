# Arquitectura de Software y Estructura de Directorios

Este documento detalla el patrón de arquitectura utilizado en **Sport-Max** y describe la distribución física del código fuente en el repositorio.

---

## 🏛️ Patrón Arquitectónico: Model-View-Template (MVT)

Sport-Max está construido sobre **Django**, el cual utiliza el patrón de diseño **MVT (Modelo-Vista-Plantilla)**, una variante del conocido Modelo-Vista-Controlador (MVC):

```
                        ┌──────────────────┐
                        │      Cliente     │
                        │    (Navegador)   │
                        └────────┬─────────┘
                                 │ ▲ (HTML/HTTP)
                      Petición   │ │ Respuesta
                               ▼ │
                        ┌────────┴─────────┐
                        │     URLs.py      │ (Enrutamiento)
                        └────────┬─────────┘
                                 │
                               ▼ │
                        ┌────────┴─────────┐
         ┌─────────────►│     Views.py     │◄─────────────┐
         │              └──────────────────┘              │
         │ (Consulta/                                     │ (Renderizado/
         │  Persistencia)                                 │  Inyección)
         ▼                                                ▼
┌──────────────────┐                            ┌──────────────────┐
│     Models.py    │                            │    Templates/    │
│  (Base de Datos) │                            │      (HTML)      │
└──────────────────┘                            └──────────────────┘
```

1. **Modelo (Model - `models.py`):** Define la estructura lógica de los datos y encapsula las reglas de negocio y persistencia en la base de datos a través del ORM de Django.
2. **Vista (View - `views.py`):** Contiene la lógica del lado del servidor para procesar las peticiones HTTP de los usuarios, interactuar con los modelos para recuperar o guardar información y seleccionar la plantilla correspondiente para responder al usuario.
3. **Plantilla (Template - `templates/`):** El motor de representación del frontend en HTML inyectado dinámicamente con la sintaxis de plantillas de Django.

---

## 📂 Estructura de Directorios

La estructura de directorios del proyecto se organiza de la siguiente manera:

```
Sport-Max/
│
├── core/                       # Configuración y enrutamiento central del proyecto
│   ├── settings.py             # Variables de configuración y declaración de apps
│   ├── urls.py                 # Enrutamiento de URLs principales
│   ├── views.py                # Vistas transversales (como chat_tux_api)
│   └── context_processors.py   # Datos inyectados de manera global en las vistas
│
├── usuarios/                   # Aplicación de registro, login y roles de usuario
│   ├── models.py               # Modelos Usuario (Custom) y Sugerencia
│   ├── views.py                # Vistas de autenticación y panel de administración
│   ├── urls.py                 # Enrutador del módulo de usuarios
│   └── templates/              # Formularios de acceso y recuperación de clave
│
├── inventario/                 # Aplicación de préstamo e inventario deportivo
│   ├── models.py               # Elementos deportivos, préstamos y sanciones
│   ├── views.py                # Lógica de préstamo, devolución y reporte de novedades
│   └── urls.py                 # Rutas de inventario y devoluciones
│
├── gimnasio/                   # Aplicación de control de aforo y acceso a gimnasio
│   ├── models.py               # Reservas de aforo y configuración del gimnasio
│   ├── views.py                # Registro de asistencia y panel de aforo máximo
│   └── urls.py                 # Enrutador del módulo de gimnasio
│
├── interfichas/                # Aplicación de torneos y partidos deportivos
│   ├── models.py               # Disciplinas, Torneos, Equipos, Partidos y Resultados
│   ├── views.py                # Generación de llaves del torneo y marcadores
│   └── urls.py                 # Rutas del módulo interfichas
│
├── habitos_saludables/         # Aplicación de seguimiento antropométrico y salud
│   ├── models.py               # SeguimientoSalud (IMC), Rutinas y Pirámide nutricional
│   ├── views.py                # Registro antropométrico e información de salud
│   └── urls.py                 # Rutas del módulo de hábitos
│
├── static/                     # Archivos estáticos compartidos (CSS, JS, imágenes)
│   ├── css/                    # Hojas de estilo personalizadas
│   └── js/                     # Scripts de interacción del frontend
│
├── templates/                  # Carpetas de plantillas HTML globales
│   ├── base.html               # Estructura maestra del frontend
│   └── ...                     # Plantillas comunes
│
├── media/                      # Archivos cargados por usuarios (fotos de perfil)
│
├── scripts/                    # Scripts auxiliares y Servidor de IA local
│   ├── ia_engine.py            # Motor de entrenamiento y procesamiento de lenguaje
│   ├── ia_server.py            # API local Flask para el chat inteligente TUX
│   └── poblar_sistema.py       # Script de carga inicial de datos de prueba
│
├── docs/                       # Documentación técnica del proyecto (este directorio)
├── requirements.txt            # Dependencias externas del proyecto
└── manage.py                   # Utilidad CLI para administración de Django
```
