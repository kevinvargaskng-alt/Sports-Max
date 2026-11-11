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
    const REGEX_CARACTERES_PROHIBIDOS = /[@#$%&*=\/\\<>!¡?¿^{}\[\]~|]/g;

    // 1. TEXTO LIMPIO & TITLE CASE (Nombres, Apellidos, Campos de texto general)
    document.querySelectorAll('.input-texto-limpio, input[name*="nombre"], input[name*="apellido"], input[name*="capitan"]').forEach(input => {
        input.addEventListener('input', (e) => {
            if (REGEX_CARACTERES_PROHIBIDOS.test(e.target.value)) {
                e.target.value = e.target.value.replace(REGEX_CARACTERES_PROHIBIDOS, '');
                e.target.classList.add('is-invalid');
                e.target.setAttribute('aria-invalid', 'true');
            } else {
                e.target.classList.remove('is-invalid');
                e.target.setAttribute('aria-invalid', 'false');
            }
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
        input.addEventListener('keydown', (e) => {
            const teclasProhibidas = ['e', 'E', '-', '+', '.', ','];
            if (teclasProhibidas.includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
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

