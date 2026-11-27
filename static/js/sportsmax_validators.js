/**
 * Sports-Max — Suite Global de Validación y Sanitización de Formularios (Frontend Vanilla JS)
 * Reglas de negocio:
 * 1. Texto Limpio: Bloqueo de caracteres especiales y auto-conversión a Title Case.
 * 2. Enteros Estrictos: Bloqueo de decimales, negativos, letras y 'e' (Documentos, Fichas, Celulares).
 * 3. Medidas de Salud: Máximo 2 cifras decimales y formateo toFixed(2).
 * 4. Fechas Restringidas: Pasado bloqueado (min: hoy) y límite a futuro (max: hoy + 7 días).
 */

document.addEventListener('DOMContentLoaded', () => {
    initSportsMaxValidators();
});

function initSportsMaxValidators() {
    const REGEX_CARACTERES_PROHIBIDOS = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]/g;

    // 1. TEXTO LIMPIO & TITLE CASE (Nombres, Apellidos, Campos de texto general)
    document.querySelectorAll('.input-texto-limpio, input[name="nombres"], input[name="apellidos"], input[name="first_name"], input[name="last_name"], input[name="capitan"], input[name="ciudad"], input[name="cargo"]').forEach(input => {
        input.setAttribute('pattern', '[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+( [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*');
        input.setAttribute('inputmode', 'text');
        const feedback = ensureValidationFeedback(input);
        input.addEventListener('input', (e) => {
            const el = e.target;
            const previous = el.value;
            el.value = previous.replace(REGEX_CARACTERES_PROHIBIDOS, '').replace(/\s+/g, ' ');
            const changed = previous !== el.value;
            if (changed) el.dataset.validationRejected = 'true';
            else delete el.dataset.validationRejected;
            setFieldValidation(el, changed ? 'El campo solo puede contener letras y espacios.' : '', feedback);
        });

        input.addEventListener('blur', (e) => {
            if (e.target.value) {
                e.target.value = e.target.value
                    .toLowerCase()
                    .split(' ')
                    .filter(word => word.length > 0)
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
            }
        });
    });

    // 2. ENTEROS ESTRICTOS (Documentos, Fichas, Teléfono/Celular, Cantidades)
    document.querySelectorAll('.input-entero-estricto, input[name*="ficha"], input[name*="documento"], input[name*="telefono"], input[name*="celular"]').forEach(input => {
        input.setAttribute('inputmode', 'numeric');
        input.setAttribute('pattern', '[0-9]+');
        const esFicha = input.name && input.name.toLowerCase().includes('ficha');
        input.setAttribute('maxlength', input.getAttribute('maxlength') || (esFicha ? '7' : '10'));
        if (input.name && /telefono|celular/i.test(input.name)) {
            input.setAttribute('minlength', input.getAttribute('minlength') || '10');
            input.setAttribute('maxlength', '10');
            input.setAttribute('pattern', '3[0-9]{9}');
            input.setCustomValidity('');
        }
        input.addEventListener('keydown', (e) => {
            const teclasProhibidas = ['e', 'E', '-', '+', '.', ','];
            if (teclasProhibidas.includes(e.key)) {
                e.preventDefault();
                input.dataset.validationRejected = 'true';
                setFieldValidation(input, 'Este campo solo puede contener dígitos.', numericFeedback);
            }
        });

        const numericFeedback = ensureValidationFeedback(input);
        input.addEventListener('input', (e) => {
            const previous = e.target.value;
            e.target.value = previous.replace(/[^0-9]/g, '');
            const changed = previous !== e.target.value;
            if (changed) e.target.dataset.validationRejected = 'true';
            else delete e.target.dataset.validationRejected;
            setFieldValidation(e.target, changed ? 'Este campo solo puede contener dígitos.' : '', numericFeedback);
        });
    });

    // Campos numéricos nativos en formularios que no usan la clase heredada.
    document.querySelectorAll('input[type="number"]:not(.input-entero-estricto)').forEach(input => {
        input.setAttribute('inputmode', input.step && input.step !== '1' ? 'decimal' : 'numeric');
        const feedback = ensureValidationFeedback(input);
        input.addEventListener('keydown', (event) => {
            const esControl = ['Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || event.ctrlKey || event.metaKey;
            const aceptaDecimal = input.step && input.step !== '1' && ['.', ','].includes(event.key);
            if (!esControl && !aceptaDecimal && !/^\d$/.test(event.key)) {
                event.preventDefault();
                input.dataset.validationRejected = 'true';
                setFieldValidation(input, 'Este campo solo puede contener números positivos.', feedback);
            }
        });
        input.addEventListener('input', () => {
            const antes = input.value;
            const decimal = input.step && input.step !== '1';
            let despues = antes.replace(decimal ? /[^0-9.,]/g : /[^0-9]/g, '');
            if (decimal) {
                despues = despues.replace(',', '.');
                const [entero, ...resto] = despues.split('.');
                despues = resto.length ? `${entero}.${resto.join('')}` : entero;
            }
            input.value = despues;
            const cambio = antes !== despues;
            if (cambio) input.dataset.validationRejected = 'true';
            else delete input.dataset.validationRejected;
            setFieldValidation(input, cambio ? 'El valor solo puede contener números positivos.' : '', feedback);
        });
    });

    // Códigos seriales: REVISAR clasificación si el proyecto incorpora otros formatos.
    document.querySelectorAll('input[name*="placa"], input[name*="serial"], input[name*="codigo_equipo"]').forEach(input => {
        input.setAttribute('pattern', '[A-Za-z0-9-]+');
        input.setAttribute('inputmode', 'text');
        const feedback = ensureValidationFeedback(input);
        input.addEventListener('input', () => {
            const antes = input.value;
            input.value = antes.replace(/[^A-Za-z0-9-]/g, '');
            const cambio = antes !== input.value;
            if (cambio) input.dataset.validationRejected = 'true';
            else delete input.dataset.validationRejected;
            setFieldValidation(input, cambio ? 'Use solo letras, números y guiones.' : '', feedback);
        });
    });

    // 3. MEDIDAS DE SALUD & VALIDADORES BIOMÉTRICOS (Estatura, Peso, Edad, Sueño, etc.)
    // 3.1 ESTATURA Y EDAD (Máximo 3 dígitos enteros, sin letras, sin negativos ni decimales)
    document.querySelectorAll('.input-estatura, .input-edad, input[name*="estatura"], input[name*="altura"], input[name*="edad"], #inputAltura, #inputEstatura, #id_estatura_cm, #inputEdad, #id_edad').forEach(input => {
        input.addEventListener('keydown', (e) => {
            // Permitir teclas de control (Backspace, Delete, Tab, Flechas, etc.)
            if (e.key === 'Backspace' || e.key === 'Delete' || e.key === 'Tab' || e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'Home' || e.key === 'End' || e.ctrlKey || e.metaKey) {
                return;
            }
            // Bloquear letras, signos y puntos/comas
            if (['e', 'E', '-', '+', '.', ','].includes(e.key) || !/^[0-9]$/.test(e.key)) {
                e.preventDefault();
                return;
            }
            // Bloquear si ya tiene 3 dígitos y no hay texto seleccionado
            const selLen = (input.selectionEnd || 0) - (input.selectionStart || 0);
            if (input.value.length >= 3 && selLen === 0) {
                e.preventDefault();
            }
        });

        const sanitizarEntero3 = (el) => {
            let val = String(el.value || '').replace(/[^0-9]/g, '');
            if (val.length > 3) val = val.slice(0, 3);
            
            // Límite específico para Estatura (máximo 230 cm)
            const isEstatura = el.classList.contains('input-estatura') || 
                               (el.id && (el.id.includes('Altura') || el.id.includes('Estatura'))) ||
                               (el.name && (el.name.includes('estatura') || el.name.includes('altura')));
            if (isEstatura && val !== '' && parseInt(val, 10) > 230) {
                val = '230';
            }

            // Límite específico para Edad (máximo 120 años)
            const isEdad = el.classList.contains('input-edad') || 
                           (el.id && el.id.includes('Edad')) ||
                           (el.name && el.name.includes('edad'));
            if (isEdad && val !== '' && parseInt(val, 10) > 120) {
                val = '120';
            }

            if (el.value !== val) el.value = val;
        };

        input.addEventListener('input', (e) => sanitizarEntero3(e.target));
        input.addEventListener('paste', (e) => {
            setTimeout(() => sanitizarEntero3(e.target), 10);
        });
    });

    // 3.2 PESO (Máximo 3 dígitos enteros, opcional 1 decimal, sin letras ni negativos, máximo 200 kg)
    document.querySelectorAll('.input-peso, input[name*="peso"], #inputPeso, #id_peso_kg').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' || e.key === 'Delete' || e.key === 'Tab' || e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'Home' || e.key === 'End' || e.ctrlKey || e.metaKey) {
                return;
            }
            // Bloquear signos y notación exponencial
            if (['e', 'E', '-', '+'].includes(e.key)) {
                e.preventDefault();
                return;
            }
            // Manejo de punto o coma decimal
            if (e.key === '.' || e.key === ',') {
                if (input.value.includes('.')) {
                    e.preventDefault();
                }
                return;
            }
            // Si no es un dígito [0-9], bloquear
            if (!/^[0-9]$/.test(e.key)) {
                e.preventDefault();
                return;
            }

            // Regla de longitud: max 3 dígitos enteros, max 1 decimal
            const selLen = (input.selectionEnd || 0) - (input.selectionStart || 0);
            if (selLen === 0) {
                const dotIdx = input.value.indexOf('.');
                const cursor = input.selectionStart || 0;
                if (dotIdx === -1) {
                    if (input.value.length >= 3) {
                        e.preventDefault();
                    }
                } else {
                    if (cursor <= dotIdx) {
                        const intPart = input.value.substring(0, dotIdx);
                        if (intPart.length >= 3) {
                            e.preventDefault();
                        }
                    } else {
                        const decPart = input.value.substring(dotIdx + 1);
                        if (decPart.length >= 1) {
                            e.preventDefault();
                        }
                    }
                }
            }
        });

        const sanitizarPeso = (el) => {
            let val = String(el.value || '').replace(',', '.').replace(/[^0-9.]/g, '');
            const partes = val.split('.');
            let intPart = partes[0] || '';
            if (intPart.length > 3) intPart = intPart.slice(0, 3);
            
            // Límite máximo para peso (200 kg)
            if (intPart !== '' && parseInt(intPart, 10) > 200) {
                intPart = '200';
                val = '200';
            } else if (partes.length > 1) {
                const decPart = partes.slice(1).join('').slice(0, 1);
                val = intPart + '.' + decPart;
            } else {
                val = intPart;
            }

            if (el.value !== val) el.value = val;
        };

        input.addEventListener('input', (e) => sanitizarPeso(e.target));
        input.addEventListener('paste', (e) => {
            setTimeout(() => sanitizarPeso(e.target), 10);
        });
    });

    // 3.3 OTRAS MEDIDAS DE SALUD (Sueño, Presión, Frecuencia)
    document.querySelectorAll('.input-decimal-salud, input[name*="sueno"]').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (['e', 'E', '-', '+'].includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('input', (e) => {
            let val = String(e.target.value || '').replace(/[^0-9.]/g, '');
            if (e.target.value !== val) e.target.value = val;
        });
    });

    // 5. FECHAS RESTRINGIDAS (Pasado bloqueado + Máximo 7 días a futuro para reservas/préstamos)
    document.querySelectorAll('.input-fecha-restringida, input[type="date"].input-reserva').forEach(input => {
        const hoy = new Date();
        const maxFecha = new Date();
        maxFecha.setDate(hoy.getDate() + 7);

        const formatDateStr = (dateObj) => {
            const year = dateObj.getFullYear();
            const month = String(dateObj.getMonth() + 1).padStart(2, '0');
            const day = String(dateObj.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };

        const minStr = formatDateStr(hoy);
        const maxStr = formatDateStr(maxFecha);

        input.setAttribute('min', minStr);
        input.setAttribute('max', maxStr);

        input.addEventListener('change', (e) => {
            if (e.target.value) {
                if (e.target.value < minStr || e.target.value > maxStr) {
                    e.target.classList.add('is-invalid');
                    e.target.value = minStr;
                } else {
                    e.target.classList.remove('is-invalid');
                }
            }
        });
    });

    // 6. PREVENCIÓN GLOBAL DE DOBLE CLIC EN ENVÍO DE FORMULARIOS ESTÁNDAR
    document.querySelectorAll('form:not(#loginForm):not(#registerForm):not(#formDesbloqueoUrgente)').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.checkValidity && !form.checkValidity()) {
                return; // Si el formulario HTML5 no es válido, no deshabilitar
            }
            const submitBtn = (e.submitter && form.contains(e.submitter))
                ? e.submitter
                : form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalContent = submitBtn.innerHTML;
                submitBtn.setAttribute('data-original-content', originalContent);
                setTimeout(() => {
                    if (e.defaultPrevented) return;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<i class="fas fa-circle-notch fa-spin me-2"></i> Procesando...`;
                }, 20);
            }
        });
    });

    // Validación visible para campos nativos y formularios que usan novalidate.
    document.querySelectorAll('form').forEach(form => {
        // Sustituye el aviso genérico del navegador por errores en español y conserva los valores.
        form.noValidate = true;
        form.addEventListener('input', (event) => {
            const field = event.target;
            if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement)) return;
            if (field.checkValidity()) setFieldValidation(field, '', ensureValidationFeedback(field));
        });
        form.addEventListener('submit', (event) => {
            const rejectedInput = form.querySelector('[data-validation-rejected="true"]');
            if (form.checkValidity() && !rejectedInput) return;
            event.preventDefault();
            const invalid = form.querySelector(':invalid') || rejectedInput;
            if (invalid) {
                const message = rejectedInput === invalid
                    ? (invalid.matches('.input-texto-limpio, [name="nombres"], [name="apellidos"], [name="first_name"], [name="last_name"], [name="capitan"], [name="ciudad"], [name="cargo"]')
                        ? 'El campo solo puede contener letras y espacios.'
                        : 'Este campo solo puede contener dígitos.')
                    : mensajeValidacionEspanol(invalid);
                setFieldValidation(invalid, message, ensureValidationFeedback(invalid));
                invalid.focus({preventScroll: false});
                if (window.Swal && typeof window.Swal.fire === 'function') {
                    window.Swal.fire({icon: 'error', title: 'Revisa el formulario', text: message, confirmButtonText: 'Entendido'});
                } else if (window.smaxDialog) {
                    window.smaxDialog.alert(message, {icon: 'danger', title: 'Revisa el formulario'});
                }
            }
        });
    });
}

function ensureValidationFeedback(field) {
    let feedback = field.parentElement && field.parentElement.querySelector(':scope > .invalid-feedback[data-live-validation]');
    if (!feedback && field.parentElement) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.dataset.liveValidation = 'true';
        field.insertAdjacentElement('afterend', feedback);
    }
    return feedback;
}

function setFieldValidation(field, message, feedback) {
    if (!field) return;
    field.classList.toggle('is-invalid', Boolean(message));
    field.setAttribute('aria-invalid', message ? 'true' : 'false');
    if (feedback) {
        feedback.textContent = message || '';
        feedback.style.display = message ? 'block' : '';
    }
}

function mensajeValidacionEspanol(field) {
    if (field.validity.valueMissing) return 'Este campo es obligatorio.';
    if (field.validity.typeMismatch && field.type === 'email') return 'Ingresa un correo electrónico con formato válido.';
    if (field.validity.patternMismatch) {
        if (/telefono|celular/i.test(field.name || '')) return 'El teléfono debe tener 10 dígitos y comenzar por 3.';
        if (/documento/i.test(field.name || '')) return 'El documento debe contener solo dígitos y tener la longitud indicada.';
        if (/nombre|apellido|capitan|first_name|last_name/i.test(field.name || '')) return 'El campo solo puede contener letras y espacios.';
        return 'El formato ingresado no es válido.';
    }
    if (field.validity.tooShort) return `Ingresa al menos ${field.minLength} caracteres.`;
    if (field.validity.tooLong) return `No ingreses más de ${field.maxLength} caracteres.`;
    if (field.validity.rangeUnderflow || field.validity.rangeOverflow) return 'El valor está fuera del rango permitido.';
    return 'Revisa este campo e intenta de nuevo.';
}

/**
 * Función global para restaurar botones de envío bloqueados en llamadas AJAX o errores.
 */
function resetSubmitButton(btnOrForm) {
    if (!btnOrForm) return;
    const btn = btnOrForm.tagName === 'FORM'
        ? btnOrForm.querySelector('button[type="submit"], input[type="submit"]')
        : btnOrForm;
    if (btn) {
        btn.disabled = false;
        const orig = btn.getAttribute('data-original-content');
        if (orig) {
            btn.innerHTML = orig;
        }
    }
}
window.resetSubmitButton = resetSubmitButton;

