/**
 * cookie_consent.js — Sports-Max SENA
 * Gestión integral de consentimiento de cookies, Google Consent Mode v2 y almacenamiento local.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'sena_cookie_consent_v1';

    const defaultConsent = {
        necessary: true,
        preferences: true,
        analytics: false,
        timestamp: null,
        version: '1.0'
    };

    function getStoredConsent() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function saveConsent(consent) {
        consent.timestamp = new Date().toISOString();
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
        } catch (e) {
            console.warn('No se pudo guardar el consentimiento en localStorage', e);
        }
        applyConsent(consent);
    }

    function applyConsent(consent) {
        // Integración con Google Consent Mode v2
        if (typeof window.gtag === 'function') {
            window.gtag('consent', 'update', {
                'analytics_storage': consent.analytics ? 'granted' : 'denied',
                'functionality_storage': consent.preferences ? 'granted' : 'denied',
                'personalization_storage': consent.preferences ? 'granted' : 'denied',
                'security_storage': 'granted'
            });
        }

        // Despachar evento personalizado para scripts de analítica
        const event = new CustomEvent('sena_cookie_consent_updated', { detail: consent });
        window.dispatchEvent(event);

        hideBanner();
    }

    function showBanner() {
        const banner = document.getElementById('senaCookieBanner');
        if (banner) {
            banner.style.display = 'block';
        }
    }

    function hideBanner() {
        const banner = document.getElementById('senaCookieBanner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    function init() {
        const existing = getStoredConsent();

        if (!existing) {
            showBanner();
        } else {
            applyConsent(existing);
        }

        // Botón Aceptar Todas
        const btnAcceptAll = document.getElementById('btnAcceptAllCookies');
        if (btnAcceptAll) {
            btnAcceptAll.addEventListener('click', function () {
                saveConsent({
                    necessary: true,
                    preferences: true,
                    analytics: true,
                    version: '1.0'
                });
            });
        }

        // Botón Rechazar Opcionales
        const btnReject = document.getElementById('btnRejectOptionalCookies');
        if (btnReject) {
            btnReject.addEventListener('click', function () {
                saveConsent({
                    necessary: true,
                    preferences: false,
                    analytics: false,
                    version: '1.0'
                });
            });
        }

        // Botón Rechazar dentro del Modal
        const btnRejectModal = document.getElementById('btnRejectModalCookies');
        if (btnRejectModal) {
            btnRejectModal.addEventListener('click', function () {
                saveConsent({
                    necessary: true,
                    preferences: false,
                    analytics: false,
                    version: '1.0'
                });
            });
        }

        // Botón Guardar Preferencias del Modal
        const btnSavePrefs = document.getElementById('btnSaveCookiePreferences');
        if (btnSavePrefs) {
            btnSavePrefs.addEventListener('click', function () {
                const prefCheck = document.getElementById('cookiePrefPersonalizacion');
                const anaCheck = document.getElementById('cookiePrefAnaliticas');

                saveConsent({
                    necessary: true,
                    preferences: prefCheck ? prefCheck.checked : true,
                    analytics: anaCheck ? anaCheck.checked : false,
                    version: '1.0'
                });
            });
        }
    }

    // Exponer API pública para abrir el modal desde cualquier enlace legal
    window.SenaCookieConsent = {
        openPreferencesModal: function () {
            const modalEl = document.getElementById('modalConfigCookies');
            if (modalEl && window.bootstrap && window.bootstrap.Modal) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            }
        },
        getConsent: getStoredConsent
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
