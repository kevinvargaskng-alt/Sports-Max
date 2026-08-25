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

    // 3. MEDIDAS DE SALUD & DECIMALES (Peso, Estatura, IMC)
    document.querySelectorAll('.input-decimal-salud, input[name*="peso"], input[name*="estatura"]').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (['e', 'E', '-', '+'].includes(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('change', (e) => {
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {
                e.target.value = val.toFixed(2);
            }
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

    // 6. PREVENCIÓN GLOBAL DE DOBLE CLIC EN ENVÍO DE FORMULARIOS (QA & UX)
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.checkValidity && !form.checkValidity()) {
                return; // Si el formulario HTML5 no es válido, no deshabilitar aún
            }
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                setTimeout(() => {
                    submitBtn.disabled = true;
                    const originalContent = submitBtn.innerHTML;
                    submitBtn.setAttribute('data-original-content', originalContent);
                    submitBtn.innerHTML = `<i class="fas fa-circle-notch fa-spin me-2"></i> Procesando...`;
                }, 10);
            }
        });
    });
}
