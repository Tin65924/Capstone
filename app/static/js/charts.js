/* Shared lightweight charts (no dependencies): donut, hbars, line.
 * Data shape: rows/points are [label, count] pairs.
 * Each renderer tolerates empty data and renders a placeholder instead.
 * All renderers are hoverable (native <title> + floating tooltip) and
 * carry axis scales/labels: donuts get an interactive legend with
 * percentages, hbars get a value scale, lines get X/Y axes with titles.
 */
(function () {
    'use strict';

    var RCOLORS = ['#1e3a8a', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444',
                   '#8b5cf6', '#ec4899', '#64748b'];

    function rNum(n) {
        try {
            return Number(n).toLocaleString('en-US');
        } catch (e) {
            return String(n);
        }
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function empty(el, text) {
        el.innerHTML = '<div class="text-xs text-gray-400 py-8 text-center">' +
            escapeHtml(text || 'No data yet') + '</div>';
    }

    function totalOf(rows) {
        var t = 0, i;
        for (i = 0; i < rows.length; i++) t += (+rows[i][1] || 0);
        return t;
    }

    function pctOf(count, total) {
        if (!total) return '0%';
        return (Math.round(count / total * 1000) / 10) + '%';
    }

    function niceCeil(v) {
        v = Math.ceil(Number(v) || 0);
        if (v <= 4) return Math.max(v, 1);
        var mag = Math.pow(10, Math.floor(Math.log10(v)));
        var norm = v / mag;
        if (norm <= 1) return mag;
        if (norm <= 2) return 2 * mag;
        if (norm <= 5) return 5 * mag;
        return 10 * mag;
    }

    function shortTick(s) {
        s = String(s == null ? '' : s);
        var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (m) return m[2] + '/' + m[3];
        return s.length > 10 ? s.slice(0, 10) : s;
    }

    /* ---- floating tooltip (one per page) ---- */
    function ensureTip() {
        var tip = document.getElementById('audit-chart-tip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'audit-chart-tip';
            tip.setAttribute('role', 'tooltip');
            document.body.appendChild(tip);
        }
        return tip;
    }

    function showTip(html, x, y) {
        var tip = ensureTip();
        tip.innerHTML = html;
        tip.style.left = x + 'px';
        tip.style.top = y + 'px';
        tip.className = 'show';
    }

    function hideTip() {
        var tip = document.getElementById('audit-chart-tip');
        if (tip) tip.className = '';
    }

    function bindTip(node, getHtml) {
        if (!node || !node.addEventListener) return;
        node.addEventListener('mousemove', function (e) {
            showTip(getHtml(), e.clientX, e.clientY);
        });
        node.addEventListener('mouseleave', hideTip);
    }

    function legendList(rows, total, unit) {
        var html = '<ul class="mt-3 space-y-1" role="list" aria-label="Chart legend">', i, label, count, pct, tip;
        for (i = 0; i < rows.length; i++) {
            label = String(rows[i][0]);
            count = +rows[i][1] || 0;
            pct = pctOf(count, total);
            tip = label + ': ' + count + ' ' + unit + ' (' + pct + ')';
            html += '<li class="audit-legend-item" role="listitem" data-idx="' + i + '"' +
                ' title="' + escapeHtml(tip) + '" tabindex="0">' +
                '<span class="w-2.5 h-2.5 rounded-full shrink-0" style="background:' +
                RCOLORS[i % RCOLORS.length] + '"></span>' +
                '<span class="flex-1 min-w-0 truncate text-gray-600">' + escapeHtml(label) + '</span>' +
                '<span class="font-bold">' + rNum(count) + '</span>' +
                '<span class="text-gray-400 w-11 text-right">' + pct + '</span></li>';
        }
        return html + '</ul>';
    }

    function highlightSeg(svg, idx, on) {
        if (!svg) return;
        var segs = svg.querySelectorAll('.audit-seg'), i;
        if (on) {
            svg.classList.add('audit-dim');
            for (i = 0; i < segs.length; i++) {
                if (segs[i].getAttribute('data-idx') === String(idx)) segs[i].classList.add('active');
                else segs[i].classList.remove('active');
            }
        } else {
            svg.classList.remove('audit-dim');
            for (i = 0; i < segs.length; i++) segs[i].classList.remove('active');
        }
    }

    function donut(el, rows, opts) {
        rows = (rows || []).slice(0, 8);
        var o = { centerSub: 'events', unit: 'events' };
        if (opts) {
            if (opts.centerSub) o.centerSub = opts.centerSub;
            if (opts.unit) o.unit = opts.unit;
        }
        var total = totalOf(rows);
        if (!total) { empty(el); return; }
        var R = 54, C = 2 * Math.PI * R, off = 0, i, frac, html, label, count;
        html = '<div class="flex items-center gap-4">' +
            '<svg width="140" height="140" viewBox="0 0 140 140" class="shrink-0" role="img" aria-label="Donut chart: ' +
            escapeHtml(o.centerSub) + ' by category">' +
            '<circle cx="70" cy="70" r="' + R + '" fill="none" stroke="#f1f5f9" stroke-width="18"/>';
        for (i = 0; i < rows.length; i++) {
            label = String(rows[i][0]);
            count = +rows[i][1] || 0;
            frac = count / total;
            if (frac <= 0) continue;
            html += '<circle class="audit-seg" data-idx="' + i + '" cx="70" cy="70" r="' + R + '" fill="none" stroke="' +
                RCOLORS[i % RCOLORS.length] + '" stroke-width="18" ' +
                'stroke-dasharray="' + (frac * C).toFixed(1) + ' ' + C.toFixed(1) + '" ' +
                'stroke-dashoffset="' + (-off * C).toFixed(1) + '" ' +
                'transform="rotate(-90 70 70)" stroke-linecap="butt">' +
                '<title>' + escapeHtml(label) + ': ' + rNum(count) + ' (' + pctOf(count, total) + ')</title></circle>';
            off += frac;
        }
        html += '<text x="70" y="66" text-anchor="middle" font-size="20" font-weight="800" fill="#1e293b">' +
            rNum(total) + '</text>' +
            '<text x="70" y="84" text-anchor="middle" font-size="10" fill="#64748b">' +
            escapeHtml(o.centerSub) + '</text></svg>';
        html += '<div class="flex-1 min-w-0">' + legendList(rows, total, o.unit) + '</div></div>';
        el.innerHTML = html;
        var svg = el.querySelector('svg');
        var items = el.querySelectorAll('.audit-legend-item');
        var segs = el.querySelectorAll('.audit-seg');
        var j, idx, row;
        for (j = 0; j < segs.length; j++) {
            (function (seg) {
                idx = parseInt(seg.getAttribute('data-idx'), 10);
                row = rows[idx] || ['-', 0];
                bindTip(seg, function () {
                    return '<b>' + escapeHtml(String(row[0])) + '</b>' +
                        '<span class="tt-sub">' + rNum(row[1]) + ' ' + escapeHtml(o.unit) +
                        ' · ' + pctOf(+row[1] || 0, total) + ' of total</span>';
                });
                seg.addEventListener('mouseenter', function () { highlightSeg(svg, idx, true); });
                seg.addEventListener('mouseleave', function () { highlightSeg(svg, idx, false); });
            })(segs[j]);
        }
        for (j = 0; j < items.length; j++) {
            (function (item) {
                idx = parseInt(item.getAttribute('data-idx'), 10);
                row = rows[idx] || ['-', 0];
                bindTip(item, function () {
                    return '<b>' + escapeHtml(String(row[0])) + '</b>' +
                        '<span class="tt-sub">' + rNum(row[1]) + ' ' + escapeHtml(o.unit) +
                        ' · ' + pctOf(+row[1] || 0, total) + ' of total</span>';
                });
                function on() { highlightSeg(svg, idx, true); }
                function off() { highlightSeg(svg, idx, false); hideTip(); }
                item.addEventListener('mouseenter', on);
                item.addEventListener('mouseleave', off);
                item.addEventListener('focus', on);
                item.addEventListener('blur', off);
            })(items[j]);
        }
    }

    function hbars(el, rows, barClass, unit) {
        rows = (rows || []).slice(0, 10);
        unit = unit || 'events';
        var max = 0, i, html, grand = 0;
        for (i = 0; i < rows.length; i++) {
            max = Math.max(max, +rows[i][1] || 0);
            grand += (+rows[i][1] || 0);
        }
        if (!rows.length || !max) { empty(el); return; }
        html = '<div class="space-y-1.5" role="list" aria-label="Bar chart: count per day">';
        for (i = 0; i < rows.length; i++) {
            html += '<div class="audit-hbar-row" role="listitem" tabindex="0" title="' +
                escapeHtml(String(rows[i][0]) + ': ' + rows[i][1] + ' ' + unit +
                    ' (' + pctOf(+rows[i][1] || 0, grand) + ' of shown)') + '">' +
                '<div class="flex justify-between text-xs mb-1">' +
                '<span class="text-gray-600 truncate pr-2">' + escapeHtml(rows[i][0]) + '</span>' +
                '<span class="font-bold shrink-0">' + rNum(rows[i][1]) + '</span></div>' +
                '<div class="h-2 rounded-full bg-slate-100 overflow-hidden"><div class="h-full rounded-full ' +
                (barClass || 'bg-primary') + '" style="width:' +
                Math.round((+rows[i][1] || 0) * 100 / max) + '%"></div></div></div>';
        }
        html += '</div>' +
            '<div class="flex justify-between text-[10px] text-gray-400 mt-2">' +
            '<span>0</span><span>Max: ' + rNum(max) + ' ' + escapeHtml(unit) + ' · hover a bar for details</span></div>';
        el.innerHTML = html;
        var nodes = el.querySelectorAll('.audit-hbar-row');
        for (i = 0; i < nodes.length; i++) {
            (function (node, row) {
                bindTip(node, function () {
                    return '<b>' + escapeHtml(String(row[0])) + '</b>' +
                        '<span class="tt-sub">' + rNum(row[1]) + ' ' + escapeHtml(unit) +
                        ' · ' + pctOf(+row[1] || 0, grand) + ' of shown</span>';
                });
            })(nodes[i], rows[i]);
        }
    }

    function line(el, points, color, opts) {
        points = points || [];
        color = color || '#1e3a8a';
        var o = { xLabel: 'Date', yLabel: 'Count', unit: 'events' };
        if (opts) {
            if (opts.xLabel) o.xLabel = opts.xLabel;
            if (opts.yLabel) o.yLabel = opts.yLabel;
            if (opts.unit) o.unit = opts.unit;
        }
        var i, rawMax = 0;
        for (i = 0; i < points.length; i++) rawMax = Math.max(rawMax, +points[i][1] || 0);
        if (!points.length || !rawMax) { empty(el); return; }
        var yMax = niceCeil(rawMax);
        var n = points.length;
        var W = 600, H = 268, ML = 48, MR = 14, MT = 12, MB = 46;
        var plotW = W - ML - MR, plotH = H - MT - MB, base = MT + plotH;
        var stepX = n > 1 ? plotW / (n - 1) : 0;
        var pts = [];
        for (i = 0; i < n; i++) {
            pts.push([
                ML + stepX * i,
                base - ((+points[i][1] || 0) / yMax) * plotH
            ]);
        }
        function linePath(p) {
            return p.map(function (q, j) {
                return (j ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1);
            }).join(' ');
        }
        var html = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="w-full" style="height:220px" role="img" ' +
            'aria-label="Line chart. X axis: ' + escapeHtml(o.xLabel) + '. Y axis: ' + escapeHtml(o.yLabel) + '.">';
        var ticks = 4, ti, tv, ty;
        for (ti = 0; ti <= ticks; ti++) {
            tv = Math.round(yMax * ti / ticks);
            ty = base - (tv / yMax) * plotH;
            html += '<line x1="' + ML + '" y1="' + ty.toFixed(1) + '" x2="' + (W - MR) + '" y2="' + ty.toFixed(1) +
                '" stroke="' + (ti === 0 ? '#cbd5e1' : '#eef2f7') + '"/>' +
                '<text x="' + (ML - 7) + '" y="' + (ty + 3.5).toFixed(1) + '" text-anchor="end" font-size="10" fill="#94a3b8">' +
                rNum(tv) + '</text>';
        }
        html += '<path d="' + linePath(pts) + ' L' + pts[n - 1][0].toFixed(1) + ' ' + base +
            ' L' + pts[0][0].toFixed(1) + ' ' + base + ' Z" fill="' + color + '18"/>' +
            '<path d="' + linePath(pts) + '" fill="none" stroke="' + color + '" stroke-width="2.5"/>' +
            '<line x1="' + ML + '" y1="' + MT + '" x2="' + ML + '" y2="' + base + '" stroke="#cbd5e1"/>' +
            '<line x1="' + ML + '" y1="' + base + '" x2="' + (W - MR) + '" y2="' + base + '" stroke="#cbd5e1"/>';
        var xCount = Math.min(5, n), xi, di, dx, anchor, ax;
        for (xi = 0; xi < xCount; xi++) {
            di = xCount === 1 ? 0 : Math.round(xi * (n - 1) / (xCount - 1));
            dx = ML + stepX * di;
            anchor = xi === 0 ? 'start' : (xi === xCount - 1 ? 'end' : 'middle');
            ax = xi === 0 ? Math.max(dx, ML) : (xi === xCount - 1 ? Math.min(dx, W - MR) : dx);
            html += '<line x1="' + dx.toFixed(1) + '" y1="' + base + '" x2="' + dx.toFixed(1) + '" y2="' + (base + 5) + '" stroke="#cbd5e1"/>' +
                '<text x="' + ax.toFixed(1) + '" y="' + (base + 18) + '" text-anchor="' + anchor + '" font-size="10" fill="#94a3b8">' +
                '<title>' + escapeHtml(String(points[di][0])) + '</title>' +
                escapeHtml(shortTick(points[di][0])) + '</text>';
        }
        for (i = 0; i < n; i++) {
            html += '<circle class="audit-dot" data-idx="' + i + '" cx="' + pts[i][0].toFixed(1) + '" cy="' + pts[i][1].toFixed(1) +
                '" r="4.5" fill="' + color + '" stroke="#fff" stroke-width="1.5"><title>' +
                escapeHtml(String(points[i][0])) + ': ' + rNum(points[i][1]) + ' ' + escapeHtml(o.unit) + '</title></circle>';
        }
        html += '<text x="14" y="' + (MT + plotH / 2).toFixed(1) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#64748b" ' +
            'transform="rotate(-90 14 ' + (MT + plotH / 2).toFixed(1) + ')">' + escapeHtml(o.yLabel) + '</text>' +
            '<text x="' + (ML + plotW / 2).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#64748b">' +
            escapeHtml(o.xLabel) + '</text></svg>' +
            '<div class="flex justify-between text-[10px] text-gray-400 mt-1"><span>X: ' +
            escapeHtml(o.xLabel) + ' (' + escapeHtml(String(points[0][0])) + ' → ' +
            escapeHtml(String(points[n - 1][0])) + ')</span><span>Y: ' + escapeHtml(o.yLabel) + '</span></div>';
        el.innerHTML = html;
        var dots = el.querySelectorAll('.audit-dot');
        for (i = 0; i < dots.length; i++) {
            (function (dot) {
                var idx = parseInt(dot.getAttribute('data-idx'), 10);
                var row = points[idx] || ['-', 0];
                bindTip(dot, function () {
                    return '<b>' + escapeHtml(String(row[0])) + '</b>' +
                        '<span class="tt-sub">' + escapeHtml(o.xLabel) + ': ' + escapeHtml(String(row[0])) +
                        ' · ' + escapeHtml(o.yLabel) + ': ' + rNum(row[1]) + '</span>';
                });
            })(dots[i]);
        }
    }

    window.AuditCharts = {
        RCOLORS: RCOLORS,
        rNum: rNum,
        escapeHtml: escapeHtml,
        donut: donut,
        hbars: hbars,
        line: line
    };
})();
