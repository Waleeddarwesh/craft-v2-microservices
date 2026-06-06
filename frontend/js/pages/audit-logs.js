/* Audit Logs Page */
const AuditLogsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Audit Logs')}</h1><p>${window.t('System activity and security trail')}</p></div>
                <button class="btn btn-outline" onclick="AuditLogsPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
            </div>
            <div class="filter-bar mb-6">
                <input type="text" id="audit-search" class="form-control" placeholder="${window.t('Search logs (user, action)...')}" style="width:300px" oninput="AuditLogsPage.applyFilter()">
            </div>
            <div id="audit-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadLogs();
    }

    let allLogs = [];

    async function loadLogs() {
        try {
            const data = await API.get('/admin-api/audit-logs/');
            allLogs = data || [];
            renderTable(allLogs);
        } catch(e) { 
            document.getElementById('audit-table').innerHTML = `<div class="empty-state"><h3>Could not load audit logs</h3><p>${e.message}</p></div>`; 
        }
    }

    function renderTable(logs) {
        DataTable.render('audit-table', {
            columns: [
                { key: 'timestamp', label: 'Time', render: v => {
                    const d = new Date(v);
                    return `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${d.toLocaleDateString()} ${d.toLocaleTimeString()}</span>`;
                }},
                { key: 'user', label: 'User', render: v => `<span class="badge badge-neutral">${v}</span>` },
                { key: 'action', label: 'Action', render: v => `<span style="font-weight:var(--fw-medium)">${v}</span>` },
                { key: 'model', label: 'Resource', render: (v, r) => v ? `${v} <span style="color:var(--clr-text-muted);font-size:var(--fs-xs)">#${r.object_id||''}</span>` : '—' },
                { key: 'ip_address', label: 'IP Address', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--clr-text-muted)">${v||'—'}</span>` },
            ],
            data: logs
        });
    }

    function applyFilter() {
        const q = document.getElementById('audit-search').value.toLowerCase();
        if (!q) return renderTable(allLogs);
        
        const filtered = allLogs.filter(l => 
            (l.user && l.user.toLowerCase().includes(q)) || 
            (l.action && l.action.toLowerCase().includes(q)) ||
            (l.model && l.model.toLowerCase().includes(q))
        );
        renderTable(filtered);
    }

    function exportData() {
        const headers = ['Time', 'User', 'Action', 'Resource', 'Resource ID', 'IP Address'];
        const dataRows = allLogs.map(l => [
            l.timestamp ? new Date(l.timestamp).toLocaleString() : '',
            l.user || '',
            l.action || '',
            l.model || '',
            l.object_id || '',
            l.ip_address || ''
        ]);
        DataExport.exportToCSV('audit_logs_export.csv', headers, dataRows);
    }

    return { render, applyFilter, exportData };
})();
