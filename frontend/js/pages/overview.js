/* Overview / Dashboard Home Page */
const OverviewPage = (() => {
    async function render(container) {
        const widgets = window.UserIdentity ? window.UserIdentity.widgets : [];

        const hasRevenueChart = widgets.includes('revenue_chart');
        const hasStatusChart = widgets.includes('status_chart');

        let chartsHtml = '';
        if (hasRevenueChart || hasStatusChart) {
            const gridStyle = (hasRevenueChart && hasStatusChart) ? '' : ' style="grid-template-columns: 1fr;"';
            chartsHtml += `<div class="overview-charts"${gridStyle}>`;
            if (hasRevenueChart) chartsHtml += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Revenue Trend')}</span></div><div class="chart-container"><canvas id="chart-revenue"></canvas></div></div>`;
            if (hasStatusChart) chartsHtml += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Orders by Status')}</span></div><div class="chart-container"><canvas id="chart-orders-status"></canvas></div></div>`;
            chartsHtml += '</div>';
        }

        const hasOrders = widgets.includes('total_orders');
        const hasActivity = widgets.includes('active_users');
        let bottom1Html = '';
        if (hasOrders || hasActivity) {
            bottom1Html += '<div class="overview-bottom" style="display:grid; grid-template-columns: ' + (hasOrders && hasActivity ? '2fr 1fr' : '1fr') + '; gap:var(--space-6); margin-top:var(--space-6)">';
            if (hasOrders) bottom1Html += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Recent Orders')}</span></div><div id="recent-orders-table"></div></div>`;
            if (hasActivity) bottom1Html += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Live Activity Feed')}</span></div><div id="recent-activity-list"></div></div>`;
            bottom1Html += '</div>';
        }

        const hasTopProducts = widgets.includes('total_revenue');
        const hasPendingReturns = widgets.includes('pending_returns');
        let bottom2Html = '';
        if (hasTopProducts || hasPendingReturns) {
            bottom2Html += '<div class="overview-bottom" style="display:grid; grid-template-columns: ' + (hasTopProducts && hasPendingReturns ? '1fr 1fr' : '1fr') + '; gap:var(--space-6); margin-top:var(--space-6)">';
            if (hasTopProducts) bottom2Html += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Top Selling Products')}</span></div><div id="top-products-table"></div></div>`;
            if (hasPendingReturns) bottom2Html += `<div class="card"><div class="card-header"><span class="card-title">${window.t('Pending Returns')}</span></div><div id="pending-returns-list"></div></div>`;
            bottom2Html += '</div>';
        }

        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Dashboard Overview')}</h1><p>${window.t("Welcome back! Here's what's happening today.")}</p></div>
                <div style="display:flex; align-items:center; gap:8px; font-size:var(--fs-xs); color:var(--clr-text-muted);">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/></svg>
                    <span id="refresh-countdown">${window.t('Refreshing in')} 60s</span>
                </div>
            </div>
            
            <div class="overview-grid" id="overview-stats">
                ${Array(8).fill('<div class="skeleton skeleton-card"></div>').join('')}
            </div>

            ${chartsHtml}
            ${bottom1Html}
            ${bottom2Html}
            
            <style>
                @media (max-width: 1024px) {
                    .overview-bottom { grid-template-columns: 1fr !important; }
                }
            </style>`;

        loadStats();
        loadCharts();
        loadRecentOrders();
        loadRecentActivity();
        loadTopProducts();
        loadPendingReturns();

        startAutoRefresh();
    }

    let refreshTimer = null;
    let refreshSeconds = 60;

    function startAutoRefresh() {
        if (refreshTimer) clearInterval(refreshTimer);
        refreshSeconds = 60;

        refreshTimer = setInterval(() => {
            refreshSeconds--;
            const indicator = document.getElementById('refresh-countdown');
            if (indicator) indicator.textContent = `${window.t('Refreshing in')} ${refreshSeconds}s`;

            if (refreshSeconds <= 0) {
                refreshSeconds = 60;
                if (indicator) indicator.textContent = window.t('Refreshing...');

                // Silently reload data
                Promise.all([
                    loadStats(), loadCharts(), loadRecentOrders(),
                    loadRecentActivity(), loadTopProducts(), loadPendingReturns()
                ]).then(() => {
                    if (indicator) indicator.textContent = `${window.t('Refreshing in')} ${refreshSeconds}s`;
                });
            }
        }, 1000);
    }

    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    async function loadStats() {
        try {
            const stats = await API.get('/admin-api/stats/');
            const icons = {
                revenue: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
                orders: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>',
                aov: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
                conversion: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
                users: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
                returns: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>',
                products: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>',
                withdrawals: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>'
            };
            const widgets = window.UserIdentity ? window.UserIdentity.widgets : [];
            let html = '';
            if (widgets.includes('total_revenue')) html += StatsCard.render(window.t('Total Revenue'), `EGP ${(stats.total_revenue || 0).toLocaleString()}`, icons.revenue, 'accent', stats.revenue_change);
            if (widgets.includes('total_orders')) html += StatsCard.render(window.t('Total Orders'), stats.total_orders || 0, icons.orders, 'primary', stats.orders_change);
            if (widgets.includes('total_revenue')) html += StatsCard.render(window.t('Avg Order Value'), `EGP ${(stats.avg_order_value || 0).toLocaleString()}`, icons.aov, 'info');
            if (widgets.includes('total_revenue')) html += StatsCard.render(window.t('Conversion Rate'), `${(stats.conversion_rate || 0)}%`, icons.conversion, 'success');
            if (widgets.includes('active_users')) html += StatsCard.render(window.t('Active Users'), stats.active_users || 0, icons.users, 'info');
            if (widgets.includes('pending_returns')) html += StatsCard.render(window.t('Pending Returns'), stats.pending_returns || 0, icons.returns, 'warning');
            if (widgets.includes('products_in_stock')) html += StatsCard.render(window.t('Products In Stock'), stats.products_in_stock || 0, icons.products, 'success');
            if (widgets.includes('pending_withdrawals')) html += StatsCard.render(window.t('Pending Withdrawals'), stats.pending_withdrawals || 0, icons.withdrawals, 'danger');

            document.getElementById('overview-stats').innerHTML = html;
            Sidebar.updateBadge('pending_returns', stats.pending_returns || 0);
            Sidebar.updateBadge('pending_withdrawals', stats.pending_withdrawals || 0);
        } catch {
            // fallback
        }
    }

    async function loadCharts() {
        try {
            const data = await API.get('/admin-api/charts/');
            if (data && data.revenue_labels) {
                if (document.getElementById('chart-revenue')) Charts.line('chart-revenue', data.revenue_labels, [{ label: 'Revenue', data: data.revenue_data }]);
                if (document.getElementById('chart-orders-status')) Charts.doughnut('chart-orders-status', (data.status_labels || ['Created', 'Delivered', 'Cancelled']).map(l => window.t(l)), data.status_data || [0, 0, 0]);
            } else {
                if (document.getElementById('chart-revenue')) Charts.line('chart-revenue', ['Jan', 'Feb', 'Mar', 'Apr', 'May'], [{ label: 'Revenue', data: [0, 0, 0, 0, 0] }]);
                if (document.getElementById('chart-orders-status')) Charts.doughnut('chart-orders-status', [window.t('No Data')], [1]);
            }
        } catch {
            if (document.getElementById('chart-revenue')) Charts.line('chart-revenue', ['Jan', 'Feb', 'Mar', 'Apr', 'May'], [{ label: 'Revenue', data: [0, 0, 0, 0, 0] }]);
            if (document.getElementById('chart-orders-status')) Charts.doughnut('chart-orders-status', [window.t('No Data')], [1]);
        }
    }

    async function loadRecentOrders() {
        try {
            const orders = await API.get('/admin-api/orders/');
            const recent = (orders || []).slice(0, 5);
            const el = document.getElementById('recent-orders-table'); if (!el) return;
            if (recent.length === 0) {
                el.innerHTML = `<div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-border);margin-bottom:12px;">
                    <circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
                <h3 style="margin-bottom:4px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">No orders yet</h3>
                <p style="color:var(--clr-text-muted);font-size:var(--fs-xs);">When users place orders, they will appear here.</p>
            </div>`; return;
            }
            el.innerHTML = `<table class="data-table"><thead><tr><th>${window.t('Order #')}</th><th>${window.t('Customer')}</th><th>${window.t('Status')}</th><th>${window.t('Amount')}</th></tr></thead><tbody>` +
                recent.map(o => `<tr>
                    <td style="font-family:var(--font-mono);font-size:var(--fs-xs)">${o.order_number || o.id?.slice(0, 8)}</td>
                    <td style="font-size:var(--fs-xs)">${o.user_email || '—'}</td>
                    <td>${statusBadge(o.status)}</td>
                    <td>EGP ${parseFloat(o.final_amount || o.total_amount || 0).toLocaleString()}</td>
                </tr>`).join('') +
                '</tbody></table>';
        } catch { document.getElementById('recent-orders-table').innerHTML = `<p style="text-align:center;color:var(--clr-text-muted);padding:var(--space-8)">${window.t('Could not load orders')}</p>`; }
    }

    async function loadRecentActivity() {
        try {
            const logs = await API.get('/admin-api/recent-activity/');
            const el = document.getElementById('recent-activity-list'); if (!el) return;
            if (!logs || logs.length === 0) {
                el.innerHTML = `<div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-border);margin-bottom:12px;">
                    <circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
                <h3 style="margin-bottom:4px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">No recent activity</h3>
                <p style="color:var(--clr-text-muted);font-size:var(--fs-xs);">System logs and activities will appear here.</p>
            </div>`; return;
            }
            el.innerHTML = logs.map(l => {
                const date = new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                return `<div style="display:flex; gap:12px; padding:var(--space-3) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <div style="width:8px; height:8px; border-radius:50%; background:var(--clr-primary); margin-top:6px;"></div>
                    <div style="flex:1;">
                        <div style="font-size:var(--fs-sm); font-weight:var(--fw-medium); color:var(--clr-text);">${l.action}</div>
                        <div style="font-size:var(--fs-xs); color:var(--clr-text-muted); display:flex; justify-content:space-between;">
                            <span>${l.actor}</span>
                            <span>${date}</span>
                        </div>
                    </div>
                </div>`;
            }).join('');
        } catch {
            document.getElementById('recent-activity-list').innerHTML = `<p style="text-align:center;color:var(--clr-text-muted);padding:var(--space-8)">${window.t('Failed to load activity')}</p>`;
        }
    }

    async function loadTopProducts() {
        try {
            const products = await API.get('/admin-api/top-products/');
            const el = document.getElementById('top-products-table'); if (!el) return;
            if (!products || products.length === 0) {
                el.innerHTML = `<div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-border);margin-bottom:12px;">
                    <circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
                <h3 style="margin-bottom:4px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">No product data</h3>
                <p style="color:var(--clr-text-muted);font-size:var(--fs-xs);">Top selling products will be listed here.</p>
            </div>`; return;
            }
            el.innerHTML = `<table class="data-table"><thead><tr><th>${window.t('Product')}</th><th>${window.t('Units Sold')}</th><th>${window.t('Revenue')}</th></tr></thead><tbody>` +
                products.map(p => `<tr onclick="window.viewOverviewProduct(${p.id})" style="cursor:pointer" title="${window.t('View Product')}">
                    <td>
                        <div style="font-weight:var(--fw-medium); font-size:var(--fs-sm);">${p.name}</div>
                        <div style="font-size:var(--fs-xs); color:var(--clr-text-muted);">${p.category || ''}</div>
                    </td>
                    <td><span class="badge badge-neutral">${p.total_sold}</span></td>
                    <td style="font-weight:var(--fw-semibold); color:var(--clr-success);">EGP ${parseFloat(p.total_revenue || 0).toLocaleString()}</td>
                </tr>`).join('') +
                '</tbody></table>';
        } catch {
            document.getElementById('top-products-table').innerHTML = `<p style="text-align:center;color:var(--clr-text-muted);padding:var(--space-8)">${window.t('Failed to load top products')}</p>`;
        }
    }

    window.viewOverviewProduct = async function(id) {
        try {
            const btn = event.currentTarget;
            btn.style.opacity = '0.5';
            const products = await API.get('/admin-api/products/');
            const p = products.find(x => x.id === id || x.ProductID === id);
            btn.style.opacity = '1';
            if (p) DataTable.showRowDetails(p, window.t("Product Details"));
            else window.Toast && window.Toast.error("Product not found");
        } catch(e) {
            window.Toast && window.Toast.error(e.message);
        }
    };

    async function loadPendingReturns() {
        try {
            const data = await API.get('/admin-api/returns/');
            const returns = (data || []).filter(r => r.status === 'new').slice(0, 5);
            const el = document.getElementById('pending-returns-list'); if (!el) return;
            if (returns.length === 0) {
                el.innerHTML = `<div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-success);margin-bottom:12px;">
                    <circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
                <h3 style="margin-bottom:4px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">No pending returns</h3>
                <p style="color:var(--clr-text-muted);font-size:var(--fs-xs);">All caught up on return requests. Great job!</p>
            </div>`; return;
            }
            el.innerHTML = returns.map(r => `<div style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-3) 0;border-bottom:1px solid var(--clr-surface-border)">
                <div><div style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">${r.product_name || window.t('Product')}</div><div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${r.reason || ''}</div></div>
                <span class="badge badge-warning">EGP ${parseFloat(r.amount || 0).toFixed(2)}</span>
            </div>`).join('');
        } catch { document.getElementById('pending-returns-list').innerHTML = `<p style="text-align:center;color:var(--clr-text-muted);padding:var(--space-8)">${window.t('Could not load returns')}</p>`; }
    }

    function statusBadge(s) {
        const map = { created: 'info', ready_to_ship: 'primary', 'on my way': 'warning', 'delivered successfully': 'success', cancelled: 'danger', 'failed delivery': 'danger' };
        return `<span class="badge badge-${map[s] || 'neutral'} badge-dot">${window.t((s || 'unknown').replace(/_/g, ' '))}</span>`;
    }

    return { render, stopAutoRefresh };
})();
