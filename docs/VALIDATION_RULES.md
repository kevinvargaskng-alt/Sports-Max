# Reglas de Validación de Datos

Este documento detalla las restricciones de integridad y validaciones aplicadas tanto en el cliente (interfaz de usuario) como en el servidor (backend) para el sistema **Sport-Max**.

---

## 🛡️ 1. Mapeo de Validaciones por Entidad

### 1.1 Gestión de Usuarios (`Usuario`)
| Campo / Regla | Ubicación | Tipo de Validación | Detalle / Restricción |
|---|---|---|---|
| `numero_documento` | Frontend / Servidor | Unicidad y longitud | Campo obligatorio. Debe ser único en la BD. En el HTML se restringe a valores numéricos o texto según el `tipo_documento` y tiene una longitud máxima de 20 caracteres. |
| `email` | Frontend / Servidor | Unicidad y formato | Debe tener estructura válida de correo electrónico (ej. `nombre@sena.edu.co`). Es de valor único e indexado. |
| `tipo_documento` | Servidor | Lista de Opciones | Validado contra la lista de choices: `CC` (Cédula), `TI` (Tarjeta de Identidad), `CE` (Cédula de Extranjería), `PA` (Pasaporte). |
| `estado` | Servidor | Lista de Opciones | Validado contra la lista de choices: `activo`, `inactivo`, `retiro_voluntario`, `cancelado`. |

### 1.2 Módulo de Inventario (`Prestamo` / `Devolucion`)
| Campo / Regla | Ubicación | Tipo de Validación | Detalle / Restricción |
|---|---|---|---|
| `cantidad_prestada` | Servidor / Frontend | Lógica de stock | La cantidad que se solicita en préstamo debe ser mayor a 0 y menor o igual a la cantidad total disponible del elemento deportivo (`cantidad_total` en `ElementoDeportivo`). |
| `estado_prestamo` | Servidor | Lista de Opciones | Por defecto 'Activo'. Transiciona a 'Devuelto' al realizar la devolución. |
| `dias_prestamo` | Servidor / Frontend | Rango Numérico | Número entero mayor a 0 (máximo 5 días para préstamos temporales). |
| `devolucion_novedad` | Servidor | Lógica de negocio | Si `tiene_novedad = True` en `Devolucion`, es obligatorio rellenar el campo `tipo_novedad_devolucion` y `estado_elemento_devolucion`. |

### 1.3 Módulo de Gimnasio (`Reserva` / `GimnasioConfig`)
| Campo / Regla | Ubicación | Tipo de Validación | Detalle / Restricción |
|---|---|---|---|
| `aforo_maximo` | Servidor / Frontend | Rango Numérico | La capacidad del gimnasio debe ser un entero positivo (por defecto 40). |
| `bloqueo_dias` | Servidor | Lógica horaria | No se permite crear reservas los fines de semana o los días feriados configurados (lista de festivos de Colombia definidos en `gimnasio/views.py`). |
| `horas_ingreso` | Servidor | Rango de horario | La hora de la reserva de gimnasio debe encontrarse dentro del horario de apertura y cierre configurados (por defecto entre las 07:00 y las 17:00). |

### 1.4 Módulo de Hábitos Saludables (`SeguimientoSalud`)
| Campo / Regla | Ubicación | Tipo de Validación | Detalle / Restricción |
|---|---|---|---|
| `peso_kg` | Servidor / Frontend | Rango Numérico | Restringido entre 20.00 kg y 300.00 kg mediante `MinValueValidator` y `MaxValueValidator` en Django. |
| `estatura_cm` | Servidor / Frontend | Rango Numérico | Restringido entre 100.00 cm y 250.00 cm mediante `MinValueValidator` y `MaxValueValidator`. |
| `horas_sueno` | Servidor / Frontend | Rango Numérico | Decimal positivo menor o igual a 24.0 horas. |
| `imc` | Servidor | Cálculo automático | Campo calculado automáticamente en el método `save()` dividiendo el peso (kg) entre la estatura al cuadrado (metros). |

---

## 🛠️ 2. Mecanismos de Validación Utilizados

### 2.1 Backend (Django ORM y Formularios)
1. **Validadores de Modelos (`django.core.validators`):** Usados para validar rangos numéricos directamente en los campos del modelo (ej. `MinValueValidator`).
2. **Métodos `clean_<campo>()` y `clean()`:** Implementados en las clases de formularios (`forms.py`) para realizar validaciones cruzadas (por ejemplo, validar que la fecha de devolución sea posterior a la de préstamo).
3. **Restricciones de BD (`unique=True`):** Validadas a nivel del motor de base de datos relacional para evitar registros duplicados.

### 2.2 Frontend (Integridad en el Cliente)
1. **Atributos de Validación HTML5:** Se utilizan atributos como `required`, `type="email"`, `min`, `max`, `step="0.01"`, `pattern` para prevenir errores de entrada del usuario antes del envío al servidor.
2. **Javascript para validación interactiva:** Validación de formularios en tiempo real (por ejemplo, deshabilitar botones de envío si las contraseñas en el formulario de registro no coinciden).
