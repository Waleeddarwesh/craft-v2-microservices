window.FraudAlertsPage = async function(container) {
    const html = `
        <div class="page-header">
            <div>
                <h1 class="page-title">${window.t('Fraud Detection Engine')}</h1>
                <p class="page-subtitle">${window.t('Review and manage suspicious account activities.')}</p>
            </div>
            <div class="page-actions">
                <button class="btn btn-outline" onclick="FraudAlertsPage.load()">${window.t('Refresh Alerts')}</button>
            </div>
        </div>

        <div class="kpi-row" id="fraud-kpi-container" style="display: none;">
            <div class="kpi-card">
                <div class="kpi-label"><div class="kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg></div> ${window.t('Total Alerts')}</div>
                <div class="kpi-value" id="kpi-total-alerts">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><div class="kpi-icon text-danger"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div> ${window.t('High Risk')}</div>
                <div class="kpi-value text-danger" id="kpi-high-risk">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><div class="kpi-icon text-warning"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg></div> ${window.t('Pending Review')}</div>
                <div class="kpi-value text-warning" id="kpi-pending">0</div>
            </div>
        </div>

        <div class="premium-table-wrapper">
            <div class="table-responsive">
                <table class="premium-table" id="fraud-alerts-table">
                    <thead>
                        <tr>
                            <th>${window.t('Alert ID')}</th>
                            <th>${window.t('User / Email')}</th>
                            <th>${window.t('Trigger Reason')}</th>
                            <th>${window.t('Risk Score')}</th>
                            <th>${window.t('Status')}</th>
                            <th>${window.t('Date')}</th>
                            <th>${window.t('Actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="7" class="text-center py-4">${window.t('Loading alerts...')}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;

    window.FraudAlertsPage.load = async () => {
        try {
            const data = await API.get('/admin-api/fraud-alerts/');
            const tbody = document.querySelector('#fraud-alerts-table tbody');
            
            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">${window.t('No fraud alerts detected. System is safe.')}</td></tr>`;
                return;
            }

            document.getElementById('fraud-kpi-container').style.display = 'grid';
            document.getElementById('kpi-total-alerts').innerText = data.length;
            document.getElementById('kpi-high-risk').innerText = data.filter(d => d.risk_score >= 80).length;
            document.getElementById('kpi-pending').innerText = data.filter(d => d.status === 'pending').length;


            tbody.innerHTML = data.map(alert => {
                let badgeClass = 'badge-primary';
                if (alert.status === 'pending') badgeClass = 'badge-warning';
                else if (alert.status === 'resolved') badgeClass = 'badge-success';
                else if (alert.status === 'action_taken') badgeClass = 'badge-danger';
                
                let scoreClass = 'text-success';
                if (alert.risk_score >= 80) scoreClass = 'text-danger font-bold';
                else if (alert.risk_score >= 50) scoreClass = 'text-warning';

                return `
                    <tr style="cursor:pointer" onclick='DataTable.showRowDetails(${JSON.stringify(alert).replace(/'/g, "&apos;")}, "Fraud Alert Details")'>
                        <td>#${alert.id}</td>
                        <td>${alert.user_email}</td>
                        <td>${alert.reason}</td>
                        <td class="${scoreClass}">${alert.risk_score}/100</td>
                        <td><span class="badge ${badgeClass}">${window.t(alert.status.replace('_', ' ').toUpperCase())}</span></td>
                        <td>${new Date(alert.created_at).toLocaleDateString()}</td>
                        <td onclick="event.stopPropagation()">
                            ${alert.status === 'pending' || alert.status === 'investigating' ? `
                                <button class="btn btn-sm btn-outline text-success" onclick="FraudAlertsPage.action(${alert.id}, 'resolve')">${window.t('Resolve')}</button>
                                <button class="btn btn-sm btn-outline text-danger" onclick="FraudAlertsPage.action(${alert.id}, 'suspend_user')">${window.t('Suspend User')}</button>
                            ` : `<span class="text-muted">${window.t('No actions available')}</span>`}
                        </td>
                    </tr>
                `;
            }).join('');
        } catch (err) {
            window.Toast.show('Error loading fraud alerts', 'error');
            console.error(err);
        }
    };

    window.FraudAlertsPage.action = async (id, action) => {
        if (!confirm('Are you sure you want to perform this action?')) return;
        try {
            await API.post(`/admin-api/fraud-alerts/${id}/action/`, { action: action, notes: '' });
            window.Toast.show('Action successful', 'success');
            window.FraudAlertsPage.load();
        } catch (err) {
            window.Toast.show('Error performing action', 'error');
            console.error(err);
        }
    };

    await window.FraudAlertsPage.load();
};
Router.register('fraud-alerts', window.FraudAlertsPage);
