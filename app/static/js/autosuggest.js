// Autosuggestions for catalog/student entry fields plus duplicate-record
// feedback for complete records.
//
// - Inputs with data-suggest="<field>" get a debounced suggestion dropdown
//   fed by GET /api/suggestions?field=&q=. The first suggestion is
//   pre-highlighted and acts as the inline suggestion.
//   Keyboard: Tab / Enter / Right Arrow (caret at end) accept the highlighted
//   value; ArrowUp/Down move the highlight; Escape closes. After accepting via
//   Tab, the next Tab navigates normally. Clicking a suggestion also selects it.
// - Forms with data-exists-book / data-exists-student run a duplicate check
//   once the identifying fields are filled. A Bloom filter (GET /api/bloom) is
//   used as a local pre-filter: only when it says "maybe exists" is the
//   confirming DB query (/api/book-exists or /api/student-exists) issued. The
//   message is only ever shown for confirmed duplicate records.
(function () {
    'use strict';

    var SUGGEST_ENDPOINT = '/api/suggestions';
    var BLOOM_ENDPOINT = '/api/bloom';
    var MIN_QUERY = 2;
    var SUGGEST_DEBOUNCE = 250;
    var EXISTS_DEBOUNCE = 400;
    var SEP = '\u001f';

    // ---------- utilities ----------
    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var ctx = this;
            var args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, wait);
        };
    }

    function normalize(value) {
        return String(value).trim().toLowerCase();
    }

    function escHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function caretAtEnd(input) {
        return input.selectionStart === input.value.length;
    }

    // ---------- Bloom filter (mirrors app/bloom.py) ----------
    var recordFilters = {};

    function fnv1a32(text, seed) {
        var bytes = new TextEncoder().encode(text);
        var h = (0x811C9DC5 ^ seed) >>> 0;
        for (var i = 0; i < bytes.length; i++) {
            h ^= bytes[i];
            h = Math.imul(h, 0x01000193) >>> 0;
        }
        return h;
    }

    function decodePayload(payload) {
        var binary = atob(payload.bits);
        var bytes = new Uint8Array(binary.length);
        for (var i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return { m: payload.m, k: payload.k, bytes: bytes };
    }

    function likelyContains(payload, value) {
        var text = normalize(value);
        if (!text) return false;
        var h1 = fnv1a32(text, 0x9747B28C);
        var h2 = fnv1a32(text, 0x5BF03635);
        if (h2 === 0) h2 = 1;
        for (var i = 0; i < payload.k; i++) {
            var idx = (h1 + i * h2) % payload.m;
            if (!(payload.bytes[idx >> 3] & (0x80 >> (idx & 7)))) return false;
        }
        return true;
    }

    function bookRecordKey(title, author, isbn) {
        return normalize(title) + SEP + normalize(author) + SEP + normalize(isbn || '');
    }

    function loadBloomFilters() {
        return fetch(BLOOM_ENDPOINT)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.book_record) recordFilters.book_record = decodePayload(data.book_record);
                if (data.student_record) recordFilters.student_record = decodePayload(data.student_record);
            })
            .catch(function () { /* bloom unavailable — DB check still runs */ });
    }

    // ---------- suggestion dropdown ----------
    function getDropdown(input) {
        if (input._asBox) return input._asBox;
        var box = document.createElement('div');
        box.className = 'as-box hidden fixed z-[9999] min-w-[200px] max-h-60 overflow-y-auto py-1 '
            + 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 '
            + 'rounded-lg shadow-lg';
        box.setAttribute('role', 'listbox');
        document.body.appendChild(box);
        input._asBox = box;
        return box;
    }

    function positionDropdown(input, box) {
        var rect = input.getBoundingClientRect();
        box.style.left = rect.left + 'px';
        box.style.top = (rect.bottom + 4) + 'px';
        box.style.width = Math.max(rect.width, 200) + 'px';
    }

    function setHighlight(input, index) {
        var box = input._asBox;
        if (!box) return;
        var items = box.querySelectorAll('.as-item');
        for (var i = 0; i < items.length; i++) {
            items[i].classList.toggle('as-item-active', i === index);
        }
        var el = items[index];
        if (el) el.scrollIntoView({ block: 'nearest' });
    }

    function closeDropdown(input) {
        if (input._asBox) input._asBox.classList.add('hidden');
        input._as.open = false;
        input._as.highlight = -1;
    }

    function acceptSuggestion(input, value) {
        input.value = value;
        input._as.skipNextSuggest = true;
        closeDropdown(input);
        input.focus();
        var evt = document.createEvent('Event');
        evt.initEvent('input', true, true);
        input.dispatchEvent(evt);
    }

    function renderDropdown(input, suggestions) {
        var state = input._as;
        var box = getDropdown(input);
        box.innerHTML = '';
        var q = input.value.trim();
        var lowerQ = q.toLowerCase();

        suggestions.forEach(function (s, i) {
            var item = document.createElement('button');
            item.type = 'button';
            item.setAttribute('role', 'option');
            item.className = 'as-item block w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-200';
            var idx = s.toLowerCase().indexOf(lowerQ);
            if (idx > -1) {
                item.innerHTML = escHtml(s.slice(0, idx)) + '<strong>'
                    + escHtml(s.slice(idx, idx + q.length)) + '</strong>'
                    + escHtml(s.slice(idx + q.length));
            } else {
                item.textContent = s;
            }
            item.addEventListener('mousedown', function (e) {
                e.preventDefault();
                acceptSuggestion(input, s);
            });
            item.addEventListener('mouseenter', function () {
                setHighlight(input, i);
            });
            box.appendChild(item);
        });

        state.suggestions = suggestions;
        state.highlight = 0;
        positionDropdown(input, box);
        box.classList.remove('hidden');
        setHighlight(input, 0);
        state.open = true;
    }

    function fetchSuggestions(input) {
        var q = input.value.trim();
        if (q.length < MIN_QUERY) {
            closeDropdown(input);
            return;
        }
        var field = input.getAttribute('data-suggest');
        var requested = normalize(q);
        fetch(SUGGEST_ENDPOINT + '?field=' + encodeURIComponent(field) + '&q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (normalize(input.value.trim()) !== requested || document.activeElement !== input) return;
                var list = data.suggestions || [];
                if (!list.length) {
                    closeDropdown(input);
                    return;
                }
                renderDropdown(input, list);
            })
            .catch(function () { closeDropdown(input); });
    }

    function handleSuggestKeydown(input, e) {
        var state = input._as;
        if (e.key === 'ArrowDown') {
            if (state.open && state.suggestions.length) {
                e.preventDefault();
                state.highlight = (state.highlight + 1) % state.suggestions.length;
                setHighlight(input, state.highlight);
            }
        } else if (e.key === 'ArrowUp') {
            if (state.open && state.suggestions.length) {
                e.preventDefault();
                state.highlight = (state.highlight - 1 + state.suggestions.length) % state.suggestions.length;
                setHighlight(input, state.highlight);
            }
        } else if (e.key === 'Enter') {
            if (state.open && state.highlight > -1) {
                e.preventDefault();
                acceptSuggestion(input, state.suggestions[state.highlight]);
            }
        } else if (e.key === 'Escape') {
            if (state.open) {
                e.preventDefault();
                closeDropdown(input);
            }
        } else if (e.key === 'Tab') {
            if (state.open && state.highlight > -1) {
                e.preventDefault();
                acceptSuggestion(input, state.suggestions[state.highlight]);
            }
        } else if (e.key === 'ArrowRight') {
            if (state.open && state.highlight > -1 && caretAtEnd(input)) {
                e.preventDefault();
                acceptSuggestion(input, state.suggestions[state.highlight]);
            }
        }
    }

    function attachSuggest(input) {
        if (input._as) return;
        input._as = { open: false, suggestions: [], highlight: -1, skipNextSuggest: false };
        input.addEventListener('input', debounce(function () {
            if (input._as.skipNextSuggest) {
                input._as.skipNextSuggest = false;
                return;
            }
            fetchSuggestions(input);
        }, SUGGEST_DEBOUNCE));
        input.addEventListener('keydown', function (e) { handleSuggestKeydown(input, e); });
        input.addEventListener('blur', function () {
            setTimeout(function () { closeDropdown(input); }, 150);
        });
    }

    // ---------- duplicate-record feedback ----------
    function showExists(form, message) {
        var msg = form.querySelector('[data-exists-msg]');
        if (!msg) return;
        msg.textContent = message;
        msg.classList.remove('hidden');
    }

    function hideExists(form) {
        var msg = form.querySelector('[data-exists-msg]');
        if (msg) msg.classList.add('hidden');
    }

    function attachBookExists(form) {
        var titleInput = form.querySelector('[name="title"]');
        var authorInput = form.querySelector('[name="author"]');
        var isbnInput = form.querySelector('[name="isbn"]');
        if (!titleInput || !authorInput) return;

        function check() {
            var title = titleInput.value.trim();
            var author = authorInput.value.trim();
            if (!title || !author) {
                hideExists(form);
                return;
            }
            var isbn = isbnInput.value.trim();
            var key = bookRecordKey(title, author, isbn);
            if (recordFilters.book_record && !likelyContains(recordFilters.book_record, key)) {
                hideExists(form);
                return;
            }
            var url = '/api/book-exists?title=' + encodeURIComponent(title)
                + '&author=' + encodeURIComponent(author);
            if (isbn) url += '&isbn=' + encodeURIComponent(isbn);
            fetch(url)
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.exists) showExists(form, 'Book already exists.');
                    else hideExists(form);
                })
                .catch(function () { hideExists(form); });
        }

        [titleInput, authorInput, isbnInput].forEach(function (el) {
            el.addEventListener('input', debounce(check, EXISTS_DEBOUNCE));
        });
    }

    function attachStudentExists(form) {
        var idInput = form.querySelector('[name="id_number"]');
        if (!idInput) return;

        function check() {
            var idNumber = idInput.value.trim();
            if (idNumber.length < 3) {
                hideExists(form);
                return;
            }
            var key = normalize(idNumber);
            if (recordFilters.student_record && !likelyContains(recordFilters.student_record, key)) {
                hideExists(form);
                return;
            }
            fetch('/api/student-exists?id_number=' + encodeURIComponent(idNumber))
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.exists) showExists(form, 'Student already exists.');
                    else hideExists(form);
                })
                .catch(function () { hideExists(form); });
        }

        idInput.addEventListener('input', debounce(check, EXISTS_DEBOUNCE));
    }

    // ---------- init ----------
    function init() {
        var suggestInputs = document.querySelectorAll('[data-suggest]');
        for (var i = 0; i < suggestInputs.length; i++) {
            attachSuggest(suggestInputs[i]);
        }

        var bookForms = document.querySelectorAll('[data-exists-book]');
        var studentForms = document.querySelectorAll('[data-exists-student]');
        if (!bookForms.length && !studentForms.length) return;

        loadBloomFilters().then(function () {
            for (var b = 0; b < bookForms.length; b++) attachBookExists(bookForms[b]);
            for (var s = 0; s < studentForms.length; s++) attachStudentExists(studentForms[s]);
        });
    }

    window.addEventListener('scroll', function () {
        document.querySelectorAll('.as-box:not(.hidden)').forEach(function (box) {
            box.classList.add('hidden');
        });
    }, true);

    // Exposed so pages that inject [data-suggest] inputs dynamically
    // (e.g. modals) can wire them after insertion, and so category
    // pickers can check values against the category_record filter.
    // recordFilters fills in asynchronously; likelyContains reads it live.
    var bloomPromise = null;

    function ensureBloom() {
        if (!bloomPromise) bloomPromise = loadBloomFilters();
        return bloomPromise;
    }

    window.MCSTAutosuggest = {
        rescan: init,
        filters: recordFilters,
        likelyContains: likelyContains,
        ensureBloom: ensureBloom
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
