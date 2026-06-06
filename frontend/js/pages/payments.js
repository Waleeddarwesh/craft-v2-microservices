/* Payments & Transactions Page */
const PaymentsPage = (() => {
    let allData = [];

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Payments & Transactions')}</h1><p>${window.t('Monitor payment history and transaction ledger')}</p></div>
                <button class="btn btn-outline" onclick="PaymentsPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
            </div>
            <div class="tabs">
                <div class="tab active" data-tab="payments" onclick="PaymentsPage.switchTab('payments')">${window.t('Payment History')}</div>
                <div class="tab" data-tab="transactions" onclick="PaymentsPage.switchTab('transactions')">${window.t('Transactions')}</div>
            </div>
            <div id="payments-content">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        currentTab = 'payments';
        loadTab();
    }

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
        loadTab();
    }

    async function loadTab() {
        if (currentTab === 'payments') await loadPayments();
        else await loadTransactions();
    }

    async function loadPayments() {
        try {
            const data = await API.get('/admin-api/payments/');
            allData = data || [];
            DataTable.render('payments-content', {
                columns: [
                    { key: 'id', label: 'ID', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${(v||'').toString().slice(0,8)}</span>` },
                    { key: 'user_email', label: 'User', render: (v, r) => v || r.user || '—' },
                    { key: 'payment_status', label: 'Status', render: v => {
                        const cls = v === 'succeeded' ? 'success' : v === 'failed' ? 'danger' : 'warning';
                        return `<span class="badge badge-${cls}">${window.t(v||'')}</span>`;
                    }},
                    { key: 'stripe_session_id', label: 'Stripe ID', render: v => v ? `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${v.slice(0,15)}…</span>` : '—' },
                    { key: 'date', label: 'Date', render: v => v ? new Date(v).toLocaleString() : '—' },
                ],
                data: allData,
                onRowClick: row => DataTable.showRowDetails(row, 'Payment Details')
            });
        } catch(e) { document.getElementById('payments-content').innerHTML = `<div class="empty-state"><h3>Could not load payments</h3><p>${e.message}</p></div>`; }
    }

    async function loadTransactions() {
        try {
            const data = await API.get('/admin-api/transactions/');
            allData = data || [];
            DataTable.render('payments-content', {
                columns: [
                    { key: 'id', label: 'ID', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${(v||'').toString().slice(0,8)}</span>` },
                    { key: 'transaction_type', label: 'Type', render: v => `<span class="badge badge-neutral">${window.t((v||'').replace(/_/g,' '))}</span>` },
                    { key: 'amount', label: 'Amount', render: v => { const n = parseFloat(v||0); return `<span class="${n >= 0 ? 'text-success' : 'text-danger'}">EGP ${Math.abs(n).toFixed(2)}</span>`; }},
                    { key: 'user_email', label: 'User', render: (v, r) => v || r.user || '—' },
                    { key: 'created_at', label: 'Date', render: v => v ? new Date(v).toLocaleString() : '—' },
                ],
                data: allData,
                onRowClick: row => DataTable.showRowDetails(row, 'Transaction Details')
            });
        } catch(e) { document.getElementById('payments-content').innerHTML = `<div class="empty-state"><h3>Could not load transactions</h3><p>${e.message}</p></div>`; }
    }

    function exportData() {
        if (currentTab === 'payments') {
            const headers = ['ID', 'User', 'Status', 'Stripe Session ID', 'Date'];
            const dataRows = allData.map(p => [
                p.id || '',
                p.user_email || p.user || '',
                p.payment_status || '',
                p.stripe_session_id || '',
                p.date ? new Date(p.date).toLocaleString() : ''
            ]);
            DataExport.exportToCSV('payments_export.csv', headers, dataRows);
        } else {
            const headers = ['ID', 'Type', 'Amount', 'User', 'Date'];
            const dataRows = allData.map(t => [
                t.id || '',
                (t.transaction_type || '').replace(/_/g, ' '),
                parseFloat(t.amount || 0).toFixed(2),
                t.user_email || t.user || '',
                t.created_at ? new Date(t.created_at).toLocaleString() : ''
            ]);
            DataExport.exportToCSV('transactions_export.csv', headers, dataRows);
        }
    }

    return { render, switchTab, exportData };
})();
