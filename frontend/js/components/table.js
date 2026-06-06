/* Data Table Component */
window.DEFAULT_IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Cg transform='translate(176, 126) scale(2)' fill='none' stroke='%239ca3af' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='18' height='18' rx='2' ry='2'/%3E%3Ccircle cx='8.5' cy='8.5' r='1.5'/%3E%3Cpolyline points='21 15 16 10 5 21'/%3E%3C/g%3E%3C/svg%3E";

const DataTable = (() => {
    function render(id, { columns, data, pageSize = 10, searchable = true, onRowClick = null }) {
        const state = { data, filtered: [...data], page: 1, pageSize, sortCol: null, sortDir: 'asc', search: '' };

        function getPageData() {
            const start = (state.page - 1) * state.pageSize;
            return state.filtered.slice(start, start + state.pageSize);
        }

        function totalPages() { return Math.max(1, Math.ceil(state.filtered.length / state.pageSize)); }

        function sort(col) {
            if (state.sortCol === col) state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
            else { state.sortCol = col; state.sortDir = 'asc'; }
            state.filtered.sort((a, b) => {
                let va = a[col], vb = b[col];
                if (va == null) return 1; if (vb == null) return -1;
                if (typeof va === 'string') { va = va.toLowerCase(); vb = (vb || '').toLowerCase(); }
                const cmp = va < vb ? -1 : va > vb ? 1 : 0;
                return state.sortDir === 'asc' ? cmp : -cmp;
            });
            state.page = 1;
            update();
        }

        function search(q) {
            state.search = q.toLowerCase();
            state.filtered = state.data.filter(row =>
                columns.some(c => String(row[c.key] || '').toLowerCase().includes(state.search))
            );
            state.page = 1;
            update();
        }

        function update() {
            const wrapper = document.getElementById(id);
            if (!wrapper) return;
            const rows = getPageData();
            const tp = totalPages();

            // Thead
            let thead = '<tr>';
            columns.forEach(c => {
                const sorted = state.sortCol === c.key;
                const arrow = sorted ? (state.sortDir === 'asc' ? ' ↑' : ' ↓') : '';
                thead += `<th class="${sorted ? 'sorted' : ''}" onclick="DataTable._instances['${id}'].sort('${c.key}')">${window.t(c.label)}${arrow}</th>`;
            });
            thead += '</tr>';

            // Tbody
            let tbody = '';
            if (rows.length === 0) {
                tbody = `<tr><td colspan="${columns.length}" style="text-align:center;padding:var(--space-10);color:var(--clr-text-muted)">
                    <div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-border);margin-bottom:16px;">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="15" x2="15" y2="15"/>
                        </svg>
                        <h3 style="margin-bottom:8px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">${window.t('No Data Available')}</h3>
                        <p style="color:var(--clr-text-muted);font-size:var(--fs-sm);">${window.t("We couldn't find any records matching your criteria.")}</p>
                    </div>
                </td></tr>`;
            } else {
                rows.forEach((row, i) => {
                    const clickAttr = onRowClick ? `style="cursor:pointer" onclick="DataTable._instances['${id}'].rowClick(${(state.page-1)*state.pageSize+i})"` : '';
                    tbody += `<tr ${clickAttr}>`;
                    columns.forEach(c => {
                        const val = c.render ? c.render(row[c.key], row) : (row[c.key] ?? '—');
                        tbody += `<td dir="auto">${val}</td>`;
                    });
                    tbody += '</tr>';
                });
            }

            // Pagination
            let pag = `<button ${state.page <= 1 ? 'disabled' : ''} onclick="DataTable._instances['${id}'].setPage(${state.page - 1})">‹</button>`;
            for (let p = 1; p <= tp; p++) {
                if (tp > 7 && p > 2 && p < tp - 1 && Math.abs(p - state.page) > 1) {
                    if (p === 3 || p === tp - 2) pag += '<button disabled>…</button>';
                    continue;
                }
                pag += `<button class="${p === state.page ? 'active' : ''}" onclick="DataTable._instances['${id}'].setPage(${p})">${p}</button>`;
            }
            pag += `<button ${state.page >= tp ? 'disabled' : ''} onclick="DataTable._instances['${id}'].setPage(${state.page + 1})">›</button>`;

            const searchHTML = searchable ? `<div class="form-search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><input class="form-input" placeholder="${window.t('Search...')}" value="${state.search}" oninput="DataTable._instances['${id}'].search(this.value)"></div>` : '';

            wrapper.innerHTML = `<div class="data-table-wrapper">
                <div class="data-table-toolbar">${searchHTML}<div class="page-info" style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${state.filtered.length} ${window.t('records')}</div></div>
                <div style="overflow-x:auto"><table class="data-table"><thead>${thead}</thead><tbody>${tbody}</tbody></table></div>
                <div class="data-table-footer"><div class="page-info">${window.t('Page')} ${state.page} ${window.t('of')} ${tp}</div><div class="pagination">${pag}</div></div>
            </div>`;
        }

        // Store instance globally for event handlers
        if (!DataTable._instances) DataTable._instances = {};
        DataTable._instances[id] = {
            sort, search, update,
            setPage(p) { state.page = p; update(); },
            rowClick(i) { if (onRowClick) onRowClick(state.filtered[i]); },
            setData(d) { state.data = d; state.filtered = [...d]; state.page = 1; if (state.search) search(state.search); else update(); }
        };

        update();
        return DataTable._instances[id];
    }

    function showRowDetails(row, title) {
        if (!row) return;
        let html = '<div class="table-responsive"><table class="data-table"><tbody>';
        for (let key in row) {
            if (row[key] !== null && row[key] !== '' && typeof row[key] !== 'function') {
                if (typeof row[key] === 'object' && !Array.isArray(row[key])) continue;

                // format key: convert snake_case or camelCase to Title Case
                const formattedKey = key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()).trim();
                let val = row[key];

                if (Array.isArray(val)) {
                    let arrayHtml = '';
                    val.forEach(item => {
                        let strItem = (typeof item === 'object' && item && item.image) ? item.image : item;
                        if (typeof strItem === 'string' && (strItem.match(/\.(jpeg|jpg|gif|png|webp|svg)$/i) || strItem.startsWith('data:image/'))) {
                            arrayHtml += `<img src="${strItem}" alt="${formattedKey}" onerror="this.onerror=null;this.src=window.DEFAULT_IMG" style="max-width:150px; max-height:150px; border-radius:var(--radius-sm); object-fit:contain; border:1px solid var(--clr-border); display:inline-block; background:var(--clr-surface-alt);">`;
                        } else if (typeof strItem !== 'object') {
                            arrayHtml += `<span class="badge badge-neutral m-1">${strItem}</span>`;
                        }
                    });
                    if (!arrayHtml) continue;
                    val = `<div style="display:flex; flex-wrap:wrap; gap:8px;">${arrayHtml}</div>`;
                } else {
                    if (val === true || val === 'true') val = window.t('Yes') || 'Yes';
                    else if (val === false || val === 'false') val = window.t('No') || 'No';
                    else if (typeof val === 'string' && (val.match(/\.(jpeg|jpg|gif|png|webp|svg)$/i) || val.startsWith('data:image/'))) {
                        val = `<img src="${val}" alt="${formattedKey}" onerror="this.onerror=null;this.src=window.DEFAULT_IMG" style="max-width:150px; max-height:150px; border-radius:var(--radius-sm); object-fit:contain; border:1px solid var(--clr-border); background:var(--clr-surface-alt);">`;
                    }
                    else if (typeof val === 'string') {
                        val = window.t(val);
                    }
                }
                
                html += `<tr><td style="font-weight:var(--fw-bold);width:35%;background:var(--clr-surface-alt);vertical-align:middle;">${window.t(formattedKey) || formattedKey}</td><td dir="auto" style="word-break:break-word;vertical-align:middle;">${val}</td></tr>`;
            }
        }
        html += '</tbody></table></div>';
        Modal.open(window.t(title || 'Details'), html, '');
    }

    return { render, _instances: {}, showRowDetails };
})();
