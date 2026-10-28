/**
 * Sports-Max — Suite Global de Validación y Restricciones en Tiempo Real (Frontend Vanilla JS)
 * Reglas de negocio:
 * 1. Restricción en Tiempo Real:
 *    - Bloqueo de teclas incorrectas:
 *      * Campos numéricos (documento, teléfono, ficha, cantidades): Bloqueo estricto de letras y símbolos.
 *      * Campos de texto puro (nombres, apellidos, capitán): Bloqueo estricto de números y símbolos.
 *    - Límite de caracteres: Impedir físicamente escribir más allá del límite establecido (maxlength).
 * 2. Específicos:
 *    - Número de Documento: 7 a 10 dígitos numéricos.
 *    - Teléfono / Celular: Exactamente 10 dígitos numéricos.
 *    - Inicio de sesión (Login): Máximo 10 caracteres.
 *    - Ficha SENA: Exactamente 7 dígitos numéricos.
 * 3. Feedback visual accesible y amigable por campo.
 */

document.addEventListener('DOMContentLoaded', () => {
    initSportsMaxValidators();
});

function initSportsMaxValidators() {
    // 1. HELPER PARA TECLAS DE CONTROL PERMITIDAS (Navegación, Borrado, Portapapeles)
    function isControlKey(e) {
        const allowedKeys = [
            'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
            'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
            'Home', 'End'
        ];
        if (allowedKeys.includes(e.key)) return true;
        // Permitir atajos Ctrl/Cmd (A, C, V, X, Z, R)
        if ((e.ctrlKey || e.metaKey) && ['a', 'c', 'v', 'x', 'z', 'r'].includes(e.key.toLowerCase())) {
            return true;
        }
        return false;
    }

    // 2. MOSTRAR MENSAJE DE RETROALIMENTACIÓN TEMPORAL POR CAMPO
    function showFieldNotice(input, message) {
        if (!input) return;
        let feedback = input.closest('.has-validation, .mb-3, .mb-4, .col-md-5, .col-md-6, .col-md-12, .form-group')?.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = input.parentElement.querySelector('.sportsmax-live-notice');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'sportsmax-live-notice small text-warning fw-semibold mt-1';
                input.parentElement.appendChild(feedback);
            }
        }
        input.classList.add('is-invalid');
        feedback.textContent = message;
        feedback.style.display = 'block';

        clearTimeout(input._noticeTimeout);
        input._noticeTimeout = setTimeout(() => {
            input.classList.remove('is-invalid');
            if (feedback.classList.contains('sportsmax-live-notice')) {
                feedback.style.display = 'none';
                feedback.textContent = '';
            }
        }, 2500);
    }

    // 3. CAMPOS NUMÉRICOS ESPECÍFICOS Y GENERALES
    function bindNumericInput(input, maxDigits, minDigits, specificMsg) {
        if (input.dataset.sportsmaxBoundNum) return;
        input.dataset.sportsmaxBoundNum = 'true';

        if (maxDigits) input.setAttribute('maxlength', maxDigits.toString());
        if (minDigits) input.setAttribute('minlength', minDigits.toString());

        input.addEventListener('keydown', (e) => {
            if (isControlKey(e)) return;

            // Bloquear letras y caracteres no numéricos
            if (!/^\d$/.test(e.key)) {
                e.preventDefault();
                showFieldNotice(input, specificMsg || 'Este campo solo permite números.');
                return;
            }

            // Límite de caracteres: Impedir físicamente escribir más allá del límite
            const max = maxDigits || parseInt(input.getAttribute('maxlength'), 10);
            if (max && input.value.length >= max && input.selectionStart === input.selectionEnd) {
                e.preventDefault();
                showFieldNotice(input, specificMsg || `Límite máximo de ${max} dígitos alcanzado.`);
            }
        });

        input.addEventListener('input', () => {
            // Limpieza al pegar o autocompletar
            let clean = input.value.replace(/\D/g, '');
            const max = maxDigits || parseInt(input.getAttribute('maxlength'), 10);
            if (max && clean.length > max) {
                clean = clean.slice(0, max);
            }
            if (input.value !== clean) {
                input.value = clean;
            }
        });
    }

    // Configurar Documentos (7 a 10 dígitos)
    const docInputs = document.querySelectorAll('input[name="numero_documento"], input[id*="numero_documento"], input[name="documento"]');
    docInputs.forEach(input => {
        bindNumericInput(input, 10, 7, 'El número de documento es obligatorio y debe tener entre 7 y 10 dígitos numéricos.');
    });

    // Configurar Teléfono / Celular (10 dígitos exactos)
    const telInputs = document.querySelectorAll('input[name="telefono"], input[name="celular"], input[type="tel"]');
    telInputs.forEach(input => {
        bindNumericInput(input, 10, 10, 'El teléfono debe contener exactamente 10 dígitos numéricos.');
    });

    // Configurar Ficha SENA (7 dígitos exactos)
    const fichaInputs = document.querySelectorAll('input[name="ficha"], input[id*="ficha"]');
    fichaInputs.forEach(input => {
        bindNumericInput(input, 7, 7, 'La ficha debe contener exactamente 7 dígitos numéricos.');
    });

    // Login: Identificador (Máximo 10 caracteres)
    const loginUsername = document.getElementById('login_username') || document.querySelector('#loginForm input[name="username"]');
    if (loginUsername) {
        loginUsername.setAttribute('maxlength', '10');
        loginUsername.addEventListener('keydown', (e) => {
            if (isControlKey(e)) return;
            if (loginUsername.value.length >= 10 && loginUsername.selectionStart === loginUsername.selectionEnd) {
                e.preventDefault();
                showFieldNotice(loginUsername, 'Las credenciales no pueden superar los 10 caracteres.');
            }
        });
        loginUsername.addEventListener('input', () => {
            if (loginUsername.value.length > 10) {
                loginUsername.value = loginUsername.value.slice(0, 10);
            }
        });
    }

    // Campos enteros genéricos
    document.querySelectorAll('.input-entero-estricto, .solo-numeros').forEach(input => {
        bindNumericInput(input, null, null, 'Este campo solo permite números enteros.');
    });

    // 4. CAMPOS DE TEXTO PURO (Nombres, Apellidos, Capitán, etc.)
    const pureTextInputs = document.querySelectorAll(
        'input[name="nombres"], input[name="apellidos"], input[name="first_name"], input[name="last_name"], input[name="capitan"], .solo-letras, .input-texto-puro'
    );
    pureTextInputs.forEach(input => {
        if (input.dataset.sportsmaxBoundText) return;
        input.dataset.sportsmaxBoundText = 'true';

        const max = parseInt(input.getAttribute('maxlength'), 10) || 100;
        input.setAttribute('maxlength', max.toString());

        input.addEventListener('keydown', (e) => {
            if (isControlKey(e)) return;

            // Bloquear números y símbolos
            if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]$/.test(e.key)) {
                e.preventDefault();
                showFieldNotice(input, `Este campo solo permite letras y un máximo de ${max} caracteres.`);
                return;
            }

            // Límite de caracteres
            if (input.value.length >= max && input.selectionStart === input.selectionEnd) {
                e.preventDefault();
                showFieldNotice(input, `Este campo solo permite letras y un máximo de ${max} caracteres.`);
            }
        });

        input.addEventListener('input', () => {
            let clean = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]/g, '');
            if (clean.length > max) {
                clean = clean.slice(0, max);
            }
            if (input.value !== clean) {
                input.value = clean;
            }
        });

        input.addEventListener('blur', () => {
            if (input.value) {
                input.value = input.value
                    .toLowerCase()
                    .split(' ')
                    .filter(w => w.length > 0)
                    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ');
            }
        });
    });

    // 5. MEDIDAS DE SALUD & DECIMALES (Peso, Estatura, IMC, etc.)
    document.querySelectorAll('.input-decimal-salud, input[name*="peso"], input[name*="estatura"], input[name*="sueno"]').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (['e', 'E', '-', '+'].includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('change', (e) => {
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {
                if (val <= 0) {
                    e.target.classList.add('is-invalid');
                } else {
                    e.target.value = val.toFixed(2);
                    e.target.classList.remove('is-invalid');
                }
            }
        });
    });

    // 6. FECHAS RESTRINGIDAS
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
    });

    // 7. PREVENCIÓN GLOBAL DE DOBLE ENVÍO
    document.querySelectorAll('form:not(#loginForm):not(#registerForm):not(#formDesbloqueoUrgente)').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.checkValidity && !form.checkValidity()) {
                return;
            }
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
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
}

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
