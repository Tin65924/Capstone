/* Shared no-reload helpers: toast + JSON POST form helper.
 *
 * Pages include this alongside their own small wiring script. Plain forms
 * keep working with JS off (classic POST -> redirect); with JS on, marked
 * forms POST via fetch with `Accept: application/json` and patch the DOM
 * in place instead of reloading the page.
 */
(function () {
    'use strict';

    var COLORS = {
        success: 'background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;',
        error: 'background:#fef2f2;color:#991b1b;border:1px solid #fecaca;',
        info: 'background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;'
    };

    function container() {
        var el = document.getElementById('ajax-toasts');
        if (el) return el;
        el = document.createElement('div');
        el.id = 'ajax-toasts';
        el.setAttribute('role', 'status');
        el.setAttribute('aria-live', 'polite');
        el.style.cssText = 'position:fixed;right:1rem;bottom:1rem;z-index:9999;' +
            'display:flex;flex-direction:column;gap:0.5rem;max-width:min(92vw,24rem);';
        document.body.appendChild(el);
        return el;
    }

    function toast(message, category) {
        var style = COLORS[category] || COLORS.info;
        var box = container();
        var el = document.createElement('div');
        el.style.cssText = style + 'border-radius:0.5rem;padding:0.625rem 0.875rem;' +
            'font-size:0.875rem;font-weight:500;box-shadow:0 8px 24px rgba(0,0,0,0.12);';
        el.textContent = message;
        box.appendChild(el);
        setTimeout(function () {
            el.style.transition = 'opacity 0.4s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 450);
        }, 4000);
    }

    function postForm(url, formData) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData,
            credentials: 'same-origin'
        }).then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (data) {
                if (!resp.ok) {
                    throw new Error((data && data.error) || ('Request failed (' + resp.status + ').'));
                }
                return data;
            });
        });
    }

    function setBusy(button, busy, idleLabel) {
        if (!button) return;
        if (busy) {
            if (button.dataset.label === undefined) {
                button.dataset.label = button.textContent;
            }
            button.disabled = true;
            button.style.opacity = '0.6';
            button.textContent = 'Saving…';
        } else {
            button.disabled = false;
            button.style.opacity = '';
            button.textContent = idleLabel !== undefined ? idleLabel : (button.dataset.label || button.textContent);
        }
    }

    window.AjaxUI = { toast: toast, postForm: postForm, setBusy: setBusy };
})();
