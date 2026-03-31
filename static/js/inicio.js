document.addEventListener('DOMContentLoaded', function () {

    // ── Helpers de alerta ──
    function showAlert(el, msg, type = 'danger') {
        el.className = `alert alert-${type} mt-2`;
        el.innerHTML = msg;
        el.classList.remove('d-none');
    }
    function hideAlert(el) { if (el) el.classList.add('d-none'); }

    // ── Helper para obtener CSRF token ──
    function getCsrf() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    // ================================================================
    // ===== LOGIN / REGISTRO / INTER-FICHAS / INTER-CENTROS / GIMNASIO
    // (Se mantienen tal como en tu JS original; no los repito por brevedad)
    // ================================================================
    // ... (omitir: copia aquí todo tu código existente para login/registro/interfichas/intercentros/gimnasio)
    // Para mantenerlo simple, asumo que ya lo tienes arriba tal cual.
    // ================================================================

    // ================================================================
    // ===== PREVIEW IMAGEN ELEMENTO ==================================
    // ================================================================
    const inputImagenElemento = document.getElementById('inputImagenElemento');
    const previewImagenElemento = document.getElementById('previewImagenElemento');

    if (inputImagenElemento) {
        inputImagenElemento.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    if (previewImagenElemento) {
                        previewImagenElemento.src = e.target.result;
                        previewImagenElemento.style.display = 'block';
                    }
                }
                reader.readAsDataURL(file);
            } else if (previewImagenElemento) {
                previewImagenElemento.src = '#';
                previewImagenElemento.style.display = 'none';
            }
        });
    }

    // ================================================================
    // ===== Helper: construir URL de edición (usa template en HTML) ==
    // ================================================================
    function buildEditUrl(id) {
        // Busca tabla con template: data-edit-url-template="{% url 'editar_elemento' 0 %}"
        const tabla = document.getElementById('tablaElementos');
        if (tabla && tabla.dataset.editUrlTemplate) {
            // Reemplaza el '0' final por el id (manteniendo la posible barra)
            return tabla.dataset.editUrlTemplate.replace(/0\/?$/, id + '/');
        }
        // Si no hay template, busca en alguna fila (data-edit-url) o usa ruta por defecto
        return `/inventario/editar-elemento/${id}/`;
    }

    // ================================================================
    // ===== AJAX: obtener elemento y abrir modal con datos reales ====
    // ================================================================
    async function fetchElementoYMostrar(id, fallbackData = null) {
        if (!id) {
            if (fallbackData) abrirModalEditar(fallbackData);
            return;
        }
        const url = buildEditUrl(id);
        try {
            const res = await fetch(url, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!res.ok) {
                // fallback a datos locales si hay error
                console.warn('GET editar-elemento falló', res.status);
                if (fallbackData) abrirModalEditar(fallbackData);
                return;
            }
            const json = await res.json();
            if (json.success && json.elemento) {
                abrirModalEditar(json.elemento);
            } else {
                console.warn('Respuesta no contiene elemento, usando fallback.');
                if (fallbackData) abrirModalEditar(fallbackData);
            }
        } catch (err) {
            console.error('Error fetch elemento:', err);
            if (fallbackData) abrirModalEditar(fallbackData);
        }
    }

    // ================================================================
    // ===== Helpers para detalle/edición (tu código con ligeras mejoras)
    // ================================================================
    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function crearFilaDetalle(data) {
        const tr = document.createElement('tr');
        tr.className = 'fila-detalle bg-secondary';
        const td = document.createElement('td');
        td.colSpan = 7;
        td.innerHTML = `
            <div class="d-flex gap-3 align-items-start">
                <div style="min-width:150px;max-width:220px;">
                    <img src="${escapeHtml(data.imagen || '/static/images/placeholder.png')}" alt="${escapeHtml(data.tipo)}" style="width:100%; border-radius:6px; object-fit:cover;">
                </div>
                <div class="flex-grow-1 text-start">
                    <h6 class="mb-1">${escapeHtml(data.tipo)}</h6>
                    <p class="mb-1 text-white-50"><strong>Cantidad:</strong> ${escapeHtml(data.cantidad)} &nbsp; <strong>Estado:</strong> ${escapeHtml(data.estado)}</p>
                    <p class="mb-1 text-white-50"><strong>Docente:</strong> ${escapeHtml(data.docente)} &nbsp; <strong>Adquisición:</strong> ${escapeHtml(data.fecha)}</p>
                    <p class="mb-1 text-white-50"><strong>Descripción:</strong> ${escapeHtml(data.descripcion || 'Sin descripción')}</p>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-warning btn-editar-detalle me-2">Editar</button>
                        <a href="${escapeHtml(data.deleteUrl || '#')}" class="btn btn-sm btn-danger btn-eliminar-detalle">Eliminar</a>
                    </div>
                </div>
            </div>
        `;
        tr.appendChild(td);
        return tr;
    }

    function cerrarDetallesAbiertos(tbody) {
        tbody.querySelectorAll('tr.fila-detalle').forEach(r => r.remove());
    }

    function abrirModalEditar(data) {
        const modalEl = document.getElementById('modalElemento');
        if (!modalEl) {
            if (data.editUrl) window.location.href = data.editUrl;
            return;
        }

        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();

        const form = modalEl.querySelector('form');
        if (!form) return;

        // marcar acción editar
        const accionInput = form.querySelector('[name="accion"]');
        if (accionInput) accionInput.value = 'editar_elemento';

        // elemento id hidden
        let idInput = form.querySelector('#elementoIdInput');
        if (!idInput) {
            idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'elemento_id';
            idInput.id = 'elementoIdInput';
            form.appendChild(idInput);
        }
        idInput.value = data.id ?? '';

        const campoTipo = form.querySelector('[name="tipo_maquina"]');
        if (campoTipo) campoTipo.value = data.tipo ?? '';

        const campoCantidad = form.querySelector('[name="cantidad_total"]');
        if (campoCantidad) campoCantidad.value = data.cantidad ?? '';

        const campoEstado = form.querySelector('[name="estado_general"]');
        if (campoEstado) campoEstado.value = data.estado ?? 'Bueno';

        const campoFecha = form.querySelector('[name="fecha_adquisicion"]');
        if (campoFecha) campoFecha.value = data.fecha ?? '';

        const campoDocente = form.querySelector('[name="docente_responsable"]');
        if (campoDocente) campoDocente.value = data.docente ?? '';

        const campoDescripcion = form.querySelector('[name="descripcion"]');
        if (campoDescripcion) campoDescripcion.value = data.descripcion ?? '';

        // preview imagen
        if (previewImagenElemento) {
            if (data.imagen) {
                previewImagenElemento.src = data.imagen;
                previewImagenElemento.style.display = 'block';
            } else {
                previewImagenElemento.src = '#';
                previewImagenElemento.style.display = 'none';
            }
        }
    }

    // ================================================================
    // ===== Click sobre filas: abrir detalle y permitir editar =======
    // ================================================================
    const tablaElementosTbody = document.querySelector('table.table tbody');

    if (tablaElementosTbody) {
        tablaElementosTbody.querySelectorAll('tr').forEach(row => {
            // si fila mensaje (colspan) saltar
            if (row.querySelector('td[colspan]')) return;

            // evitar que clicks en botones/links internos activen la expansión
            row.querySelectorAll('a, button').forEach(btn => {
                btn.addEventListener('click', function (ev) {
                    ev.stopPropagation();
                });
            });

            // click sobre la fila -> toggle detalle (y fetch si hay id)
            row.addEventListener('click', function () {
                const tbody = row.parentElement;
                const next = row.nextElementSibling;
                if (next && next.classList.contains('fila-detalle')) {
                    next.remove();
                    return;
                }

                // cerrar otros detalles
                cerrarDetallesAbiertos(tbody);

                const id = row.dataset.id || row.getAttribute('data-id') || '';
                const fallbackData = {
                    id: id,
                    tipo: row.dataset.tipo || row.getAttribute('data-tipo') || row.children[1]?.innerText?.trim() || '',
                    cantidad: row.dataset.cantidad || row.getAttribute('data-cantidad') || row.children[2]?.innerText?.trim() || '',
                    estado: row.dataset.estado || row.getAttribute('data-estado') || '',
                    docente: row.dataset.docente || row.getAttribute('data-docente') || '',
                    fecha: row.dataset.fecha || row.getAttribute('data-fecha') || row.children[5]?.innerText?.trim() || '',
                    descripcion: row.dataset.descripcion || row.getAttribute('data-descripcion') || '',
                    imagen: row.dataset.imagen || row.getAttribute('data-imagen') || (row.querySelector('img')?.src || ''),
                    editUrl: row.dataset.editUrl || row.getAttribute('data-edit-url') || null,
                    deleteUrl: row.dataset.deleteUrl || row.getAttribute('data-delete-url') || (row.querySelector('a.btn-danger')?.href || '#')
                };

                // Si hay ID, intenta obtener datos frescos del servidor; si falla, usa fallback
                if (id) {
                    fetchElementoYMostrar(id, fallbackData).then(() => {
                        // después de abrir modal (si el usuario lo pidió), no añadimos detalle automático
                    });
                    // También mostramos el detalle local mientras se hace fetch (mejora UX)
                    const detalleLocal = crearFilaDetalle(fallbackData);
                    row.after(detalleLocal);

                    // Agregar listeners de ese detalle local (editar/eliminar)
                    const btnEditarLocal = detalleLocal.querySelector('.btn-editar-detalle');
                    if (btnEditarLocal) {
                        btnEditarLocal.addEventListener('click', function (ev) {
                            ev.stopPropagation();
                            // abrir modal con datos reales cuando exista id
                            fetchElementoYMostrar(id, fallbackData);
                        });
                    }
                    const btnEliminarLocal = detalleLocal.querySelector('.btn-eliminar-detalle');
                    if (btnEliminarLocal) {
                        btnEliminarLocal.addEventListener('click', function (ev) {
                            if (!confirm('¿Eliminar este elemento?')) ev.preventDefault();
                        });
                    }
                } else {
                    // No hay id -> usar datos locales
                    const detalle = crearFilaDetalle(fallbackData);
                    row.after(detalle);

                    const btnEditar = detalle.querySelector('.btn-editar-detalle');
                    if (btnEditar) {
                        btnEditar.addEventListener('click', function (ev) {
                            ev.stopPropagation();
                            abrirModalEditar(fallbackData);
                        });
                    }
                    const btnEliminar = detalle.querySelector('.btn-eliminar-detalle');
                    if (btnEliminar) {
                        btnEliminar.addEventListener('click', function (ev) {
                            if (!confirm('¿Eliminar este elemento?')) ev.preventDefault();
                        });
                    }
                }
            });
        });
    }

    // ================================================================
    // ===== Interceptar icono "Editar" en la tabla para abrir modal ==
    // (ahora intenta GET al servidor si hay id) ======================
    // ================================================================
    document.querySelectorAll('table.table tbody a.btn-warning').forEach(a => {
        a.addEventListener('click', function (ev) {
            ev.preventDefault();
            const row = this.closest('tr');
            if (!row) {
                window.location.href = this.href;
                return;
            }

            const id = row.dataset.id || row.getAttribute('data-id') || '';
            const fallbackData = {
                id: id,
                tipo: row.dataset.tipo || row.getAttribute('data-tipo') || row.children[1]?.innerText?.trim() || '',
                cantidad: row.dataset.cantidad || row.getAttribute('data-cantidad') || row.children[2]?.innerText?.trim() || '',
                estado: row.dataset.estado || row.getAttribute('data-estado') || '',
                docente: row.dataset.docente || row.getAttribute('data-docente') || '',
                fecha: row.dataset.fecha || row.getAttribute('data-fecha') || row.children[5]?.innerText?.trim() || '',
                descripcion: row.dataset.descripcion || row.getAttribute('data-descripcion') || '',
                imagen: row.dataset.imagen || row.getAttribute('data-imagen') || (row.querySelector('img')?.src || ''),
                editUrl: this.href
            };

            if (id) {
                fetchElementoYMostrar(id, fallbackData);
            } else {
                abrirModalEditar(fallbackData);
            }
        });
    });

    // ================================================================
    // ===== Interceptar submit del form del modal para POST AJAX =====
    // ================================================================
    (function initModalSubmit() {
        const modalEl = document.getElementById('modalElemento');
        if (!modalEl) return;
        const form = modalEl.querySelector('form') || document.getElementById('formElemento');
        if (!form) return;

        form.addEventListener('submit', async function (ev) {
            ev.preventDefault();

            const submitBtn = form.querySelector('button[type="submit"]') || form.querySelector('button.btn-primary');
            const originalHtml = submitBtn?.innerHTML;
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
                submitBtn.disabled = true;
            }

            // obtener id (si existe) para saber si es editar
            const id = form.querySelector('#elementoIdInput')?.value || '';

            // construir URL: si hay id, usamos editar; si no, dejamos que el form se envíe normalmente (crear)
            const url = id ? buildEditUrl(id) : form.action || window.location.href;

            try {
                const fd = new FormData(form);
                // incluir imagen si el input existe y tiene archivo
                const imagenInput = form.querySelector('#inputImagenElemento');
                if (imagenInput && imagenInput.files && imagenInput.files[0]) {
                    fd.set('imagen_elemento', imagenInput.files[0]);
                }

                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrf(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: fd
                });

                if (!res.ok) {
                    const text = await res.text();
                    console.error('Error respuesta POST:', res.status, text);
                    alert('Error al guardar. Revisa la consola.');
                    return;
                }

                const json = await res.json();
                if (json.success && json.elemento) {
                    const el = json.elemento;
                    // actualizar fila en la tabla si existe
                    const row = document.querySelector(`tr[data-id="${el.id}"]`);
                    if (row) {
                        // actualizar celdas visibles (ajusta índices si tu tabla diferente)
                        if (row.children[1]) row.children[1].innerText = el.tipo || '';
                        if (row.children[2]) row.children[2].innerText = el.cantidad ?? '';
                        // estado: poner badge
                        if (row.children[3]) {
                            const estadoCell = row.children[3];
                            if (el.estado === 'Bueno') estadoCell.innerHTML = `<span class="badge bg-success">${el.estado}</span>`;
                            else if (el.estado === 'Regular') estadoCell.innerHTML = `<span class="badge bg-warning text-dark">${el.estado}</span>`;
                            else estadoCell.innerHTML = `<span class="badge bg-danger">${el.estado}</span>`;
                        }
                        if (row.children[4]) row.children[4].innerText = el.docente || '';
                        if (row.children[5]) row.children[5].innerText = el.fecha || '';

                        // actualizar data-attributes
                        row.dataset.tipo = el.tipo || '';
                        row.dataset.cantidad = el.cantidad ?? '';
                        row.dataset.estado = el.estado || '';
                        row.dataset.docente = el.docente || '';
                        row.dataset.fecha = el.fecha || '';
                        row.dataset.descripcion = el.descripcion || '';
                        if (el.imagen) row.dataset.imagen = el.imagen;
                        else delete row.dataset.imagen;

                        // si la fila tiene una img visible, actualizar src si aplica
                        const imgInRow = row.querySelector('img');
                        if (imgInRow && el.imagen) imgInRow.src = el.imagen;
                    } else {
                        // Si no existe fila local, podrías añadirla dinámicamente o recargar la página
                        console.warn('Fila no encontrada para actualizar:', el.id);
                    }

                    // cerrar modal
                    const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                    modalInstance.hide();
                } else {
                    alert('Error al guardar: ' + (json.error || 'Revisa los datos.'));
                }
            } catch (err) {
                console.error('Error al enviar formulario modal:', err);
                alert('Error de conexión al guardar.');
            } finally {
                if (submitBtn) {
                    submitBtn.innerHTML = originalHtml;
                    submitBtn.disabled = false;
                }
            }
        });
    })();

    // ================================================================
    // ===== FIN ======================================================
    // ================================================================
});