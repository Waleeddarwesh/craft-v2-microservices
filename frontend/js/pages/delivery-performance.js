window.DeliveryPerformancePage = async function(container) {
    const html = `
        <div class="page-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
            <div>
                <h1>${window.t('Delivery Performance')}</h1>
                <p style="color:var(--clr-text-muted);">${window.t('Monitor success rates and assignments for delivery agents.')}</p>
            </div>
            <div class="page-header-actions">
                <button class="btn btn-outline" onclick="DeliveryPerformancePage.load()">${window.t('Refresh')}</button>
            </div>
        </div>

        <div class="overview-grid" id="deliv-kpi-container" style="display: none; margin-bottom: 32px;">
            ${StatsCard.render(window.t('Total Agents'), '<span id="kpi-agents">0</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>', 'primary')}
            ${StatsCard.render(window.t('Avg Success Rate'), '<span id="kpi-success-rate">0%</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>', 'success')}
            ${StatsCard.render(window.t('Total Failures'), '<span id="kpi-failures">0</span>', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>', 'danger')}
        </div>

        <div id="delivery-perf-table-container"></div>
    `;
    
    container.innerHTML = html;

    window.DeliveryPerformancePage.load = async () => {
        try {
            const data = await API.get('/admin-api/performance/delivery/');
            if (data && data.length > 0) {
                document.getElementById('deliv-kpi-container').style.display = 'grid';
                document.getElementById('kpi-agents').innerText = data.length;
                const avgRate = data.reduce((sum, d) => sum + parseFloat(d.success_rate || 0), 0) / data.length;
                document.getElementById('kpi-success-rate').innerText = avgRate.toFixed(1) + '%';
                document.getElementById('kpi-failures').innerText = data.reduce((sum, d) => sum + parseInt(d.failed_count || 0), 0);
            }

            DataTable.render('delivery-perf-table-container', {
                columns: [
                    { key: 'delivery_name', label: 'Delivery Agent', render: (v, r) => `
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div class="avatar bg-info text-white" style="width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;">${v.charAt(0)}</div>
                            <div>
                                <div style="font-weight:var(--fw-medium)">${v}</div>
                                <div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${r.email}</div>
                            </div>
                        </div>` 
                    },
                    { key: 'area', label: 'Area', render: v => window.t(v || '-') },
                    { key: 'total_assigned', label: 'Total Assigned' },
                    { key: 'success_count', label: 'Success', render: v => `<span style="color:var(--clr-success);font-weight:var(--fw-bold);">${v}</span>` },
                    { key: 'failed_count', label: 'Failures', render: v => `<span style="color:var(--clr-danger);font-weight:var(--fw-bold);">${v}</span>` },
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
            window.Toast.show('Error loading delivery performance data', 'error');
            console.error(err);
        }
    };

    await window.DeliveryPerformancePage.load();
};
Router.register('delivery-performance', window.DeliveryPerformancePage);
