/* Orders Management Page */
const OrdersPage = (() => {
    const STATUS_MAP = { created:'info', ready_to_ship:'primary', 'on my way':'warning', 'In Transmit':'warning', 'delivered to First warehouse':'info', 'delivered to Second warehouse':'info', 'delivered successfully':'success', 'failed delivery':'danger', cancelled:'danger' };

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>Orders Management</h1><p>Track and manage all customer orders</p></div>
                <button class="btn btn-outline" onclick="OrdersPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
            </div>
            <div class="filter-bar mb-6">
                <select id="order-status-filter" onchange="OrdersPage.applyFilter()">
                    <option value="">All Statuses</option>
                    <option value="created">Created</option>
                    <option value="ready_to_ship">Ready to Ship</option>
                    <option value="on my way">On My Way</option>
                    <option value="delivered successfully">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                </select>
                <select id="order-payment-filter" onchange="OrdersPage.applyFilter()">
                    <option value="">All Payments</option>
                    <option value="Cash on Delivery">Cash on Delivery</option>
                    <option value="Credit Card">Credit Card</option>
                    <option value="Balance">Balance</option>
                </select>
                <div style="display:flex; gap:var(--space-2); align-items:center;">
                    <input type="date" id="order-date-start" class="form-input" style="width:140px" onchange="OrdersPage.loadOrders()">
                    <span style="color:var(--clr-text-muted)">to</span>
                    <input type="date" id="order-date-end" class="form-input" style="width:140px" onchange="OrdersPage.loadOrders()">
                </div>
            </div>
            <div id="orders-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadOrders();
    }

    let allOrders = [];
    async function loadOrders() {
        try {
            document.getElementById('orders-table').innerHTML = '<div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>';
            const start = document.getElementById('order-date-start')?.value || '';
            const end = document.getElementById('order-date-end')?.value || '';
            const qs = start || end ? `?start_date=${start}&end_date=${end}` : '';
            const data = await API.get('/admin-api/orders/' + qs);
            allOrders = data || [];
            applyFilter();
        } catch(e) { document.getElementById('orders-table').innerHTML = `<div class="empty-state"><h3>Could not load orders</h3><p>${e.message}</p></div>`; }
    }

    function renderTable(orders) {
        DataTable.render('orders-table', {
            columns: [
                { key: 'order_number', label: 'Order #', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${v || '—'}</span>` },
                { key: 'user_email', label: 'Customer', render: (v, row) => `<span class="truncate" style="max-width:160px;display:inline-block">${v || row.user || '—'}</span>` },
                { key: 'final_amount', label: 'Total', render: v => `EGP ${parseFloat(v || 0).toLocaleString()}` },
                { key: 'payment_method', label: 'Payment' },
                { key: 'status', label: 'Status', render: v => `<span class="badge badge-${STATUS_MAP[v] || 'neutral'} badge-dot">${window.t((v||'').replace(/_/g,' '))}</span>` },
                { key: 'paid', label: 'Paid', render: v => v ? '<span class="text-success">✓</span>' : '<span class="text-danger">✗</span>' },
                { key: 'created_at', label: 'Date', render: v => v ? new Date(v).toLocaleDateString() : '—' },
                { key: '_actions', label: '', render: (_, row) => `<button class="btn btn-sm btn-ghost" onclick="OrdersPage.viewOrder('${row.id}')">View</button>` }
            ],
            data: orders,
            onRowClick: (row) => viewOrder(row.id)
        });
    }

    function applyFilter() {
        const status = document.getElementById('order-status-filter').value;
        const payment = document.getElementById('order-payment-filter').value;
        let filtered = allOrders;
        if (status) filtered = filtered.filter(o => o.status === status);
        if (payment) filtered = filtered.filter(o => o.payment_method === payment);
        renderTable(filtered);
    }

    async function viewOrder(id) {
        try {
            const order = allOrders.find(o => o.id === id);
            if (!order) return;
            const items = order.items || [];
            
            // Generate timeline based on status
            const statuses = ['created', 'ready_to_ship', 'on my way', 'delivered successfully'];
            let currentIndex = statuses.indexOf(order.status);
            if (currentIndex === -1) currentIndex = statuses.length; // e.g., if cancelled, just show what we can
            
            let timelineHtml = '<div class="timeline mt-4 mb-6">';
            statuses.forEach((s, i) => {
                const isPast = i <= currentIndex;
                const isCurrent = i === currentIndex;
                const isFailed = order.status === 'cancelled' || order.status === 'failed delivery';
                const statusColor = isCurrent && isFailed ? 'var(--clr-danger)' : (isPast ? 'var(--clr-success)' : 'var(--clr-surface-border)');
                
                timelineHtml += `
                    <div class="timeline-step" style="display:flex; align-items:center; gap:var(--space-3); margin-bottom:var(--space-4); opacity:${isPast ? '1' : '0.5'};">
                        <div style="width:24px; height:24px; border-radius:50%; background:${statusColor}; display:flex; align-items:center; justify-content:center; color:white;">
                            ${isPast ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
                        </div>
                        <div style="flex:1;">
                            <div style="font-weight:var(--fw-medium); color:var(--clr-text); text-transform:capitalize;">${window.t(s.replace(/_/g, ' '))}</div>
                            <div style="font-size:var(--fs-xs); color:var(--clr-text-muted)">${i === 0 ? new Date(order.created_at).toLocaleString() : (isPast ? 'Completed' : 'Pending')}</div>
                        </div>
                    </div>
                `;
            });
            timelineHtml += '</div>';

            const body = `
                <div style="display:grid; grid-template-columns: 2fr 1fr; gap:var(--space-6);">
                    <div>
                        <div class="detail-grid mb-4">
                            <div class="detail-item"><span class="detail-label">Order Number</span><span class="detail-value">${order.order_number || ''}</span></div>
                            <div class="detail-item"><span class="detail-label">Customer</span><span class="detail-value">${order.user_email || ''}</span></div>
                            <div class="detail-item"><span class="detail-label">${window.t('Status')}</span><span class="detail-value"><span class="badge badge-${STATUS_MAP[order.status]||'neutral'} badge-dot">${window.t((order.status||'').replace(/_/g, ' '))}</span></span></div>
                            <div class="detail-item"><span class="detail-label">Payment</span><span class="detail-value">${order.payment_method || ''}</span></div>
                            <div class="detail-item"><span class="detail-label">Subtotal</span><span class="detail-value">EGP ${parseFloat(order.total_amount || 0).toFixed(2)}</span></div>
                            <div class="detail-item"><span class="detail-label">Discount</span><span class="detail-value">EGP ${parseFloat(order.discount_amount || 0).toFixed(2)}</span></div>
                            <div class="detail-item"><span class="detail-label">Delivery Fee</span><span class="detail-value">EGP ${parseFloat(order.delivery_fee || 0).toFixed(2)}</span></div>
                            <div class="detail-item"><span class="detail-label">Final Amount</span><span class="detail-value" style="font-weight:var(--fw-bold);color:var(--clr-accent)">EGP ${parseFloat(order.final_amount || 0).toFixed(2)}</span></div>
                            <div class="detail-item"><span class="detail-label">Paid</span><span class="detail-value">${order.paid ? '<span class="text-success">✓ Yes</span>' : '<span class="text-danger">✗ No</span>'}</span></div>
                            <div class="detail-item"><span class="detail-label">Date</span><span class="detail-value">${order.created_at ? new Date(order.created_at).toLocaleString() : ''}</span></div>
                        </div>
                        ${items.length ? '<h4 style="margin-bottom:var(--space-3);font-size:var(--fs-sm)">Order Items</h4><table class="data-table"><thead><tr><th>Product</th><th>Qty</th><th>Price</th></tr></thead><tbody>' + items.map(i => `<tr><td>${i.product_name || ''}</td><td>${i.quantity}</td><td>EGP ${parseFloat(i.price||0).toFixed(2)}</td></tr>`).join('') + '</tbody></table>' : ''}
                    </div>
                    <div style="border-left:1px solid var(--clr-surface-border); padding-left:var(--space-4);">
                        <h4 style="margin-bottom:var(--space-4);">Order Timeline</h4>
                        ${timelineHtml}
                    </div>
                </div>
            `;
            Modal.open('Order Details', body, '', 'modal-lg');
        } catch (e) { Toast.error('Failed to load order: ' + e.message); }
    }

    function exportData() {
        const headers = ['Order Number', 'Customer', 'Total', 'Payment', 'Status', 'Paid', 'Date'];
        const dataRows = allOrders.map(o => [
            o.order_number || '',
            o.user_email || o.user || '',
            parseFloat(o.final_amount || 0).toFixed(2),
            o.payment_method || '',
            (o.status || '').replace(/_/g, ' '),
            o.paid ? 'Yes' : 'No',
            o.created_at ? new Date(o.created_at).toLocaleDateString() : ''
        ]);
        DataExport.exportToCSV('orders_export.csv', headers, dataRows);
    }

    return { render, viewOrder, applyFilter, exportData };
})();
