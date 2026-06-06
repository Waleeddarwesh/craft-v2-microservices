/* Disputes Page */
const DisputesPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header">
                <div><h1>${window.t('Disputes')}</h1><p>${window.t('Manage conflicts between customers and suppliers')}</p></div>
            </div>
            <div id="disputes-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadDisputes();
    }

    async function loadDisputes() {
        try {
            const data = await API.get('/admin-api/disputes/');
            if (!data || data.length === 0) {
                document.getElementById('disputes-table').innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--clr-text-muted)" stroke-width="1" style="margin-bottom:16px;"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><h3>No Disputes</h3><p style="color:var(--clr-text-muted);">All clear here!</p></div>';
                return;
            }
            DataTable.render('disputes-table', {
                columns: [
                    { key: 'id', label: 'ID' },
                    { key: 'customer_email', label: 'Customer' },
                    { key: 'supplier_email', label: 'Supplier' },
                    { key: 'order_number', label: 'Order #' },
                    { key: 'status', label: 'Status', render: v => {
                        const map = { open: 'danger', resolved: 'success', closed: 'neutral' };
                        return `<span class="badge badge-${map[v] || 'neutral'}">${window.t(v.toUpperCase())}</span>`;
                    }},
                    { key: 'reason', label: 'Reason' },
                    { key: 'created_at', label: 'Created At', render: v => new Date(v).toLocaleString() },
                    { key: 'actions', label: 'Actions', render: (v, row) => `
                        <button class="btn btn-sm btn-primary" onclick="window.arbitrateDispute(${row.id})">${window.t('Arbitrate')}</button>
                    `}
                ],
                data: data
            });
        } catch(e) {
            document.getElementById('disputes-table').innerHTML = `<div class="empty-state"><h3>Could not load disputes</h3><p>${e.message}</p></div>`;
        }
    }

    return { render, loadDisputes };
})();

window.arbitrateDispute = async function(id) {
    try {
        const dispute = await API.get(`/admin-api/disputes/${id}/`);
        
        const content = `
            <div style="display:flex; flex-direction:column; gap:16px;">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
                    <div class="card" style="padding:16px; background:var(--clr-bg-alt);">
                        <h4 style="margin-top:0; color:var(--clr-primary);">${window.t('Customer')}</h4>
                        <p><strong>${window.t('Name')}:</strong> ${dispute.customer.name}</p>
                        <p><strong>${window.t('Email')}:</strong> ${dispute.customer.email}</p>
                    </div>
                    <div class="card" style="padding:16px; background:var(--clr-bg-alt);">
                        <h4 style="margin-top:0; color:var(--clr-warning);">${window.t('Supplier')}</h4>
                        <p><strong>${window.t('Name')}:</strong> ${dispute.supplier.name}</p>
                        <p><strong>${window.t('Email')}:</strong> ${dispute.supplier.email}</p>
                    </div>
                </div>
                
                <div class="card" style="padding:16px;">
                    <h4 style="margin-top:0;">${window.t('Dispute Details')}</h4>
                    <p><strong>${window.t('Order')}:</strong> ${dispute.order ? dispute.order.order_number : 'N/A'} ($${dispute.order ? dispute.order.amount : '0.00'})</p>
                    <p><strong>${window.t('Reason')}:</strong> ${dispute.reason}</p>
                    <p><strong>${window.t('Current Status')}:</strong> <span class="badge badge-primary">${dispute.status.toUpperCase()}</span></p>
                </div>
                
                <hr style="border:0; border-top:1px solid var(--clr-border);">
                
                <form id="dispute-resolve-form" style="display:flex; flex-direction:column; gap:12px;">
                    <div>
                        <label>${window.t('Admin Resolution & Official Ruling')}</label>
                        <textarea id="dispute-resolution" class="input" rows="5" placeholder="${window.t('Type the official ruling here...')}" required>${dispute.admin_resolution || ''}</textarea>
                        <small style="color:var(--clr-text-muted);">${window.t('This ruling is manually enforced. Ensure all financial actions are performed separately before closing.')}</small>
                    </div>
                    <div>
                        <label>${window.t('Update Status')}</label>
                        <select id="dispute-status" class="input">
                            <option value="open" ${dispute.status === 'open' ? 'selected' : ''}>${window.t('Open')}</option>
                            <option value="resolved" ${dispute.status === 'resolved' ? 'selected' : ''}>${window.t('Resolved (Close Case)')}</option>
                            <option value="closed" ${dispute.status === 'closed' ? 'selected' : ''}>${window.t('Closed (Dismissed)')}</option>
                        </select>
                    </div>
                    <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:8px;">
                        <button type="button" class="btn btn-outline" onclick="Modal.close()">${window.t('Cancel')}</button>
                        <button type="submit" class="btn btn-primary">${window.t('Submit Resolution')}</button>
                    </div>
                </form>
            </div>
        `;

        Modal.open(`${window.t('Dispute')} #${dispute.id} ${window.t('Arbitration')}`, content);

        document.getElementById('dispute-resolve-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const status = document.getElementById('dispute-status').value;
            const admin_resolution = document.getElementById('dispute-resolution').value;
            
            try {
                const btn = e.target.querySelector('button[type="submit"]');
                btn.innerText = window.t('Submitting...');
                btn.disabled = true;

                await API.patch(`/admin-api/disputes/${id}/`, { status, admin_resolution });
                Toast.show(window.t('Dispute resolved successfully'), 'success');
                Modal.close();
                DisputesPage.loadDisputes();
            } catch(err) {
                Toast.show(err.message || window.t('Failed to update dispute'), 'error');
                const btn = e.target.querySelector('button[type="submit"]');
                btn.innerText = window.t('Submit Resolution');
                btn.disabled = false;
            }
        });

    } catch(err) {
        Toast.show(window.t('Failed to load dispute details'), 'error');
    }
};
