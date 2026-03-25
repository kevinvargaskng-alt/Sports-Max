document.addEventListener('DOMContentLoaded', function () {

    // ── Helpers de alerta ──
    function showAlert(el, msg, type = 'danger') {
        el.className = `alert alert-${type} mt-2`;
        el.innerHTML = msg;
        el.classList.remove('d-none');
    }
    function hideAlert(el) { el.classList.add('d-none'); }

    // ── Helper para obtener CSRF token ──
    function getCsrf() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    // ================================================================
    // ===== LOGIN (conectado a Django) ================================
    // ================================================================
    const loginForm  = document.getElementById('loginForm');
    const loginAlert = document.getElementById('loginAlert');

    if (loginForm && loginAlert) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            hideAlert(loginAlert);

            const doc      = document.getElementById('loginDoc')?.value.trim();
            const password = document.getElementById('loginPassword')?.value;
            const btn      = this.querySelector('button[type="submit"]');

            if (!doc || !password) {
                showAlert(loginAlert, '<i class="fas fa-exclamation-triangle me-1"></i> Por favor completa todos los campos.', 'warning');
                return;
            }

            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cargando...';
            btn.disabled  = true;

            try {
                const res = await fetch('/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCsrf()
                    },
                    body: new URLSearchParams({ username: doc, password })
                });

                const data = await res.json();

                if (data.success) {
                    showAlert(loginAlert, '<i class="fas fa-check-circle me-1"></i> ¡Bienvenido! Redirigiendo...', 'success');
                    setTimeout(() => window.location.href = data.redirect || '/perfil/', 800);
                } else {
                    showAlert(loginAlert,
                        '<i class="fas fa-exclamation-triangle me-1"></i> ' + (data.error || 'Credenciales incorrectas') +
                        '. ¿Deseas <a href="#" id="goToRegister" class="alert-link fw-bold">registrarte</a>?',
                        'warning'
                    );
                    setTimeout(() => {
                        document.getElementById('goToRegister')?.addEventListener('click', function (ev) {
                            ev.preventDefault();
                            document.getElementById('register-tab')?.click();
                        });
                    }, 50);
                }
            } catch (err) {
                showAlert(loginAlert, '<i class="fas fa-times-circle me-1"></i> Error de conexión. Intenta de nuevo.', 'danger');
            } finally {
                btn.innerHTML = '<i class="fas fa-sign-in-alt me-1"></i> Ingresar al Sistema';
                btn.disabled  = false;
            }
        });
    }

    // ================================================================
    // ===== REGISTRO (conectado a Django) ============================
    // ================================================================
    const camposComunes  = document.getElementById('camposComunes');
    const campoTipoDoc   = document.getElementById('campoTipoDoc');
    const campoEstado    = document.getElementById('campoEstado');
    const tipoDocumento  = document.getElementById('tipoDocumento');
    const estadoAprendiz = document.getElementById('estadoAprendiz');
    const registerAlert  = document.getElementById('registerAlert');
    const registerForm   = document.getElementById('registerForm');

    // Mostrar campos al cargar (siempre aprendiz)
    camposComunes?.classList.remove('d-none');
    campoTipoDoc?.style.setProperty('display', 'block', 'important');
    campoEstado?.style.setProperty('display', 'block', 'important');
    if (tipoDocumento)  tipoDocumento.required  = true;
    if (estadoAprendiz) estadoAprendiz.required = true;

    if (registerForm && registerAlert) {
        registerForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            hideAlert(registerAlert);

            const contrasena = this.querySelector('[name=contrasena]')?.value;
            const confirmar  = document.getElementById('confirmarContrasena')?.value;
            const btn        = this.querySelector('button[type="submit"]');

            if (contrasena !== confirmar) {
                showAlert(registerAlert, '<i class="fas fa-times-circle me-1"></i> Las contraseñas no coinciden.', 'danger');
                return;
            }
            if (!this.checkValidity()) {
                this.reportValidity();
                return;
            }

            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Registrando...';
            btn.disabled  = true;

            try {
                const formData = new FormData(this);
                // Aseguramos que contrasena va con el nombre correcto
                formData.set('contrasena', contrasena);

                const res = await fetch('/registro/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrf() },
                    body: formData
                });

                const data = await res.json();

                if (data.success) {
                    showAlert(registerAlert,
                        '<i class="fas fa-check-circle me-1"></i> ¡Registro exitoso! Redirigiendo a tu perfil...',
                        'success'
                    );
                    setTimeout(() => window.location.href = data.redirect || '/perfil/', 800);
                } else {
                    const errorMsg = data.error || JSON.stringify(data.errors) || 'Error al registrarse.';
                    showAlert(registerAlert,
                        '<i class="fas fa-times-circle me-1"></i> ' + errorMsg,
                        'danger'
                    );
                }
            } catch (err) {
                showAlert(registerAlert, '<i class="fas fa-times-circle me-1"></i> Error de conexión. Intenta de nuevo.', 'danger');
            } finally {
                btn.innerHTML = '<i class="fas fa-user-plus me-1"></i> Crear Cuenta';
                btn.disabled  = false;
            }
        });
    }

    // ================================================================
    // ===== INTER-FICHAS =============================================
    // ================================================================
    const botonesAccion  = document.querySelectorAll('.btn-accion');
    const panel          = document.getElementById('panel-interfichas');
    const panelContenido = document.getElementById('panel-contenido');

    const contenidos = {
        torneos: `
            <h5 class="fw-bold"><i class="fas fa-list-alt me-2"></i>Lista de Torneos</h5>
            <p>Aquí se cargarán los torneos desde la base de datos.</p>`,
        inscribir: null,
        resultados: `
            <h5 class="fw-bold"><i class="fas fa-chart-bar me-2"></i>Resultados</h5>
            <p>Tabla de posiciones y marcadores en tiempo real.</p>`
    };

    if (botonesAccion.length) {
        botonesAccion.forEach(btn => {
            btn.addEventListener('click', function () {
                const seccion = this.dataset.seccion;
                if (seccion === 'inscribir') {
                    new bootstrap.Modal(document.getElementById('modalInscripcion')).show();
                    return;
                }
                panel?.classList.remove('d-none');
                if (panelContenido) panelContenido.innerHTML = contenidos[seccion] || '';
            });
        });

        const formInscripcion = document.getElementById('formInscripcion');
        if (formInscripcion) {
            formInscripcion.addEventListener('submit', function (e) {
                e.preventDefault();
                const btn = this.querySelector('button[type="submit"]');
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Registrando...';
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('modalInscripcion')).hide();
                    btn.innerHTML = '<i class="fas fa-check me-2"></i>Confirmar Inscripción';
                    alert('¡Equipo inscrito correctamente!');
                }, 1200);
            });
        }
    }

    // ================================================================
    // ===== INTER-CENTROS ============================================
    // ================================================================
    const botonesAccionCentro  = document.querySelectorAll('.btn-accion-centro');
    const panelCentro          = document.getElementById('panel-intercentros');
    const panelContenidoCentro = document.getElementById('panel-contenido-centro');

    const contenidosCentro = {
        torneos: `
            <h5 class="fw-bold"><i class="fas fa-list-alt me-2"></i>Lista de Torneos Inter-Centros</h5>
            <p>Aquí se cargarán los torneos desde la base de datos.</p>`,
        resultados: `
            <h5 class="fw-bold"><i class="fas fa-chart-bar me-2"></i>Resultados Inter-Centros</h5>
            <p>Tabla de posiciones y marcadores en tiempo real.</p>`
    };

    if (botonesAccionCentro.length) {
        botonesAccionCentro.forEach(btn => {
            btn.addEventListener('click', function () {
                const seccion = this.dataset.seccion;
                panelCentro?.classList.remove('d-none');
                if (panelContenidoCentro) panelContenidoCentro.innerHTML = contenidosCentro[seccion] || '';
            });
        });
    }

    // ================================================================
    // ===== GIMNASIO =================================================
    // ================================================================
    const botonesGimnasio        = document.querySelectorAll('.btn-accion-gimnasio');
    const panelGimnasio          = document.getElementById('panel-gimnasio');
    const panelContenidoGimnasio = document.getElementById('panel-contenido-gimnasio');

    const contenidosGimnasio = {
        'mis-reservas': `
            <h5 class="fw-bold"><i class="fas fa-clipboard-list me-2"></i>Mis Reservas Activas</h5>
            <p>Aquí se cargarán tus reservas activas desde la base de datos.</p>`
    };

    if (botonesGimnasio.length) {
        botonesGimnasio.forEach(btn => {
            btn.addEventListener('click', function () {
                const seccion = this.dataset.seccion;
                panelGimnasio?.classList.remove('d-none');
                if (panelContenidoGimnasio) panelContenidoGimnasio.innerHTML = contenidosGimnasio[seccion] || '';
            });
        });
    }

    // ================================================================
    // ===== INVENTARIO ===============================================
    // ================================================================
    const botonesInventario        = document.querySelectorAll('.btn-accion-inv');
    const panelInventario          = document.getElementById('panel-inventario');
    const panelContenidoInventario = document.getElementById('panel-contenido-inventario');

    const contenidosInventario = {
        devoluciones: `
            <h5 class="fw-bold"><i class="fas fa-undo me-2"></i>Devoluciones Pendientes</h5>
            <p>Aquí se cargarán las devoluciones pendientes desde la base de datos.</p>`,
        sanciones: `
            <h5 class="fw-bold"><i class="fas fa-exclamation-triangle me-2"></i>Sanciones Activas</h5>
            <p>Aquí se cargarán las sanciones activas desde la base de datos.</p>`
    };

    if (botonesInventario.length) {
        botonesInventario.forEach(btn => {
            btn.addEventListener('click', function () {
                const seccion = this.dataset.seccion;
                panelInventario?.classList.remove('d-none');
                if (panelContenidoInventario) panelContenidoInventario.innerHTML = contenidosInventario[seccion] || '';
            });
        });
    }

}); // ── fin DOMContentLoaded ──