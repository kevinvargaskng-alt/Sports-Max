/**
 * Generador de Imágenes IA para Tux (Exclusivo Administrador)
 * Sistema de Gestión Deportiva - SENA Centro Minero
 */

let currentAspect = '1:1';
let currentStyle = 'fotorealista';

function buildGeneratedImageCardHtml(imgData) {
    const url = imgData.url;
    const prompt = imgData.prompt || '';
    const estilo = imgData.estilo || 'Fotorealista';
    const aspecto = imgData.aspecto || '1:1';
    const filename = imgData.filename || 'imagen_tux_ia.jpg';

    return `
    <div class="gen-img-card">
      <div class="gen-img-wrapper" onclick="openLightbox('${url}', '${filename}')" title="Clic para ampliar en pantalla completa">
        <img src="${url}" class="gen-img-tag" alt="${prompt}" loading="lazy"/>
      </div>
      <div class="gen-img-meta">
        <div class="gen-badges-row">
          <span class="gen-badge brand">📐 ${aspecto}</span>
          <span class="gen-badge purple">🎨 ${estilo}</span>
        </div>
        <div style="font-size:11px; color:var(--muted); font-style:italic; line-height:1.35; margin-top:2px;">
          "${prompt}"
        </div>
        <div class="gen-actions-row">
          <a href="${url}" download="${filename}" class="gen-act-btn primary" title="Descargar imagen en alta calidad">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Descargar
          </a>
          <button type="button" class="gen-act-btn" onclick="openLightbox('${url}', '${filename}')" title="Ver en tamaño completo">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
            Ampliar
          </button>
        </div>
      </div>
    </div>`;
}

function openImageGenPanel() {
    const panel = document.getElementById('imageGenPanel');
    if (panel) {
        panel.classList.add('open');
        const pInput = document.getElementById('imgGenPrompt');
        if (pInput) setTimeout(() => pInput.focus(), 150);
    }
}

function closeImageGenPanel() {
    const panel = document.getElementById('imageGenPanel');
    if (panel) panel.classList.remove('open');
}

function selectAspect(btn, aspect) {
    document.querySelectorAll('#aspectGrid .opt-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentAspect = aspect;
}

function selectStyle(btn, style) {
    document.querySelectorAll('#styleGrid .opt-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentStyle = style;
}

function applyPromptSuggestion(text) {
    const input = document.getElementById('imgGenPrompt');
    if (input) {
        input.value = text;
        input.focus();
    }
}

function addCustomTyping(customText) {
    if (typeof removeTyping === 'function') removeTyping();
    const msgs = document.getElementById('msgs');
    if (!msgs) return;
    const row = document.createElement('div');
    row.className = 'msg-row appear';
    row.id = 'typing-row';
    const avHtml = typeof catAv === 'function' ? catAv() : '';
    row.innerHTML = `${avHtml}<div class="typing-bubble">
      <div class="typing-dots"><span></span><span></span><span></span></div>
      <div class="typing-label">${customText || ''}</div>
    </div>`;
    msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
}

async function submitGenerateImage() {
    const promptEl = document.getElementById('imgGenPrompt');
    const prompt = (promptEl ? promptEl.value : '').trim();
    if (!prompt) {
        if (promptEl) promptEl.focus();
        return;
    }

    const aspectBtn = document.querySelector('#aspectGrid .opt-btn.active');
    const aspecto = aspectBtn ? aspectBtn.getAttribute('data-aspect') : '1:1';

    const styleBtn = document.querySelector('#styleGrid .opt-btn.active');
    const estilo = styleBtn ? styleBtn.getAttribute('data-style') : 'fotorealista';

    const chkOpt = document.getElementById('chkOptimizarPrompt');
    const optimizar = chkOpt ? chkOpt.checked : true;

    // Cerrar panel de configuración
    closeImageGenPanel();

    // Notificar en el chat la solicitud del usuario
    const t = typeof now === 'function' ? now() : new Date().toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'});
    const estiloNombre = styleBtn ? styleBtn.innerText.replace(/[^\w\sáéíóúÁÉÍÓÚ]/gi, '').trim() : estilo;
    const userPromptDisplay = `🎨 <strong>Generar Imagen:</strong> <em>"${prompt}"</em><br><small style="opacity:0.75;">Formato: ${aspecto} | Estilo: ${estiloNombre}</small>`;
    if (typeof addMsg === 'function') addMsg(userPromptDisplay, 'user', t);

    // Indicador visual de generación
    addCustomTyping("🎨 Tux está generando tu imagen con IA...");
    const btnSubmit = document.getElementById('btnSubmitGenImg');
    if (btnSubmit) btnSubmit.disabled = true;

    try {
        const headers = {'Content-Type': 'application/json'};
        const csrf = typeof getCsrfToken === 'function' ? getCsrfToken() : '';
        if (csrf) headers['X-CSRFToken'] = csrf;

        const res = await fetch('/api/generar-imagen-ia/', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                prompt: prompt,
                aspecto: aspecto,
                estilo: estilo,
                optimizar: optimizar
            })
        });

        if (typeof removeTyping === 'function') removeTyping();
        if (btnSubmit) btnSubmit.disabled = false;

        const data = await res.json();
        if (!res.ok || !data.success) {
            const errMsg = data.error || 'No se pudo generar la imagen.';
            if (typeof addMsg === 'function') addMsg(`⚠️ ${errMsg}`, 'bot', t, errMsg);
            return;
        }

        // Construir tarjeta interactiva de resultado
        const replyText = `✨ <strong>¡Imagen generada con éxito, Administrador!</strong> 🎨`;
        const cardHtml = buildGeneratedImageCardHtml({
            url: data.image_url,
            prompt: data.prompt_original,
            estilo: data.estilo_nombre,
            aspecto: data.aspecto,
            filename: data.filename
        });

        if (typeof addMsg === 'function') {
            addMsg(replyText + cardHtml, 'bot', t, `Imagen generada: ${data.prompt_original}`);
        }
        if (typeof speak === 'function') {
            speak("Tu imagen ha sido generada con éxito.");
        }

        // Limpiar el campo de texto
        if (promptEl) promptEl.value = '';

    } catch (err) {
        if (typeof removeTyping === 'function') removeTyping();
        if (btnSubmit) btnSubmit.disabled = false;
        console.error("Error generando imagen:", err);
        if (typeof addMsg === 'function') {
            addMsg('🔌 Error al procesar la generación de imagen en el servidor.', 'bot', t);
        }
    }
}

// ══════════════════════════════════════════════
//  LIGHTBOX (PANTALLA COMPLETA)
// ══════════════════════════════════════════════

function openLightbox(src, filename) {
    const modal = document.getElementById('tuxLightbox');
    const img = document.getElementById('lightboxImg');
    const dlBtn = document.getElementById('lightboxDownloadBtn');
    if (modal && img) {
        img.src = src;
        if (dlBtn) {
            dlBtn.href = src;
            dlBtn.download = filename || 'imagen_tux_ia.jpg';
        }
        modal.classList.add('open');
    }
}

function closeLightbox(e) {
    const modal = document.getElementById('tuxLightbox');
    if (modal) modal.classList.remove('open');
}

// Exportar globalmente
window.buildGeneratedImageCardHtml = buildGeneratedImageCardHtml;
window.openImageGenPanel = openImageGenPanel;
window.closeImageGenPanel = closeImageGenPanel;
window.selectAspect = selectAspect;
window.selectStyle = selectStyle;
window.applyPromptSuggestion = applyPromptSuggestion;
window.submitGenerateImage = submitGenerateImage;
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
