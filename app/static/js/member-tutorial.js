(function () {
    'use strict';

    var root = document.getElementById('member-tutorial');
    var launcher = document.querySelector('[data-tutorial-launcher]');
    var invitation = document.getElementById('member-tutorial-invitation');
    if (!root || !launcher || !invitation) return;

    var role = document.body.getAttribute('data-tutorial-role');
    var steps = [
        { url: '/user/profile', selector: '[data-tour="dashboard"]', title: 'Your library overview', copy: 'Start here to see your current loans, due dates, reservations ready for pickup, and recent requests.' },
        { url: '/user/profile', selector: '[data-tour="current-borrowings"]', title: 'Check borrowed books', copy: 'Your active books and their due dates appear here. Open View Details when you need the borrowing information.' },
        { url: '/user/profile', selector: '[data-tour="reservations"]', title: 'Pick up reservations', copy: 'When a reserved book is ready, this section shows the claim deadline. Please collect it before that date.' },
        { url: '/user/profile', selector: '[data-tour="notifications"]', title: 'Read library updates', copy: 'Notifications keep you informed about due dates, reservations, requests, and other account updates.' },
        { url: '/user/profile', selector: '[data-tour="catalog-link"]', title: 'Find a resource', copy: 'Use Catalog to look for a title, author, keyword, or ISBN.' },
        { url: '/catalog', selector: '[data-tour="catalog-search"]', title: 'Search the catalog', copy: 'Type a title, author, keyword, or ISBN, then choose a result to view availability and borrowing options.' },
        { url: '/user/request-book', selector: '[data-tour="request-form"]', title: 'Suggest a book', copy: 'Cannot find a resource? Enter the title and, if known, the author to suggest it for the collection.' },
        { url: '/user/request-book', selector: '[data-tour="request-submit"]', title: 'Review before sending', copy: 'Check the information before you submit. This guide will never submit a request for you.' },
        { url: '/user/history?tab=borrowing', selector: '[data-tour="history-tabs"]', title: 'Review your history', copy: 'Use these tabs to review borrowing activity, fines, reservations, and book requests.' },
        { url: '/user/history?tab=borrowing', selector: '[data-tour="history-borrowing"]', title: 'Borrowing and returns', copy: 'This tab records active and returned books, their due dates, and any related fine.' },
        { url: '/user/history?tab=reservations', selector: '[data-tour="history-reservations"]', title: 'Reservation status', copy: 'Check your queue position and whether a reserved book is waiting, allocated, claimed, or expired.' },
        { url: '/user/history?tab=requests', selector: '[data-tour="history-requests"]', title: 'Request progress', copy: 'Follow each suggested book from review through approval or a final decision.' }
    ];
    var storageKey = 'mcst-member-tutorial-step';
    var stepIndex = -1;
    var returnFocus;
    var panel = root.querySelector('[data-tutorial-panel]');
    var shades = root.querySelectorAll('[data-tutorial-shade]');
    var csrfToken = root.getAttribute('data-tutorial-csrf');
    var title = root.querySelector('[data-tutorial-title]');
    var copy = root.querySelector('[data-tutorial-copy]');
    var count = root.querySelector('[data-tutorial-count]');
    var back = root.querySelector('[data-tutorial-back]');
    var next = root.querySelector('[data-tutorial-next]');

    function save(status) {
        window.fetch('/tutorials/progress', {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ status: status })
        }).catch(function () {});
    }
    function matchesUrl(url) {
        var destination = new URL(url, window.location.origin);
        return window.location.pathname === destination.pathname && window.location.search === destination.search;
    }
    function targetFor(index) {
        return Array.prototype.slice.call(document.querySelectorAll(steps[index].selector)).find(function (element) {
            var rect = element.getBoundingClientRect();
            return element.offsetParent !== null && rect.width > 0 && rect.height > 0;
        }) || null;
    }
    function navigate(index) {
        window.sessionStorage.setItem(storageKey, String(index));
        window.location.assign(steps[index].url);
    }
    function setShade(shade, left, top, width, height) {
        shade.style.left = Math.max(0, left) + 'px';
        shade.style.top = Math.max(0, top) + 'px';
        shade.style.width = Math.max(0, width) + 'px';
        shade.style.height = Math.max(0, height) + 'px';
    }
    function spotlight(target) {
        if (!target) {
            shades.forEach(function (shade) { setShade(shade, 0, 0, window.innerWidth, window.innerHeight); });
            return;
        }
        var rect = target.getBoundingClientRect();
        var gap = 8;
        var left = rect.left - gap;
        var top = rect.top - gap;
        var right = rect.right + gap;
        var bottom = rect.bottom + gap;
        setShade(shades[0], 0, 0, window.innerWidth, top);
        setShade(shades[1], 0, bottom, window.innerWidth, window.innerHeight - bottom);
        setShade(shades[2], 0, top, left, bottom - top);
        setShade(shades[3], right, top, window.innerWidth - right, bottom - top);
    }
    function positionPanel(target) {
        var rect = target ? target.getBoundingClientRect() : null;
        var gap = 14;
        var width = panel.offsetWidth;
        var height = panel.offsetHeight;
        var left = rect ? Math.min(Math.max(gap, rect.left), window.innerWidth - width - gap) : (window.innerWidth - width) / 2;
        var top = rect && rect.bottom + gap + height <= window.innerHeight ? rect.bottom + gap : rect && rect.top - gap - height >= gap ? rect.top - gap - height : (window.innerHeight - height) / 2;
        panel.style.left = Math.max(gap, left) + 'px';
        panel.style.top = Math.max(gap, top) + 'px';
        panel.style.transform = 'none';
    }
    function focusables(container) {
        return Array.prototype.slice.call(container.querySelectorAll('button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'));
    }
    function trapFocus(event, container) {
        var items = focusables(container);
        if (!items.length) return;
        var first = items[0];
        var last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    function open(index) {
        stepIndex = index;
        if (!returnFocus) returnFocus = document.activeElement;
        root.classList.remove('hidden');
        root.setAttribute('aria-hidden', 'false');
        render();
    }
    function openInvitation() {
        returnFocus = document.activeElement;
        invitation.classList.remove('hidden');
        invitation.classList.add('flex');
        invitation.setAttribute('aria-hidden', 'false');
        invitation.querySelector('[data-tutorial-start]').focus();
    }
    function closeInvitation() {
        invitation.classList.add('hidden');
        invitation.classList.remove('flex');
        invitation.setAttribute('aria-hidden', 'true');
    }
    function close(status) {
        root.classList.add('hidden');
        root.setAttribute('aria-hidden', 'true');
        document.querySelectorAll('[data-tutorial-active]').forEach(function (el) { el.removeAttribute('data-tutorial-active'); });
        window.sessionStorage.removeItem(storageKey);
        if (status) save(status);
        if (returnFocus && returnFocus.focus) returnFocus.focus();
        returnFocus = null;
    }
    function render() {
        var step = steps[stepIndex];
        if (!matchesUrl(step.url)) { navigate(stepIndex); return; }
        var target = targetFor(stepIndex);
        document.querySelectorAll('[data-tutorial-active]').forEach(function (el) { el.removeAttribute('data-tutorial-active'); });
        if (target) {
            target.setAttribute('data-tutorial-active', 'true');
            target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
        }
        count.textContent = (role === 'Faculty' ? 'Faculty guide' : 'Student guide') + ' ' + (stepIndex + 1) + ' of ' + steps.length;
        title.textContent = step.title;
        copy.textContent = step.copy;
        back.classList.toggle('invisible', stepIndex === 0);
        next.textContent = stepIndex === steps.length - 1 ? 'Finish' : 'Next';
        window.setTimeout(function () { spotlight(target); positionPanel(target); panel.focus(); }, 200);
    }
    launcher.addEventListener('click', function () { returnFocus = null; open(0); });
    invitation.querySelector('[data-tutorial-start]').addEventListener('click', function () { closeInvitation(); open(0); });
    invitation.querySelector('[data-tutorial-decline]').addEventListener('click', function () { closeInvitation(); save('dismissed'); });
    root.querySelector('[data-tutorial-exit]').addEventListener('click', function () { close('dismissed'); });
    shades.forEach(function (shade) { shade.addEventListener('click', function () { close('dismissed'); }); });
    back.addEventListener('click', function () { if (stepIndex > 0) { stepIndex--; render(); } });
    next.addEventListener('click', function () { if (stepIndex === steps.length - 1) close('completed'); else { stepIndex++; render(); } });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Tab') {
            if (!root.classList.contains('hidden')) trapFocus(event, panel);
            if (!invitation.classList.contains('hidden')) trapFocus(event, invitation);
        }
        if (event.key !== 'Escape') return;
        if (!root.classList.contains('hidden')) close('dismissed');
        if (!invitation.classList.contains('hidden')) { closeInvitation(); save('dismissed'); }
    });
    window.addEventListener('resize', function () {
        if (!root.classList.contains('hidden')) { var target = targetFor(stepIndex); spotlight(target); positionPanel(target); }
    });

    var resume = window.sessionStorage.getItem(storageKey);
    if (resume !== null) { window.sessionStorage.removeItem(storageKey); window.setTimeout(function () { open(Number(resume)); }, 150); return; }
    if (document.body.hasAttribute('data-tutorial-invite')) {
        window.fetch('/tutorials/status').then(function (response) { return response.ok ? response.json() : null; }).then(function (data) {
            if (data && data.available && !data.status) window.setTimeout(openInvitation, 350);
        }).catch(function () {});
    }
})();
