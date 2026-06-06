/* Withdrawal Requests Page */
const WithdrawalsPage = (() => {
    const STATUS_MAP = { Requested:'warning', 'Awaiting Approval':'warning', Approved:'info', Processing:'info', Completed:'success', Rejected:'danger', Failed:'danger' };
    let allWithdrawals = [];

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>Withdrawal Requests</h1><p>Manage balance withdrawal requests from suppliers</p></div>
                <button class="btn btn-outline" onclick="WithdrawalsPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
            </div>
            <div class="filter-bar mb-6">
                <select id="withdraw-status-filter" onchange="WithdrawalsPage.applyFilter()">
                    <option value="">All Statuses</option>
                    <option value="Requested">Requested</option>
                    <option value="Approved">Approved</option>
                    <option value="Processing">Processing</option>
                    <option value="Completed">Completed</option>
                    <option value="Rejected">Rejected</option>
                </select>
            </div>
            <div id="withdrawals-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadWithdrawals();
    }

    async function loadWithdrawals() {
        try {
            const data = await API.get('/admin-api/withdrawals/');
            allWithdrawals = data || [];
            renderTable(allWithdrawals);
        } catch(e) { document.getElementById('withdrawals-table').innerHTML = `<div class="empty-state"><h3>Could not load withdrawals</h3><p>${e.message}</p></div>`; }
    }

    function renderTable(items) {
        DataTable.render('withdrawals-table', {
            columns: [
                { key: 'id', label: 'ID', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${(v||'').toString().slice(0,8)}</span>` },
                { key: 'user_name', label: 'User', render: (v, r) => v || r.user || '—' },
                { key: 'amount', label: 'Amount', render: v => `EGP ${parseFloat(v||0).toFixed(2)}` },
                { key: 'transfer_type', label: 'Method' },
                { key: 'transfer_number', label: 'Transfer #' },
                { key: 'risk_score', label: 'Risk', render: v => {
                    const n = parseFloat(v||0); const cls = n > 70 ? 'danger' : n > 30 ? 'warning' : 'success';
                    return `<span class="badge badge-${cls}">${n.toFixed(0)}%</span>`;
                }},
                { key: 'transfer_status', label: 'Status', render: v => `<span class="badge badge-${STATUS_MAP[v]||'neutral'} badge-dot">${v||''}</span>` },
                { key: '_actions', label: 'Actions', render: (_, row) => {
                    if (row.transfer_status === 'Requested' || row.transfer_status === 'Awaiting Approval') {
                        return `<div style="display:flex;gap:var(--space-2)">
                            <button class="btn btn-sm btn-success" onclick="WithdrawalsPage.action('${row.id}','approve')">Approve</button>
                            <button class="btn btn-sm btn-danger" onclick="WithdrawalsPage.action('${row.id}','reject')">Reject</button>
                        </div>`;
                    }
                    return `<button class="btn btn-sm btn-ghost" onclick="WithdrawalsPage.view('${row.id}')">View</button>`;
                }}
            ],
            data: items
        });
    }

    function applyFilter() {
        const status = document.getElementById('withdraw-status-filter').value;
        renderTable(status ? allWithdrawals.filter(w => w.transfer_status === status) : allWithdrawals);
    }

    async function action(id, act) {
        Modal.confirm(`${act.charAt(0).toUpperCase()+act.slice(1)} Withdrawal`, `Are you sure you want to ${act} this withdrawal request?`, async () => {
            try {
                await API.post(`/admin-api/withdrawals/${id}/action/`, { action: act });
                Toast.success(`Withdrawal ${act}d successfully`);
                await loadWithdrawals();
            } catch(e) { Toast.error(e.message); }
        }, act.charAt(0).toUpperCase()+act.slice(1), act === 'approve' ? 'success' : 'danger');
    }

    async function view(id) {
        const w = allWithdrawals.find(x => x.id === id);
        if (!w) return;
        Modal.open('Withdrawal Details', `<div class="detail-grid">
            <div class="detail-item"><span class="detail-label">User</span><span class="detail-value">${w.user_name || ''}</span></div>
            <div class="detail-item"><span class="detail-label">Amount</span><span class="detail-value">EGP ${parseFloat(w.amount||0).toFixed(2)}</span></div>
            <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value"><span class="badge badge-${STATUS_MAP[w.transfer_status]||'neutral'}">${w.transfer_status}</span></span></div>
            <div class="detail-item"><span class="detail-label">Method</span><span class="detail-value">${w.transfer_type||''}</span></div>
            <div class="detail-item"><span class="detail-label">Transfer #</span><span class="detail-value">${w.transfer_number||''}</span></div>
            <div class="detail-item"><span class="detail-label">Risk Score</span><span class="detail-value">${parseFloat(w.risk_score||0).toFixed(1)}%</span></div>
            <div class="detail-item"><span class="detail-label">Date</span><span class="detail-value">${w.created_at ? new Date(w.created_at).toLocaleString() : ''}</span></div>
        </div>${w.notes ? `<div class="mt-4"><strong style="font-size:var(--fs-sm)">Notes:</strong><p style="font-size:var(--fs-sm);color:var(--clr-text-secondary);margin-top:var(--space-1)">${w.notes}</p></div>` : ''}
        ${w.admin_notes ? `<div class="mt-4"><strong style="font-size:var(--fs-sm)">Admin Notes:</strong><p style="font-size:var(--fs-sm);color:var(--clr-text-secondary);margin-top:var(--space-1)">${w.admin_notes}</p></div>` : ''}`);
    }

    function exportData() {
        const headers = ['ID', 'User', 'Amount', 'Method', 'Transfer #', 'Risk Score %', 'Status', 'Date'];
        const dataRows = allWithdrawals.map(w => [
            w.id || '',
            w.user_name || w.user || '',
            parseFloat(w.amount || 0).toFixed(2),
            w.transfer_type || '',
            w.transfer_number || '',
            parseFloat(w.risk_score || 0).toFixed(1),
            w.transfer_status || '',
            w.created_at ? new Date(w.created_at).toLocaleDateString() : ''
        ]);
        DataExport.exportToCSV('withdrawals_export.csv', headers, dataRows);
    }

    return { render, action, view, applyFilter, exportData };
})();
