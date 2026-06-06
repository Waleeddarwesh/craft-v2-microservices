/* Financial Reports Page */
const ReportsPage = (() => {
    let currentPeriod = 'this_month';

    async function render(container) {
        container.innerHTML = `
            <div class="page-header">
                <div><h1>${window.t('Financial Reports')}</h1><p>${window.t('Revenue analytics and earning breakdowns')}</p></div>
                <div style="display:flex; gap:var(--space-2); align-items:center;">
                    <div class="report-period-selector">
                        <button class="period-btn active" data-period="this_day" onclick="ReportsPage.setPeriod('this_day')">${window.t('Today')}</button>
                        <button class="period-btn" data-period="this_month" onclick="ReportsPage.setPeriod('this_month')">${window.t('This Month')}</button>
                        <button class="period-btn" data-period="this_year" onclick="ReportsPage.setPeriod('this_year')">${window.t('This Year')}</button>
                        <button class="period-btn" data-period="custom" onclick="ReportsPage.setPeriod('custom')">${window.t('Custom')}</button>
                    </div>
                    <button class="btn btn-primary" onclick="window.print()">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
                        ${window.t('Print / PDF')}
                    </button>
                </div>
            </div>    <div id="custom-date-range" style="display:none; gap:var(--space-2); margin-top:var(--space-2); align-items:center;">
                    <input type="date" id="report-date-start" class="form-input" style="width:140px">
                    <span style="color:var(--clr-text-muted)">${window.t('to')}</span>
                    <input type="date" id="report-date-end" class="form-input" style="width:140px">
                    <button class="btn btn-primary btn-sm" onclick="ReportsPage.loadReport()">${window.t('Apply')}</button>
                </div>
            <div class="report-kpi-grid" id="report-kpis">
                ${Array(3).fill('<div class="skeleton skeleton-card"></div>').join('')}
            </div>
            <div id="quick-stats-bar" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:var(--space-4); margin-bottom:var(--space-6); background:var(--clr-surface); padding:var(--space-4); border-radius:var(--radius-lg); border:1px solid var(--clr-surface-border); text-align:center;">
                <div><div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${window.t('Total Customers')}</div><div id="qs-customers" style="font-size:var(--fs-lg);font-weight:var(--fw-bold)">-</div></div>
                <div style="border-left:1px solid var(--clr-surface-border); border-right:1px solid var(--clr-surface-border)"><div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${window.t('Total Products')}</div><div id="qs-products" style="font-size:var(--fs-lg);font-weight:var(--fw-bold)">-</div></div>
                <div><div style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${window.t('Avg Product Rating')}</div><div id="qs-rating" style="font-size:var(--fs-lg);font-weight:var(--fw-bold)">-</div></div>
            </div>
            <div style="display:grid; grid-template-columns: 2fr 1fr; gap:var(--space-6);">
                <div class="card mb-6"><div class="card-header"><span class="card-title">${window.t('Income vs Outcome')}</span></div><div class="chart-container lg"><canvas id="chart-earnings"></canvas></div></div>
                <div class="card mb-6"><div class="card-header"><span class="card-title">${window.t('Payment Methods')}</span></div><div class="chart-container lg"><canvas id="chart-payments"></canvas></div></div>
            </div>`;
        currentPeriod = 'this_month';
        document.querySelector('[data-period="this_month"]')?.classList.add('active');
        document.querySelector('[data-period="this_day"]')?.classList.remove('active');
        loadReport();
    }

    function setPeriod(p) {
        currentPeriod = p;
        document.querySelectorAll('.period-btn').forEach(b => b.classList.toggle('active', b.dataset.period === p));
        
        if (p === 'custom') {
            document.getElementById('custom-date-range').style.display = 'flex';
        } else {
            document.getElementById('custom-date-range').style.display = 'none';
            loadReport();
        }
    }

    async function loadReport() {
        try {
            document.getElementById('report-kpis').innerHTML = Array(3).fill('<div class="skeleton skeleton-card"></div>').join('');
            
            let qs = `?period=${currentPeriod}`;
            if (currentPeriod === 'custom') {
                const start = document.getElementById('report-date-start').value;
                const end = document.getElementById('report-date-end').value;
                if (!start || !end) {
                    Toast.error('Please select both start and end dates');
                    return;
                }
                qs += `&start_date=${start}&end_date=${end}`;
            }
            
            const data = await API.get('/admin-api/reports/' + qs);
            const inc = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>';
            const out = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>';
            const earn = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>';

            document.getElementById('report-kpis').innerHTML =
                StatsCard.render(window.t('Total Income'), `EGP ${parseFloat(data.total_income || 0).toLocaleString()}`, inc, 'success') +
                StatsCard.render(window.t('Total Outcome'), `EGP ${parseFloat(data.total_outcome || 0).toLocaleString()}`, out, 'danger') +
                StatsCard.render(window.t('Net Earnings'), `EGP ${parseFloat(data.total_earning || 0).toLocaleString()}`, earn, 'accent', data.percentage_change);

            const graphData = data.graph_data || [];
            if (graphData.length > 0) {
                Charts.bar('chart-earnings', graphData.map(g => g.month || g.date || ''), [
                    { label: window.t('Income'), data: graphData.map(g => g.income || 0) },
                    { label: window.t('Outcome'), data: graphData.map(g => g.outcome || 0) }
                ]);
            } else {
                Charts.bar('chart-earnings', [window.t('No Data')], [{ label: window.t('Income'), data: [0] }, { label: window.t('Outcome'), data: [0] }]);
            }
            
            if (data.payment_methods) {
                Charts.doughnut('chart-payments', data.payment_methods.labels, data.payment_methods.data);
            }
            
            if (data.quick_stats) {
                document.getElementById('qs-customers').textContent = data.quick_stats.customers.toLocaleString();
                document.getElementById('qs-products').textContent = data.quick_stats.products.toLocaleString();
                document.getElementById('qs-rating').textContent = `⭐ ${data.quick_stats.avg_rating}`;
            }
        } catch(e) {
            document.getElementById('report-kpis').innerHTML =
                StatsCard.render(window.t('Total Income'), 'EGP 0', '', 'success') +
                StatsCard.render(window.t('Total Outcome'), 'EGP 0', '', 'danger') +
                StatsCard.render(window.t('Net Earnings'), 'EGP 0', '', 'accent');
            Charts.bar('chart-earnings', [window.t('No Data')], [{ label: window.t('Income'), data: [0] }]);
        }
    }

    return { render, setPeriod, loadReport };
})();
