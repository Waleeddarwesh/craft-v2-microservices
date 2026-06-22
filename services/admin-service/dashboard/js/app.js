/* =============================================================================
   Craft Admin Dashboard — Main App Initialization
   ============================================================================= */
(async function() {
    // Guard: redirect to login if not authenticated
    if (!Auth.isLoggedIn()) {
        Auth.logout();
        return;
    }

    try {
        // Fetch user identity and RBAC config
        window.UserIdentity = null;
        try {
            window.UserIdentity = await API.get('/admin-api/me/');
            if (!window.UserIdentity || !window.UserIdentity.modules.length) {
                // User has no access to dashboard
                Auth.logout();
                return;
            }
        } catch (e) {
            Auth.logout();
            return;
        }

        // Render shell components
        Sidebar.render(document.getElementById('sidebar'));
        Topbar.render(document.getElementById('topbar'));

        // Check if password change is forced
        const user = Auth.getUser();
        if (user && user.must_change_password) {
            // Lock UI and force password change
            const formHtml = `
                <div id="force-password-container" style="padding: 16px;">
                    <p style="margin-bottom:16px; color:var(--clr-text-muted);">For security reasons, you must change your password before accessing the dashboard.</p>
                    <input type="password" id="force-new-pass" class="form-input" placeholder="New Password" style="margin-bottom:8px; width:100%;">
                    <input type="password" id="force-conf-pass" class="form-input" placeholder="Confirm Password" style="margin-bottom:16px; width:100%;">
                    <button class="btn btn-primary" style="width:100%" onclick="window.submitForcePasswordChange()">Update Password</button>
                </div>
            `;
            Modal.open('Mandatory Password Change', formHtml, '');
            
            // Prevent closing the modal
            const closeBtn = document.querySelector('.modal-header .btn-icon');
            if (closeBtn) closeBtn.style.display = 'none';

            window.submitForcePasswordChange = async function() {
                const new_password = document.getElementById('force-new-pass').value;
                const confirm_password = document.getElementById('force-conf-pass').value;

                if (!new_password || !confirm_password) return Toast.error('Both fields are required');
                if (new_password !== confirm_password) return Toast.error('Passwords do not match');

                try {
                    const res = await fetch(`${Auth.getApiBase()}/admin-api/me/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${Auth.getAccessToken()}`
                        },
                        body: JSON.stringify({ new_password, confirm_password })
                    });
                    
                    if (res.ok) {
                        Toast.success('Password updated successfully!');
                        user.must_change_password = false;
                        Auth.setUser(user);
                        Modal.close();
                    } else {
                        const data = await res.json();
                        Toast.error(data.message || 'Failed to update password');
                    }
                } catch (err) {
                    Toast.error('Network error. Please try again.');
                }
            };
            
            return; // Prevent loading dashboard until password is changed
        }

        // Register all page routes
        Router.register('overview', OverviewPage.render);
        Router.register('orders', OrdersPage.render);
        Router.register('returns', ReturnsPage.render);
        Router.register('products', ProductsPage.render);
        Router.register('users', UsersPage.render);
        Router.register('payments', PaymentsPage.render);
        Router.register('withdrawals', WithdrawalsPage.render);
        Router.register('courses', CoursesPage.render);
        Router.register('reviews', ReviewsPage.render);
        Router.register('coupons', CouponsPage.render);
        Router.register('reports', ReportsPage.render);
        Router.register('notifications', NotificationsPage.render);
        Router.register('support-tickets', SupportTicketsPage.render);
        Router.register('disputes', DisputesPage.render);
        Router.register('audit-logs', AuditLogsPage.render);
        Router.register('settings', SettingsPage.render);
        Router.register('api-docs', ApiDocsPage.render);
        Router.register('system-health', SystemHealthPage.render);
        Router.register('servers', window.ServersPage.render);
        Router.register('services', window.ServicesPage.render);
        Router.register('users-linux', window.UsersLinuxPage.render);
        Router.register('system-logs', window.SystemLogsPage.render);
        Router.register('storage', window.StoragePage.render);
        Router.register('backups', window.BackupsPage.render);
        Router.register('cron-jobs', window.CronJobsPage.render);
        Router.register('security-center', window.SecurityCenterPage.render);
        Router.register('config-management', window.ConfigManagementPage.render);
        Router.register('file-explorer', window.FileExplorerPage.render);
        Router.register('containers', window.ContainersPage.render);
        Router.register('incidents', window.IncidentsPage.render);
        Router.register('automation', window.AutomationPage.render);

        // Start router
        Router.init();

        // Load sidebar badge counts in background
        async function loadBadges() {
            try {
                const stats = await API.get('/admin-api/stats/');
                if (stats) {
                    Sidebar.updateBadge('pending_returns', stats.pending_returns || 0);
                    Sidebar.updateBadge('pending_withdrawals', stats.pending_withdrawals || 0);
                }
            } catch {}
        }
        loadBadges();
    } catch (criticalError) {
        document.getElementById('main-content').innerHTML = `
            <div style="padding: 40px; color: red; text-align: left;">
                <h2>Critical Dashboard Error</h2>
                <pre style="white-space: pre-wrap; font-size: 14px;">${criticalError.stack || criticalError.message}</pre>
            </div>
        `;
    }
})();
