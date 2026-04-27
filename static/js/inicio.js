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
    const tablaElementos = document.getElementById('tablaElementos');

    // ============================================================
    // 2. SISTEMA DE SEGURIDAD (LOGIN, REGISTRO & VALIDACIÓN)
    // ============================================================

    // Detección automática de modal de login por URL (?login=1)
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

            // --- NUEVA SEGURIDAD: VALIDACIÓN DE CAMPOS REQUERIDOS ---
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
        inputDias.addEventListener('input', function() {
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

    function extraerDataDeFila(row) {
        return {
            id: row.dataset.id || '',
            tipo: row.dataset.tipo || '',
            cantidad: row.dataset.cantidad || '',
            estado: row.dataset.estado || '',
            docente: row.dataset.docente || '',
            fecha: row.dataset.fecha || '',
            descripcion: row.dataset.descripcion || '',
            imagen: row.dataset.imagen || PLACEHOLDER_IMG,
            deleteUrl: row.dataset.deleteUrl || '#'
        };
    }

    function abrirModalEditar(data) {
        if (!modalElemento) return;
        if (formElemento) formElemento.reset();

        const tituloModal = document.getElementById('modalTitle');
        if (tituloModal) tituloModal.innerText = 'Editar Elemento Deportivo';

        const inputAccion = document.getElementById('inputAccion') || formElemento.querySelector('[name="accion"]');
        const inputCodigo = document.getElementById('inputCodigo') || document.getElementById('elementoIdInput');
        
        if (inputAccion) inputAccion.value = 'editar_elemento';
        if (inputCodigo) inputCodigo.value = data.id;

        const campos = {
            'inputTipo': data.tipo,
            'inputTipoMaquina': data.tipo,
            'inputCantidad': data.cantidad,
            'inputCantidadTotal': data.cantidad,
            'inputEstado': data.estado,
            'inputEstadoGeneral': data.estado,
            'inputDocente': data.docente,
            'inputDocenteResponsable': data.docente,
            'inputFecha': data.fecha,
            'inputFechaAdquisicion': data.fecha,
            'inputDescripcion': data.descripcion
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

    if (tablaElementos) {
        const tbody = tablaElementos.querySelector('tbody');
        tbody.addEventListener('click', function (e) {
            const target = e.target;
            const row = target.closest('tr');
            if (!row || row.classList.contains('fila-detalle')) return;

            if (target.closest('.btn-editar-elemento') || target.closest('.btn-abrir-editar')) {
                e.preventDefault();
                abrirModalEditar(extraerDataDeFila(row));
                return;
            }

            if (target.closest('.btn-expand')) {
                e.preventDefault();
                const next = row.nextElementSibling;
                if (next && next.classList.contains('fila-detalle')) {
                    next.remove();
                } else {
                    tbody.querySelectorAll('.fila-detalle').forEach(r => r.remove());
                    
                    const data = extraerDataDeFila(row);
                    const numCols = tablaElementos.querySelectorAll('thead th').length || 8;
                    const imgUrl = (data.imagen && data.imagen.trim() !== '') ? data.imagen : PLACEHOLDER_IMG;
                    
                    const detalleHtml = `
                        <tr class="fila-detalle">
                            <td colspan="${numCols}">
                                <div class="d-flex gap-3 align-items-start p-3 m-2" style="background: rgba(0, 210, 255, 0.05); border-radius: 12px; border-left: 4px solid var(--accent-blue);">
                                    <div style="width: 120px; height: 120px; flex-shrink: 0; background: rgba(0,0,0,0.5); border-radius: 8px; border: 1px solid var(--accent-blue); overflow: hidden; display: flex; align-items: center; justify-content: center;">
                                        <img src="${escapeHtml(imgUrl)}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                        <i class="fas fa-image fa-3x text-muted" style="display: none;"></i>
                                    </div>
                                    <div class="text-start flex-grow-1">
                                        <h6 class="fw-bold text-uppercase" style="color: var(--accent-blue); font-size: 1.1rem; margin-bottom: 8px;">${escapeHtml(data.tipo)}</h6>
                                        <p class="small text-white-50 mb-3"><strong>Descripción:</strong> ${escapeHtml(data.descripcion || 'Sin descripción disponible')}</p>
                                        <button class="btn btn-sm btn-warning mt-2 btn-editar-sub">
                                            <i class="fas fa-edit me-1"></i> Editar Elemento
                                        </button>
                                    </div>
                                </div>
                            </td>
                        </tr>`;
                        
                    row.insertAdjacentHTML('afterend', detalleHtml);
                    row.nextElementSibling.querySelector('.btn-editar-sub').onclick = () => abrirModalEditar(data);
                }
            }
        });
    }

    // ============================================================
    // 4. OTROS (TABS, PANELES & EFECTOS)
    // ============================================================

    window.prestamoRapido = function(id) {
        const select = document.getElementById('selectElemento');
        if (select) {
            select.value = id;
            const modalP = document.getElementById('modalPrestamo');
            if (modalP) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalP);
                modal.show();
            }
        }
    };

    window.mostrarSeccion = function(tipo) {
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

    window.cerrarSeccion = function() {
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
});

// ============================================================
// 5. PREVISUALIZAR FOTO DE PERFIL
// ============================================================
window.previewProfileImage = function(event) {
    var reader = new FileReader();
    reader.onload = function(){
        var output = document.getElementById('imgPreviewPerfil');
        if (output) {
            output.src = reader.result;
            output.style.border = "2px solid var(--accent-hover)"; 
        }
    };
    if(event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
};
