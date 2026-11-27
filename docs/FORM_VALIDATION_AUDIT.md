# Auditoría de validación de formularios

## Alcance inspeccionado

Se encontraron 66 etiquetas `<form>` en 19 plantillas, dos módulos `forms.py` de aplicación (`usuarios` y `habitos_saludables`), además de formularios declarativos auxiliares en `core/security/validators.py`. La mayoría de las operaciones de inventario, gimnasio e interfichas procesan `request.POST` directamente en las vistas. Por eso, una regla HTML o JavaScript por sí sola no protege esos endpoints.

## Hallazgos por pantalla

| Pantalla / plantilla | Formularios encontrados | Hallazgos principales |
| --- | --- | --- |
| `inicio/inicio.html` | Inicio de sesión, registro, desbloqueo | El registro ya tenía longitudes y algunos patrones; nombres permitían apóstrofes y guiones, y el teléfono no comprobaba prefijo colombiano. Se endurecieron formulario, modelo, atributos y JS. El desbloqueo tenía validación manual y se alineó el teléfono a diez dígitos con prefijo 3. |
| `usuarios/perfil.html` | Editar perfil, prueba física, reportar/editar/eliminar reportes | El correo y la carga de imagen tenían validación de servidor. El celular aceptaba cualquier prefijo; ahora exige 3 inicial y diez dígitos. Los comentarios se sanitizan parcialmente, pero edición/respuesta de reportes aún necesita límites y errores enlazados al campo. |
| `usuarios/gestionar_usuarios.html` | Filtros, editar usuario, cambiar rol | El rol usa lista permitida. La edición de nombre solo verificaba texto seguro (permitía números/símbolos) y no comprobaba correo duplicado; se corrigió. Filtros y persistencia de errores requieren revisión individual. |
| `usuarios/gestionar_backups.html` | Restauración de respaldo | Tiene controles de permisos y carga; requiere revisar límites/tipo de archivo y confirmación de datos en la vista de restauración. |
| `usuarios/registration/password_reset*.html` | Solicitar y confirmar restablecimiento | Django valida el formato/token y contraseña. Hay que revisar la vista para conservar valores no sensibles y mostrar errores en español consistentes. |
| `inventario/inventario.html` | Crear/editar elemento, préstamo y acciones de eliminación | Las vistas validan cantidades, fechas, permisos y relaciones en varios caminos; existen conversiones manuales y límites no siempre reflejados en HTML. `tipo_maquina` recibe un validador de nombre alfanumérico con guiones (`# REVISAR`: nombres/modelos de implementos pueden incluir puntuación legítima). |
| `inventario/devoluciones.html` | Registrar devolución | Validación manual de cantidad y estado del préstamo; ahora hay límite según saldo pendiente, y la novedad requiere tipo. El modelo limita cantidad; textos libres aún requieren normalización uniforme. |
| `inventario/sanciones.html` | Crear/editar/cerrar sanción | La vista valida fechas, rangos y estado permitido. El modelo ahora también rechaza fecha final anterior a inicial. Falta mostrar errores conservando el formulario en lugar de redirigir. |
| Reportes de inventario/gimnasio/usuarios/hábitos | Filtros GET | Son búsquedas, no altas. Hay controles de formato dispersos; límite y normalización de parámetros deben revisarse por endpoint para evitar filtros inválidos. |
| `gimnasio/gimnasio.html` y `machine_list.html` | Configuración, fechas, franjas, reservas, máquinas y acciones | Hay validaciones de fecha, hora, aforo, estado y franja en vistas; varios valores JSON y conversiones se validan localmente. Se añadieron límites de aforo/permanencia y validación de fecha de salida en modelos. Nombres de máquina son alfanuméricos por compatibilidad con modelos (`# REVISAR`). |
| `interfichas/interfichas.html` y `gestion/gestionar_torneo.html` | Torneos, disciplinas, equipos, jugadores, resultados, grupos y cronogramas | Las vistas validan muchas relaciones y resultados, pero hay conversiones `int()` manuales y campos de texto con reglas no uniformes. Se añadieron validadores a ficha de siete dígitos, nombre de capitán/jugador y documento de jugador; nombre de equipo admite números (`# REVISAR`). |
| `habitos_saludables/salud.html` | Consentimiento, seguimiento y registro de hábitos | `HabeasDataForm` y `SeguimientoSaludForm` ya validaban rangos, choices y presión; se sanitizan observaciones. El registro diario usa vistas manuales y requiere revisión de fechas/duplicados. |
| `habitos_saludables/receta_form.html` | Crear/editar receta | Se migró a `RecetaSaludableForm` (ModelForm): valida números, rangos, choices, archivo, longitud y limpia HTML; el template conserva los valores enviados y muestra errores por campo. |
| `habitos_saludables/contenido_educativo.html` | Filtro de biblioteca | Choice de tipo protegido por `BuscarMaterialForm`; la búsqueda se limita y limpia. |
| `interfichas/gestion/gestionar_torneo.html` | Eliminaciones, generación de fases y cronograma | Muchos forms son acciones, sin campos libres; IDs y estado del torneo se validan en endpoints, pero hay que mantener validación de pertenencia y errores por cada acción. |

## Cambios compartidos aplicados

- `core/validators.py`: validadores reutilizables de letras, dígitos, teléfono colombiano, códigos alfanuméricos, normalización de espacios y limpieza de HTML/scripts en texto libre.
- `static/js/sportsmax_validators.js`: valida los forms antes de enviar, conserva los valores, señala el campo, añade `invalid-feedback` y muestra un diálogo en español. Usa SweetAlert2 si ya está cargado; en este proyecto utiliza el diálogo local `smaxDialog` como respaldo.
- `usuarios/forms.py`, `usuarios/models.py`, `usuarios/views.py`: endurece nombres, teléfono y duplicidad de correo en los flujos cubiertos.
- Modelos de inventario, gimnasio e interfichas: añade límites numéricos y validadores de campos principales, además de fecha fin/inicio de sanción y salida/entrada.
- `habitos_saludables/forms.py`: limpia etiquetas y limita títulos, descripciones y observaciones de los formularios declarados.

## Pendientes detectados

El inventario estático abarca los formularios anteriores, pero no se añadió una capa genérica a cada endpoint manual: aplicar una misma regla a todos los POST podría clasificar mal texto libre, nombres comerciales, códigos y acciones AJAX. La configuración del gimnasio, parte de la edición de resultados/respuestas de reportes y otras acciones AJAX aún deben revisarse por endpoint. Los nombres comerciales de máquina/implemento y equipo quedan anotados `# REVISAR` porque pueden contener números de modelo.
