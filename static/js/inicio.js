// inicio.js
document.addEventListener('DOMContentLoaded', function () {

    // === INICIALIZAR TOOLTIPS DE BOOTSTRAP ===
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ============================================================
    // 1. CONFIGURACIÓN, HELPERS Y REFERENCIAS
    // ============================================================
    const PLACEHOLDER_IMG = '/static/images/placeholder.png';

    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    const modalElemento = document.getElementById('modalElemento');
    const formElemento = document.getElementById('formElemento');
    const inputImagenElemento = document.getElementById('inputImagen');
    const previewImagenElemento = document.getElementById('previewImagen');
    const previewPlaceholder = document.getElementById('previewPlaceholder');

    // ============================================================
    // 2. SISTEMA DE SEGURIDAD (LOGIN, REGISTRO & VALIDACIÓN)
    // ============================================================

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('login') === '1') {
        const modalAuth = document.getElementById('modalForm');
        if (modalAuth) {
            var myModal = new bootstrap.Modal(modalAuth);
            myModal.show();
        }
    }

    function setupToggle(btnId, inputId) {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if (btn && input) {
            btn.addEventListener('click', function () {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-eye');
                    icon.classList.toggle('fa-eye-slash');
                }
            });
        }
    }

    setupToggle('togglePassword', 'id_password');
    setupToggle('togglePassword2', 'id_contrasena');
    setupToggle('togglePassword3', 'confirmarContrasena');

    // Medidor de fortaleza de contraseña
    const contrasenaInput = document.getElementById('id_contrasena');
    if (contrasenaInput) {
        contrasenaInput.addEventListener('input', function () {
            const strengthBar = document.getElementById('passwordStrengthBar');
            const strengthText = document.getElementById('passwordStrengthText');
            if (!strengthBar) return;

            const val = this.value;
            let score = 0;
            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;

            const levels = [
                { pct: '0%', color: '', label: '' },
                { pct: '25%', color: '#dc3545', label: '🔴 Muy débil' },
                { pct: '50%', color: '#fd7e14', label: '🟠 Débil' },
                { pct: '75%', color: '#ffc107', label: '🟡 Aceptable' },
                { pct: '100%', color: '#198754', label: '🟢 Fuerte' },
            ];
            const lvl = levels[score] || levels[0];
            strengthBar.style.width = lvl.pct;
            strengthBar.style.backgroundColor = lvl.color;
            strengthText.textContent = lvl.label;
        });
    }

    // LOGIN AJAX
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const loginAlert = document.getElementById('loginAlert');
            const formData = new FormData(this);

            if (loginAlert) {
                loginAlert.classList.remove('d-none');
                loginAlert.className = 'alert alert-info';
                loginAlert.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Verificando credenciales...';
            }

            fetch('/login/', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (loginAlert) {
                    loginAlert.className = `alert alert-${data.status === 'success' ? 'success' : 'danger'}`;
                    loginAlert.innerHTML = data.message;
                }
                if (data.status === 'success') {
                    setTimeout(() => { window.location.href = data.redirect || '/perfil/'; }, 1000);
                }
            })
            .catch(error => {
                console.error('Error en Login:', error);
                if (loginAlert) {
                    loginAlert.className = 'alert alert-danger';
                    loginAlert.innerHTML = 'Error de conexión con el servidor.';
                }
            });
        });
    }

    // REGISTRO AJAX CON VALIDACIÓN DE SEGURIDAD
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const form = e.target;
            const registerAlert = document.getElementById('registerAlert');

            if (!form.checkValidity()) {
                e.stopPropagation();
                form.classList.add('was-validated');
                if (registerAlert) {
                    registerAlert.classList.remove('d-none');
                    registerAlert.className = 'alert alert-danger mt-3';
                    registerAlert.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Por favor, completa todos los campos obligatorios (*).';
                }
                return;
            }

            const pass = document.getElementById('id_contrasena').value;
            const confPass = document.getElementById('confirmarContrasena').value;

            if (pass !== confPass) {
                if (registerAlert) {
                    registerAlert.classList.remove('d-none');
                    registerAlert.className = 'alert alert-warning mt-3';
                    registerAlert.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Las contraseñas no coinciden.';
                }
                return;
            }

            const formData = new FormData(this);
            if (registerAlert) {
                registerAlert.classList.remove('d-none');
                registerAlert.className = 'alert alert-info mt-3';
                registerAlert.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando registro...';
            }

            fetch('/registro/', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (registerAlert) {
                    registerAlert.className = `alert alert-${data.status === 'success' ? 'success' : 'danger'} mt-3`;
                    registerAlert.innerHTML = data.message;
                }
                if (data.status === 'success') {
                    setTimeout(() => { window.location.href = data.redirect || '/perfil/'; }, 1500);
                }
            })
            .catch(error => {
                console.error('Error en Registro:', error);
                if (registerAlert) {
                    registerAlert.className = 'alert alert-danger mt-3';
                    registerAlert.innerHTML = '<i class="fas fa-times-circle me-2"></i> Error en la conexión.';
                }
            });
        });
    }

    // ============================================================
    // 3. MÓDULO INVENTARIO & PRÉSTAMOS
    // ============================================================

    const inputDias = document.getElementById('inputDias');
    const infoFecha = document.getElementById('infoFecha') || document.getElementById('infoFechaPrestamo');
    const spanFecha = document.getElementById('spanFecha') || document.getElementById('textoFecha');
    const inputFechaHidden = document.getElementById('inputFechaHidden') || document.getElementById('inputFechaDev');

    if (inputDias) {
        inputDias.addEventListener('input', function () {
            const dias = parseInt(this.value);
            if (dias > 0) {
                let fechaActual = new Date();
                fechaActual.setDate(fechaActual.getDate() + dias);

                const opciones = { day: 'numeric', month: 'long', year: 'numeric' };
                if (spanFecha) spanFecha.innerText = fechaActual.toLocaleDateString('es-ES', opciones);

                const yyyy = fechaActual.getFullYear();
                let mm = fechaActual.getMonth() + 1;
                let dd = fechaActual.getDate();
                if (dd < 10) dd = '0' + dd;
                if (mm < 10) mm = '0' + mm;

                if (inputFechaHidden) inputFechaHidden.value = yyyy + '-' + mm + '-' + dd;
                if (infoFecha) infoFecha.style.display = 'block';
            } else {
                if (infoFecha) infoFecha.style.display = 'none';
            }
        });
    }

    if (inputImagenElemento) {
        inputImagenElemento.addEventListener('change', function () {
            const file = this.files[0];
            if (file && previewImagenElemento) {
                const reader = new FileReader();
                reader.onload = e => {
                    previewImagenElemento.src = e.target.result;
                    previewImagenElemento.style.display = 'block';
                    if (previewPlaceholder) previewPlaceholder.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // ============================================================
    // INVENTARIO — Expand row con botones de ícono pequeño
    // ============================================================
    // NOTA: La lógica de expand ya está en inventario.html (.expansion-row).
    // Este bloque NO crea filas dinámicas para no duplicar el panel.
    // Solo mejora los botones de acción dentro del panel expandido.

    function abrirModalEditar(data) {
        if (!modalElemento) return;
        if (formElemento) formElemento.reset();

        const tituloModal = document.getElementById('modalTitle');
        if (tituloModal) tituloModal.innerText = 'Editar Elemento Deportivo';

        const inputAccion = document.getElementById('inputAccion');
        const inputCodigo = document.getElementById('inputCodigo');

        if (inputAccion) inputAccion.value = 'editar_elemento';
        if (inputCodigo) inputCodigo.value = data.id;

        const campos = {
            'inputTipoMaquina':        data.tipo,
            'inputCantidadTotal':      data.cantidad,
            'inputEstadoGeneral':      data.estado,
            'inputDocenteResponsable': data.docente,
            'inputFechaAdquisicion':   data.fecha,
            'inputDescripcion':        data.descripcion
        };

        for (let id in campos) {
            const el = document.getElementById(id);
            if (el) el.value = campos[id];
        }

        if (previewImagenElemento) {
            if (data.imagen && data.imagen !== PLACEHOLDER_IMG) {
                previewImagenElemento.src = data.imagen;
                previewImagenElemento.style.display = 'block';
                if (previewPlaceholder) previewPlaceholder.style.display = 'none';
            } else {
                previewImagenElemento.style.display = 'none';
                if (previewPlaceholder) previewPlaceholder.style.display = 'block';
            }
        }

        bootstrap.Modal.getOrCreateInstance(modalElemento).show();
    }

    // Delegar clicks en el tbody de inventario
    const tablaElementos = document.getElementById('tablaElementos');
    if (tablaElementos) {
        const tbody = tablaElementos.querySelector('tbody');

        tbody.addEventListener('click', function (e) {
            // ── Botón EDITAR dentro del panel expansion-row ──
            const btnEditar = e.target.closest('.btn-editar-elemento');
            if (btnEditar) {
                e.preventDefault();
                // Subir hasta la expansion-row y luego a la main-row anterior
                const expansionRow = btnEditar.closest('tr.expansion-row');
                if (!expansionRow) return;
                const mainRow = expansionRow.previousElementSibling;
                if (!mainRow) return;

                abrirModalEditar({
                    id:          mainRow.dataset.id || '',
                    tipo:        mainRow.dataset.tipo || '',
                    cantidad:    mainRow.dataset.cantidad || '',
                    estado:      mainRow.dataset.estado || '',
                    docente:     mainRow.dataset.docente || '',
                    fecha:       mainRow.dataset.fecha || '',
                    descripcion: mainRow.dataset.descripcion || '',
                    imagen:      mainRow.dataset.imagen || PLACEHOLDER_IMG,
                });
                return;
            }

            // ── Botón EXPAND (toggle fila) — ya manejado en inventario.html,
            //    aquí NO hacemos nada para evitar duplicados ──
        });
    }

    // ============================================================
    // 4. OTROS (TABS, PANELES & EFECTOS)
    // ============================================================

    window.prestamoRapido = function (id) {
        const select = document.getElementById('selectElemento');
        if (select) {
            select.value = id;
            select.dispatchEvent(new Event('change'));
            const modalP = document.getElementById('modalPrestamo');
            if (modalP) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalP);
                modal.show();
            }
        }
    };

    window.mostrarSeccion = function (tipo) {
        const panel = document.getElementById('seccion-extra');
        const titulo = document.getElementById('titulo-seccion');
        const contenido = document.getElementById('contenido-seccion');

        if (panel) {
            panel.classList.remove('d-none');
            if (tipo === 'devoluciones') {
                titulo.innerHTML = '<i class="fas fa-undo text-success me-2"></i>DEVOLUCIONES PENDIENTES';
                contenido.innerHTML = '<p class="text-white-50 p-4">Cargando implementos pendientes por entregar...</p>';
            } else {
                titulo.innerHTML = '<i class="fas fa-exclamation-triangle text-danger me-2"></i>HISTORIAL DE SANCIONES';
                contenido.innerHTML = '<p class="text-white-50 p-4">Consultando historial de sanciones...</p>';
            }
            panel.scrollIntoView({ behavior: 'smooth' });
        }
    };

    window.cerrarSeccion = function () {
        const panel = document.getElementById('seccion-extra');
        if (panel) panel.classList.add('d-none');
    };

    document.querySelectorAll('.sport-card').forEach(card => {
        card.onmousemove = e => {
            const rect = card.getBoundingClientRect();
            card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
            card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
        };
    });

    function handleTabs(btnSelector, contentSelector) {
        document.querySelectorAll(btnSelector).forEach(btn => {
            btn.addEventListener('click', function () {
                const targetId = this.dataset.target;
                document.querySelectorAll(contentSelector).forEach(el => el.style.display = 'none');
                document.querySelectorAll(btnSelector).forEach(b => b.classList.remove('active'));
                const targetEl = document.getElementById(targetId);
                if (targetEl) targetEl.style.display = 'block';
                this.classList.add('active');
            });
        });
    }
    handleTabs('.inter-ficha-btn', '.inter-ficha-content');
    handleTabs('.inter-centro-btn', '.inter-centro-content');

    // ============================================================
    // 6. GESTIÓN DE REPORTE DE ERRORES (Delegación de Eventos)
    // ============================================================
    
    // Escuchador global para clics en botones de editar/borrar (Delegación)
    document.addEventListener('click', function(e) {
        // EDITAR
        const btnEdit = e.target.closest('.btn-editar-reporte');
        if (btnEdit) {
            e.preventDefault();
            const id = btnEdit.dataset.id;
            const comentario = btnEdit.dataset.comentario;
            
            const inputId = document.getElementById('inputEditId');
            const inputComentario = document.getElementById('inputEditComentario');
            
            if (inputId && inputComentario) {
                inputId.value = id;
                inputComentario.value = comentario;
                const modalEdit = new bootstrap.Modal(document.getElementById('modalEditarReporte'));
                modalEdit.show();
            }
            return;
        }

        // BORRAR
        const btnDelete = e.target.closest('.btn-borrar-reporte');
        if (btnDelete) {
            e.preventDefault(); // Prevenir la acción por defecto del botón
            const reporteId = btnDelete.dataset.id;
            const modalConfirmarEliminar = new bootstrap.Modal(document.getElementById('modalConfirmarEliminarReporte'));
            
            // Asignar el ID al input oculto del formulario de borrado
            document.getElementById('inputDeleteId').value = reporteId;

            // Mostrar el modal de confirmación
            modalConfirmarEliminar.show();

            // Manejar el clic en el botón de confirmación dentro del modal
            document.getElementById('confirmDeleteReporteBtn').onclick = function() {
                document.getElementById('formBorrarReporte').submit();
            };
        }
    });

    // Envío de nuevo reporte vía AJAX
    const formReportar = document.getElementById('reportarErrorForm');
    if (formReportar) {
        formReportar.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const reportAlert = document.getElementById('reportAlert');

            fetch(window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => {
                if (reportAlert) {
                    reportAlert.classList.remove('d-none');
                    reportAlert.style.display = 'block';
                    reportAlert.innerHTML = '<i class="fas fa-check-circle me-2"></i>Su reporte ha sido enviado con éxito.';
                    
                    // Scroll hacia arriba del modal para ver el mensaje
                    document.querySelector('#modalBuzonSugerencias .modal-body').scrollTop = 0;
                }
                this.reset();
                const fileNameSpan = document.getElementById('fileName');
                if (fileNameSpan) fileNameSpan.innerText = 'Seleccionar imagen desde su equipo...';
            })
            .catch(error => console.error('Error:', error));
        });
    }
});

// ============================================================
// 5. PREVISUALIZAR FOTO DE PERFIL
// ============================================================
window.previewProfileImage = function (event) {
    var reader = new FileReader();
    reader.onload = function () {
        var output = document.getElementById('imgPreviewPerfil');
        if (output) {
            output.src = reader.result;
            output.style.border = "2px solid var(--accent-hover)";
        }
    };
    if (event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
};