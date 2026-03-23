document.addEventListener('DOMContentLoaded', function () {

    // ================================================================
    // ===== STORE TEMPORAL DE USUARIOS (reemplazar con AJAX/Django) ===
    // ================================================================
    const registeredUsers = [];

    // ── Helpers de alerta ──
    function showAlert(el, msg, type = 'danger') {
        el.className = `alert alert-${type} mt-2`;
        el.innerHTML = msg;
        el.classList.remove('d-none');
    }
    function hideAlert(el) { el.classList.add('d-none'); }

    // ================================================================
    // ===== LOGIN ====================================================
    // ================================================================
    const loginForm  = document.getElementById('loginForm');
    const loginAlert = document.getElementById('loginAlert');

    if (loginForm && loginAlert) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            hideAlert(loginAlert);

            const doc      = document.getElementById('loginDoc')?.value.trim();
            const password = document.getElementById('loginPassword')?.value;
            const btn      = this.querySelector('button[type="submit"]');

            if (!doc || !password) {
                showAlert(loginAlert, '<i class="fas fa-exclamation-triangle me-1"></i> Por favor completa todos los campos.', 'warning');
                return;
            }

            // Animación de carga
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cargando...';
            btn.disabled  = true;

            setTimeout(() => {
                const user = registeredUsers.find(u => u.numero_documento === doc && u.contrasena === password);

                if (user) {
                    // ✅ Login exitoso
                    showAlert(loginAlert, `<i class="fas fa-check-circle me-1"></i> ¡Bienvenido, ${user.nombres}!`, 'success');
                    btn.innerHTML = '<i class="fas fa-sign-in-alt me-1"></i> Ingresar al Sistema';
                    btn.disabled  = false;
                    // window.location.href = '/dashboard/';  // ← descomentar en producción
                } else {
                    // ❌ No encontrado → sugerir registro
                    showAlert(loginAlert,
                        '<i class="fas fa-exclamation-triangle me-1"></i> Usuario no encontrado. ' +
                        '¿Deseas <a href="#" id="goToRegister" class="alert-link fw-bold">registrarte</a>?',
                        'warning'
                    );
                    btn.innerHTML = '<i class="fas fa-sign-in-alt me-1"></i> Ingresar al Sistema';
                    btn.disabled  = false;

                    setTimeout(() => {
                        const link = document.getElementById('goToRegister');
                        if (link) {
                            link.addEventListener('click', function (ev) {
                                ev.preventDefault();
                                document.getElementById('register-tab')?.click();
                            });
                        }
                    }, 50);
                }
            }, 1000);
        });
    }

    // ================================================================
    // ===== REGISTRO =================================================
    // ================================================================
    const rolSelect     = document.getElementById('rolSelect');
    const camposComunes = document.getElementById('camposComunes');
    const campoTipoDoc  = document.getElementById('campoTipoDoc');
    const campoEstado   = document.getElementById('campoEstado');
    const tipoDocumento = document.getElementById('tipoDocumento');
    const estadoAprendiz= document.getElementById('estadoAprendiz');
    const registerAlert = document.getElementById('registerAlert');
    const registerForm  = document.getElementById('registerForm');

    // Mostrar/ocultar campos según rol
    if (rolSelect) {
        rolSelect.addEventListener('change', function () {
            const rol = this.value;
            if (!rol) {
                camposComunes?.classList.add('d-none');
                return;
            }
            camposComunes?.classList.remove('d-none');

            if (rol === 'aprendiz') {
                campoTipoDoc?.style.setProperty('display', 'block', 'important');
                campoEstado?.style.setProperty('display', 'block', 'important');
                if (tipoDocumento)  tipoDocumento.required  = true;
                if (estadoAprendiz) estadoAprendiz.required = true;
            } else {
                campoTipoDoc?.style.setProperty('display', 'none', 'important');
                campoEstado?.style.setProperty('display', 'none', 'important');
                if (tipoDocumento)  tipoDocumento.required  = false;
                if (estadoAprendiz) estadoAprendiz.required = false;
            }
        });
    }

    // Submit registro
    if (registerForm && registerAlert) {
        registerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            hideAlert(registerAlert);

            const rol        = rolSelect?.value;
            const contrasena = this.contrasena?.value;
            const confirmar  = document.getElementById('confirmarContrasena')?.value;
            const btn        = this.querySelector('button[type="submit"]');

            if (!rol) {
                showAlert(registerAlert, 'Selecciona un rol para continuar.', 'warning');
                return;
            }
            if (contrasena !== confirmar) {
                showAlert(registerAlert, 'Las contraseñas no coinciden.', 'danger');
                return;
            }
            if (!this.checkValidity()) {
                this.reportValidity();
                return;
            }

            // Animación
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Registrando...';
            btn.disabled  = true;

            setTimeout(() => {
                const nuevoUsuario = {
                    numero_documento: this.numero_documento?.value.trim(),
                    nombres:          this.nombres?.value.trim(),
                    apellidos:        this.apellidos?.value.trim(),
                    telefono:         this.telefono?.value.trim(),
                    genero:           this.genero?.value,
                    rol,
                    contrasena,
                };
                if (rol === 'aprendiz') {
                    nuevoUsuario.tipo_documento = tipoDocumento?.value;
                    nuevoUsuario.estado         = estadoAprendiz?.value;
                }

                const existe = registeredUsers.find(u => u.numero_documento === nuevoUsuario.numero_documento);
                if (existe) {
                    showAlert(registerAlert, 'Ya existe un usuario con ese número de documento.', 'warning');
                    btn.innerHTML = '<i class="fas fa-user-plus me-1"></i> Crear Cuenta';
                    btn.disabled  = false;
                    return;
                }

                registeredUsers.push(nuevoUsuario);
                showAlert(registerAlert,
                    `<i class="fas fa-check-circle me-1"></i> ¡Registro exitoso! Ahora puedes ` +
                    `<a href="#" id="goToLogin" class="alert-link fw-bold">iniciar sesión</a>.`,
                    'success'
                );
                registerForm.reset();
                camposComunes?.classList.add('d-none');
                btn.innerHTML = '<i class="fas fa-user-plus me-1"></i> Crear Cuenta';
                btn.disabled  = false;

                setTimeout(() => {
                    document.getElementById('goToLogin')?.addEventListener('click', function (ev) {
                        ev.preventDefault();
                        document.getElementById('login-tab')?.click();
                    });
                }, 50);
            }, 1000);
        });
    }

    // ================================================================
    // ===== INTER-FICHAS =============================================
    // ================================================================
    const botonesAccion = document.querySelectorAll('.btn-accion');
    const panel         = document.getElementById('panel-interfichas');
    const panelContenido= document.getElementById('panel-contenido');

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
    const botonesAccionCentro   = document.querySelectorAll('.btn-accion-centro');
    const panelCentro           = document.getElementById('panel-intercentros');
    const panelContenidoCentro  = document.getElementById('panel-contenido-centro');

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