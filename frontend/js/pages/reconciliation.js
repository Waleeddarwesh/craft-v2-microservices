window.ReconciliationPage = async function(container) {
    const html = `
        <div class="page-header">
            <div>
                <h1 class="page-title">${window.t('Financial Reconciliation')}</h1>
                <p class="page-subtitle">${window.t('Compare Stripe payments, total orders, internal income, and supplier balances.')}</p>
            </div>
            <div class="page-actions">
                <button class="btn btn-outline" onclick="ReconciliationPage.load()">${window.t('Refresh Data')}</button>
            </div>
        </div>

        <div id="reconciliation-content">
            <div class="text-center py-4">${window.t('Loading reconciliation data...')}</div>
        </div>
    `;
    
    container.innerHTML = html;

    window.ReconciliationPage.load = async () => {
        try {
            const data = await API.get('/admin-api/finance/reconciliation/');
            
            const content = document.getElementById('reconciliation-content');
            
            let statusBanner = '';
            if (data.status === 'Healthy') {
                statusBanner = `
                    <div class="kpi-card" style="border: 1px solid var(--clr-success); background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, transparent 100%); margin-bottom: var(--space-6);">
                        <div class="d-flex align-items-center gap-4">
                            <div class="avatar" style="width: 48px; height: 48px; background: var(--clr-success-bg); color: var(--clr-success);">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                            </div>
                            <div>
                                <h3 class="text-success m-0 font-bold" style="font-size: var(--fs-lg);">${window.t('Ledger is Balanced')}</h3>
                                <p class="text-muted m-0" style="font-size: var(--fs-sm);">${window.t('No Discrepancies Detected. Your finances are in perfect sync.')}</p>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                statusBanner = `
                    <div class="kpi-card" style="border: 1px solid var(--clr-danger); background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, transparent 100%); margin-bottom: var(--space-6);">
                        <div class="d-flex align-items-center gap-4">
                            <div class="avatar" style="width: 48px; height: 48px; background: var(--clr-danger-bg); color: var(--clr-danger);">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                            </div>
                            <div>
                                <h3 class="text-danger m-0 font-bold" style="font-size: var(--fs-lg);">${window.t('Discrepancy Detected!')}</h3>
                                <p class="text-muted m-0" style="font-size: var(--fs-sm);">${window.t('Review the ledger immediately. There is a mismatch between your internal data and external payment gateways.')}</p>
                            </div>
                        </div>
                    </div>
                `;
            }

            content.innerHTML = `
                ${statusBanner}
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: var(--space-6);">
                    <!-- Stripe vs Orders -->
                    <div class="card p-5" style="border-radius: var(--radius-xl); background: linear-gradient(145deg, var(--clr-surface), transparent); border: 1px solid var(--glass-border); box-shadow: var(--shadow-lg); position: relative; overflow: hidden; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'; this.style.borderColor='var(--clr-primary-glow)'" onmouseout="this.style.transform='none'; this.style.borderColor='var(--glass-border)'">
                        <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: radial-gradient(circle, var(--clr-primary-glow) 0%, transparent 60%); opacity: 0.1; pointer-events: none;"></div>
                        <h3 class="font-medium mb-4 d-flex align-items-center gap-2" style="font-size: var(--fs-lg)">
                            <div class="avatar avatar-sm" style="background: var(--clr-primary-glow); color: var(--clr-primary);"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg></div>
                            ${window.t('External vs Internal Revenue')}
                        </h3>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Captured via Stripe')}</span>
                            <strong class="text-success" style="font-size: var(--fs-lg);">$${data.total_stripe_captured.toFixed(2)}</strong>
                        </div>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Platform Order Value')}</span>
                            <strong style="font-size: var(--fs-lg);">$${data.total_order_value.toFixed(2)}</strong>
                        </div>
                        <hr class="my-4" style="border-color: var(--glass-border);">
                        <div class="d-flex justify-content-between align-items-center p-3" style="background: ${Math.abs(data.stripe_discrepancy) > 1 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)'}; border: 1px solid ${Math.abs(data.stripe_discrepancy) > 1 ? 'var(--clr-danger)' : 'var(--clr-success)'}; border-radius: var(--radius-md);">
                            <span class="font-medium">${window.t('Stripe Discrepancy')}</span>
                            <strong class="${Math.abs(data.stripe_discrepancy) > 1 ? 'text-danger' : 'text-success'}" style="font-size: var(--fs-xl);">
                                $${data.stripe_discrepancy.toFixed(2)}
                            </strong>
                        </div>
                        <p class="text-xs text-muted mt-2">${window.t('Checks if the money captured by Stripe matches the internal transaction ledger.')}</p>
                    </div>

                    <!-- Internal Ledger -->
                    <div class="card p-5" style="border-radius: var(--radius-xl); background: linear-gradient(145deg, var(--clr-surface), transparent); border: 1px solid var(--glass-border); box-shadow: var(--shadow-lg); position: relative; overflow: hidden; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'; this.style.borderColor='var(--clr-primary-glow)'" onmouseout="this.style.transform='none'; this.style.borderColor='var(--glass-border)'">
                        <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: radial-gradient(circle, var(--clr-info-bg) 0%, transparent 60%); opacity: 0.3; pointer-events: none;"></div>
                        <h3 class="font-medium mb-4 d-flex align-items-center gap-2" style="font-size: var(--fs-lg)">
                            <div class="avatar avatar-sm" style="background: var(--clr-info-bg); color: var(--clr-info);"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"></path><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path></svg></div>
                            ${window.t('Internal Ledger vs Balances')}
                        </h3>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Transaction Income')}</span>
                            <strong class="text-success" style="font-size: var(--fs-lg);">$${data.total_internal_income.toFixed(2)}</strong>
                        </div>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Transaction Outcome (Debits)')}</span>
                            <strong class="text-danger" style="font-size: var(--fs-lg);">-$${data.total_internal_outcome.toFixed(2)}</strong>
                        </div>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Completed Withdrawals')}</span>
                            <strong class="text-info" style="font-size: var(--fs-lg);">-$${data.total_withdrawals.toFixed(2)}</strong>
                        </div>
                        <div class="d-flex justify-content-between align-items-center p-3 mb-3" style="background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                            <span class="text-muted" style="font-size: var(--fs-sm);">${window.t('Total Supplier/User Balances')}</span>
                            <strong class="text-primary" style="font-size: var(--fs-lg);">$${data.total_user_balances.toFixed(2)}</strong>
                        </div>
                        <hr class="my-4" style="border-color: var(--glass-border);">
                        <div class="d-flex justify-content-between align-items-center p-3" style="background: ${Math.abs(data.internal_discrepancy) > 1 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)'}; border: 1px solid ${Math.abs(data.internal_discrepancy) > 1 ? 'var(--clr-danger)' : 'var(--clr-success)'}; border-radius: var(--radius-md);">
                            <span class="font-medium">${window.t('Ledger Discrepancy')}</span>
                            <strong class="${Math.abs(data.internal_discrepancy) > 1 ? 'text-danger' : 'text-success'}" style="font-size: var(--fs-xl);">
                                $${data.internal_discrepancy.toFixed(2)}
                            </strong>
                        </div>
                        <p class="text-xs text-muted mt-2">${window.t('Formula: Income - Outcome - User Balances = 0.')}</p>
                    </div>
                </div>
            `;
        } catch (err) {
            window.Toast.show('Error loading reconciliation data', 'error');
            console.error(err);
        }
    };

    await window.ReconciliationPage.load();
};
Router.register('reconciliation', window.ReconciliationPage);
