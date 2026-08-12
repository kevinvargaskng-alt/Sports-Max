# Estrategia de Persistencia de Datos y Base de Datos

Este documento define la estrategia de almacenamiento del proyecto **Sport-Max**, la estructura del motor de base de datos y las directrices para la gestión de migraciones en entornos de desarrollo y producción.

---

## 💾 1. Motor de Base de Datos y Estrategia

Sport-Max utiliza el **ORM de Django (Object-Relational Mapping)** para gestionar toda la persistencia. Esto permite desacoplar la lógica de negocio en Python del motor de base de datos relacional subyacente.

### 1.1 Entorno de Desarrollo (Local)
* **Motor:** SQLite3 (`db.sqlite3`).
* **Justificación:** Es una base de datos ligera basada en archivos locales que no requiere instalación de servicios de servidor en la máquina de desarrollo, lo que facilita el inicio rápido del proyecto.

### 1.2 Entorno de Producción (Recomendado)
* **Motor:** PostgreSQL o MySQL.
* **Justificación:** SQLite3 bloquea todo el archivo de base de datos durante las escrituras, lo cual genera problemas de concurrencia e inestabilidad con múltiples usuarios concurrentes reservando aforo o solicitando elementos deportivos. PostgreSQL ofrece control de concurrencia multiversión (MVCC) ideal para producción.

---

## 🗺️ 2. Mapeo Objeto-Relacional (Relaciones Críticas)

Los modelos de Django especifican las siguientes estructuras y cardinalidades:

1. **Relaciones Uno a Muchos (1:N) - `models.ForeignKey`:**
   * **Reservas e Inventario:** Un `Usuario` (aprendiz) puede tener múltiples registros de `Reserva` en el gimnasio y múltiples solicitudes de `Prestamo` de implementos deportivos.
   * **Responsable de Elementos:** Un gestor deportivo (`Usuario`) puede ser el `usuario_responsable` de múltiples `ElementoDeportivo`.
   * **Torneos y Equipos:** Un torneo (`TorneoInterfichas`) inscribe múltiples `EquipoInterfichas`.
2. **Relaciones Muchos a Muchos (M:N) - `models.ManyToManyField`:**
   * **Equipos en Grupos:** Un `GrupoInterfichas` contiene múltiples `EquipoInterfichas`, y a su vez, un equipo puede pertenecer a varios grupos (fases del torneo).
3. **Relaciones Uno a Uno (1:1) - `models.OneToOneField`:**
   * **Resultados de Torneo:** Un `TorneoInterfichas` posee un único `ResultadoTorneo` al finalizar.
   * **Habeas Data:** Un `Usuario` posee un único registro de aceptación de términos `HabeasDataConsent`.

---

## ⚙️ 3. Flujo de Trabajo con Migraciones

Django rastrea los cambios de estructura en los archivos `models.py` y genera archivos de migración (código Python) en la carpeta `migrations/` de cada aplicación.

### 3.1 Pasos para aplicar cambios en la base de datos
Cuando edite o añada campos a un modelo, debe ejecutar los siguientes comandos en la terminal desde el directorio del proyecto:

1. **Generar las migraciones (crear archivos de cambio):**
   ```bash
   .venv\Scripts\python.exe manage.py makemigrations
   ```
2. **Aplicar los cambios en la base de datos local:**
   ```bash
   .venv\Scripts\python.exe manage.py migrate
   ```
3. **Verificar el estado de las migraciones:**
   ```bash
   .venv\Scripts\python.exe manage.py showmigrations
   ```

*Nota: Los archivos de migración en las carpetas `migrations/` deben agregarse al repositorio Git para garantizar que todos los desarrolladores compartan exactamente la misma estructura de base de datos.*
