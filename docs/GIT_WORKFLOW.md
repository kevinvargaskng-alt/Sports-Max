# Flujo de Trabajo en Git y Control de Versiones

Este documento define la estrategia de control de versiones y el flujo de ramificación que se utiliza para el desarrollo del proyecto **Sport-Max**.

---

## 🌿 1. Modelo de Ramas (GitHub Flow Modificado)

El flujo de trabajo se basa en ramas de funcionalidades cortas y estables que se integran en una rama principal de manera ordenada:

```
 main (Producción)   ───────────────────────────●──────────────────────────
                                               ▲ (Merge)
                                              ╱
                                             ╱ (Pull Request / Review)
 feature/modulo-xyz   ──────●────────●──────●
                         (Commit) (Commit) (PR)
```

1. **`main` (Rama Principal):**
   * Es la rama de producción oficial.
   * Su código siempre debe compilar, estar libre de errores críticos y listo para desplegar.
   * **Restricción:** No se permiten desarrollos directos ni commits sobre esta rama.
2. **`feature/` (Ramas de Funcionalidades):**
   * Ramas temporales creadas a partir de `main` para desarrollar nuevas historias de usuario o tareas.
   * Formato de nomenclatura: `feature/nombre-funcionalidad` (ej. `feature/pruebas-unitarias`, `feature/seguridad-perfiles`).
3. **`bugfix/` (Ramas de Parches):**
   * Creadas a partir de `main` para solucionar errores o fallos detectados en producción de forma inmediata.
   * Formato de nomenclatura: `bugfix/descripcion-error` (ej. `bugfix/aforo-gimnasio`).

---

## 📝 2. Estándar de Mensajes de Commit

Los mensajes de commit deben describir con claridad el cambio realizado siguiendo el estándar de **Conventional Commits**:

```
<tipo>: <descripción en minúscula y en español>
```

* **`feat`:** Nueva funcionalidad (ej. `feat: agregar formulario de anamnesis en gimnasio`).
* **`fix`:** Corrección de un bug (ej. `fix: corregir error de fecha en préstamos de elementos`).
* **`docs`:** Cambios en la documentación (ej. `docs: crear guia de arquitectura y git`).
* **`test`:** Creación o modificación de pruebas unitarias (ej. `test: agregar pruebas de login de usuarios`).
* **`style`:** Formateo, estilos visuales, orden de código sin cambios en lógica (ej. `style: aplicar pep8 a modelos de inventario`).

---

## 🛠️ 3. Ciclo de Desarrollo e Integración

Para desarrollar una nueva funcionalidad, siga estos pasos:

1. **Crear e ir a la nueva rama:**
   ```bash
   git checkout -b feature/nombre-funcionalidad
   ```
2. **Desarrollar y realizar commits locales organizados:**
   ```bash
   git add .
   git commit -m "feat: descripcion del cambio"
   ```
3. **Subir la rama al repositorio remoto:**
   ```bash
   git push origin feature/nombre-funcionalidad
   ```
4. **Crear un Pull Request (PR):**
   * Solicitar la integración de la rama en `main` a través de la interfaz web (GitHub, GitLab, etc.).
   * Completar la descripción del PR explicando el cambio y qué historias de usuario satisface.
   * Confirmar que la suite de pruebas unitarias locales pasa exitosamente antes de realizar el merge.
