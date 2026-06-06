/* Return Requests Page */
const ReturnsPage = (() => {
    const STATUS_MAP = { new:'warning', accepted:'success', rejected:'danger', cancelled:'neutral' };
    let allReturns = [];

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Return Requests')}</h1><p>${window.t('Review and manage product return requests')}</p></div>
                <button class="btn btn-outline" onclick="ReturnsPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    ${window.t('Export CSV')}
                </button>
            </div>
            <div class="filter-bar mb-6">
                <select id="return-status-filter" onchange="ReturnsPage.applyFilter()">
                    <option value="">${window.t('All Statuses')}</option>
                    <option value="new">${window.t('New')}</option>
                    <option value="accepted">${window.t('Accepted')}</option>
                    <option value="rejected">${window.t('Rejected')}</option>
                    <option value="cancelled">${window.t('Cancelled')}</option>
                </select>
                <select id="return-reason-filter" onchange="ReturnsPage.applyFilter()">
                    <option value="">${window.t('All Reasons')}</option>
                    <option value="damaged">${window.t('Damaged')}</option>
                    <option value="wrong_item">${window.t('Wrong Item')}</option>
                    <option value="wrong_size">${window.t('Wrong Size')}</option>
                    <option value="not_as_described">${window.t('Not as Described')}</option>
                    <option value="changed_mind">${window.t('Changed Mind')}</option>
                    <option value="other">${window.t('Other')}</option>
                </select>
                <div style="display:flex; gap:var(--space-2); align-items:center;">
                    <input type="date" id="return-date-start" class="form-input" style="width:140px" onchange="ReturnsPage.loadReturns()">
                    <span style="color:var(--clr-text-muted)">${window.t('to')}</span>
                    <input type="date" id="return-date-end" class="form-input" style="width:140px" onchange="ReturnsPage.loadReturns()">
                </div>
            </div>
            <div id="returns-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadReturns();
    }

    async function loadReturns() {
        try {
            document.getElementById('returns-table').innerHTML = '<div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>';
            const start = document.getElementById('return-date-start')?.value || '';
            const end = document.getElementById('return-date-end')?.value || '';
            const qs = start || end ? `?start_date=${start}&end_date=${end}` : '';
            const data = await API.get('/admin-api/returns/' + qs);
            allReturns = data || [];
            applyFilter();
        } catch(e) { document.getElementById('returns-table').innerHTML = `<div class="empty-state"><h3>Could not load returns</h3><p>${e.message}</p></div>`; }
    }

    function renderTable(returns) {
        DataTable.render('returns-table', {
            columns: [
                { key: 'id', label: 'ID', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${(v||'').toString().slice(0,8)}</span>` },
                { key: 'product_name', label: 'Product', render: (v, row) => v || row.product || '—' },
                { key: 'customer_name', label: 'Customer' },
                { key: 'quantity', label: 'Qty' },
                { key: 'reason', label: 'Reason', render: v => `<span class="badge badge-neutral">${(v||'').replace(/_/g,' ')}</span>` },
                { key: 'amount', label: 'Amount', render: v => `EGP ${parseFloat(v||0).toFixed(2)}` },
                { key: 'status', label: 'Status', render: v => `<span class="badge badge-${STATUS_MAP[v]||'neutral'} badge-dot">${v||''}</span>` },
                { key: 'created_at', label: 'Date', render: v => v ? new Date(v).toLocaleDateString() : '—' },
                { key: '_actions', label: 'Actions', render: (_, row) => row.status === 'new' ? `
                    <div style="display:flex;gap:var(--space-2)">
                        <button class="btn btn-sm btn-success" onclick="ReturnsPage.action('${row.id}','accept')">Accept</button>
                        <button class="btn btn-sm btn-danger" onclick="ReturnsPage.action('${row.id}','reject')">Reject</button>
                    </div>` : `<button class="btn btn-sm btn-ghost" onclick="ReturnsPage.view('${row.id}')">View</button>` }
            ],
            data: returns
        });
    }

    function applyFilter() {
        const status = document.getElementById('return-status-filter').value;
        const reason = document.getElementById('return-reason-filter').value;
        let filtered = allReturns;
        if (status) filtered = filtered.filter(r => r.status === status);
        if (reason) filtered = filtered.filter(r => r.reason === reason);
        renderTable(filtered);
    }

    async function action(id, act) {
        const actionText = act === 'accept' ? 'Accept' : 'Reject';
        Modal.confirm(`${actionText} Return Request`, `Are you sure you want to ${act} this return request?`, async () => {
            try {
                await API.post(`/admin-api/returns/${id}/action/`, { action: act });
                Toast.success(`Return request ${act}ed successfully`);
                await loadReturns();
            } catch(e) { Toast.error(e.message); }
        }, actionText, act === 'accept' ? 'success' : 'danger');
    }

    async function view(id) {
        const ret = allReturns.find(r => r.id === id);
        if (!ret) return;
        const body = `
            <div class="detail-grid">
                <div class="detail-item"><span class="detail-label">Product</span><span class="detail-value">${ret.product_name || ret.product || ''}</span></div>
                <div class="detail-item"><span class="detail-label">Customer</span><span class="detail-value">${ret.customer_name || ''}</span></div>
                <div class="detail-item"><span class="detail-label">Quantity</span><span class="detail-value">${ret.quantity}</span></div>
                <div class="detail-item"><span class="detail-label">Amount</span><span class="detail-value">EGP ${parseFloat(ret.amount||0).toFixed(2)}</span></div>
                <div class="detail-item"><span class="detail-label">Reason</span><span class="detail-value">${(ret.reason||'').replace(/_/g,' ')}</span></div>
                <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value"><span class="badge badge-${STATUS_MAP[ret.status]||'neutral'}">${ret.status}</span></span></div>
                <div class="detail-item"><span class="detail-label">Date</span><span class="detail-value">${ret.created_at ? new Date(ret.created_at).toLocaleString() : ''}</span></div>
            </div>
            ${ret.image ? `<div class="mt-4"><img src="${Auth.getApiBase()}${ret.image}" style="max-width:100%;border-radius:var(--radius-md)"/></div>` : ''}`;
        Modal.open('Return Request Details', body);
    }

    function exportData() {
        const headers = ['ID', 'Product', 'Customer', 'Qty', 'Reason', 'Amount', 'Status', 'Date'];
        const dataRows = allReturns.map(r => [
            r.id || '',
            r.product_name || r.product || '',
            r.customer_name || '',
            r.quantity || 0,
            (r.reason || '').replace(/_/g, ' '),
            parseFloat(r.amount || 0).toFixed(2),
            r.status || '',
            r.created_at ? new Date(r.created_at).toLocaleDateString() : ''
        ]);
        DataExport.exportToCSV('returns_export.csv', headers, dataRows);
    }

    return { render, action, view, applyFilter, exportData };
})();
