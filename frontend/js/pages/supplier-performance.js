window.SupplierPerformancePage = async function(container) {
    const html = `
        <div class="page-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
            <div>
                <h1>${window.t('Supplier Performance')}</h1>
                <p style="color:var(--clr-text-muted);">${window.t('Monitor operational scores, returns, and ratings for all suppliers.')}</p>
            </div>
            <div class="page-header-actions">
                <button class="btn btn-outline" onclick="SupplierPerformancePage.load()">${window.t('Refresh')}</button>
            </div>
        </div>

        <div class="overview-grid" id="supplier-kpi-container" style="display: none; margin-bottom: 32px;">
            ${StatsCard.render(window.t('Total Suppliers'), '<span id="kpi-total-suppliers">0</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>', 'primary')}
            ${StatsCard.render(window.t('Avg Score'), '<span id="kpi-avg-score">0</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>', 'info')}
            ${StatsCard.render(window.t('Total Orders'), '<span id="kpi-total-orders">0</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>', 'success')}
        </div>

        <div id="supplier-perf-table-container"></div>
    `;
    
    container.innerHTML = html;

    window.SupplierPerformancePage.load = async () => {
        try {
            const data = await API.get('/admin-api/performance/suppliers/');
            
            if (data && data.length > 0) {
                document.getElementById('supplier-kpi-container').style.display = 'grid';
                document.getElementById('kpi-total-suppliers').innerText = data.length;
                const avgScore = data.reduce((sum, s) => sum + parseFloat(s.performance_score || 0), 0) / data.length;
                document.getElementById('kpi-avg-score').innerText = avgScore.toFixed(1);
                document.getElementById('kpi-total-orders').innerText = data.reduce((sum, s) => sum + parseInt(s.total_orders || 0), 0);
            }
            
            DataTable.render('supplier-perf-table-container', {
                columns: [
                    { key: 'supplier_name', label: 'Supplier', render: (v, r) => `
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div class="avatar bg-primary text-white" style="width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;">${v.charAt(0)}</div>
                            <div>
                                <div style="font-weight:var(--fw-medium)">${v}</div>
                                <div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${r.email}</div>
                            </div>
                        </div>` 
                    },
                    { key: 'category', label: 'Category', render: v => window.t(v || '-') },
                    { key: 'total_orders', label: 'Orders' },
                    { key: 'return_rate', label: 'Return Rate', render: (v, r) => `${v}% <span style="font-size:var(--fs-xs);color:var(--clr-text-muted)">(${r.returns_count})</span>` },
                    { key: 'success_rate', label: 'Success Rate', render: v => `${v}%` },
                    { key: 'rating', label: 'Rating', render: v => `
                        <div style="display:flex; align-items:center; gap:4px">
                            <span style="color:var(--clr-warning)">★</span>
                            <span>${v}</span>
                        </div>` 
                    },
                    { key: 'performance_score', label: 'Score', render: v => `<strong>${v}</strong>` },
                    { key: 'status', label: 'Status', render: v => {
                        let bc = 'badge-success';
                        if (v === 'Warning') bc = 'badge-warning';
                        if (v === 'High Risk') bc = 'badge-danger';
                        if (v === 'New') bc = 'badge-info';
                        return `<span class="badge ${bc}">${window.t(v)}</span>`;
                    }}
                ],
                data: data,
                pageSize: 10
            });
        } catch (err) {
            window.Toast.show('Error loading supplier performance data', 'error');
            console.error(err);
        }
    };

    await window.SupplierPerformancePage.load();
};
Router.register('supplier-performance', window.SupplierPerformancePage);
