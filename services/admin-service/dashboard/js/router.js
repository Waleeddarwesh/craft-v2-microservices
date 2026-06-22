/* =============================================================================
   Client-Side Hash Router
   ============================================================================= */
const Router = (() => {
    const routes = {};
    let currentPage = null;

    function register(hash, handler) {
        routes[hash] = handler;
    }

    function navigate(hash) {
        window.location.hash = hash;
    }

    function getCurrentRoute() {
        return window.location.hash.slice(1) || 'overview';
    }

    async function handleRoute() {
        const route = getCurrentRoute();
        const handler = routes[route];
        const content = document.getElementById('main-content');
        const titles = {
            overview: 'Dashboard', tasks: 'My Tasks', approvals: 'Pending Approvals',
            orders: 'Orders', returns: 'Return Requests',
            products: 'Products', users: 'Users', payments: 'Payments',
            withdrawals: 'Withdrawals', courses: 'Courses', reviews: 'Reviews',
            coupons: 'Coupons', reports: 'Reports', notifications: 'Notifications',
            'support-tickets': 'Support Tickets', disputes: 'Disputes',
            'supplier-performance': 'Supplier Performance', 'delivery-performance': 'Delivery Performance',
            'fraud-alerts': 'Fraud Alerts', 'product-moderation': 'Product Moderation',
            reconciliation: 'Financial Reconciliation',
            'audit-logs': 'Audit Logs', settings: 'Settings',
            'system-health': 'System Health',
            servers: 'Servers Inventory',
            services: 'Services Registry',
            'users-linux': 'Linux User Administration',
            'system-logs': 'System Logs',
            storage: 'Storage Administration',
            backups: 'Backup & Recovery',
            'cron-jobs': 'Cron Job Administration',
            'security-center': 'Security Center',
            'config-management': 'Configuration Management',
            'file-explorer': 'File Explorer',
            containers: 'Container Operations',
            incidents: 'Incident Management',
            automation: 'Operational Scripts'
        };
        
        let breadcrumbHtml = '';
        const pageTitle = titles[route] || route;
        
        if (route !== 'overview') {
            breadcrumbHtml = `
                <div class="breadcrumbs" style="font-size:var(--fs-xs); color:var(--clr-text-muted); margin-bottom:var(--space-4); display:flex; gap:var(--space-2); align-items:center;">
                    <a href="#overview" style="color:var(--clr-primary); text-decoration:none;" onclick="Router.navigate('#overview');return false;">${window.t('Dashboard')}</a>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                    <span>${window.t(pageTitle)}</span>
                </div>
            `;
        }

        if (!handler) {
            content.innerHTML = `${breadcrumbHtml}<div class="empty-state"><h3>${window.t('Page not found')}</h3><p>${window.t('The page')} "${window.t(route)}" ${window.t('does not exist.')}</p></div>`;
            return;
        }
        
        if (window.UserIdentity) {
            const authorizedModules = window.UserIdentity.modules.map(m => m.key);
            if (!authorizedModules.includes(route)) {
                content.innerHTML = `${breadcrumbHtml}<div class="empty-state"><h3>${window.t('Access Denied')}</h3><p>${window.t('You do not have permission to view the')} "${window.t(pageTitle)}" ${window.t('module.')}</p></div>`;
                return;
            }
        }

        // Clean up page specific intervals/timers
        if (window.OverviewPage && window.OverviewPage.stopAutoRefresh) {
            window.OverviewPage.stopAutoRefresh();
        }

        // Show loading
        content.innerHTML = `<div class="page-loader"><div class="spinner spinner-lg"></div><p>${window.t('Loading...')}</p></div>`;
        content.style.opacity = '0';

        // Update sidebar active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.route === route);
        });

        document.title = `Craft Dashboard — ${pageTitle}`;

        try {
            // Setup a wrapper for the page content, insert breadcrumbs before it
            content.innerHTML = `${breadcrumbHtml}<div id="page-content-wrapper"></div>`;
            await handler(document.getElementById('page-content-wrapper'));
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><h3>${window.t('Error loading page')}</h3><p>${err.message}</p></div>`;
            console.error('Route error:', err);
        }

        // Animate in
        requestAnimationFrame(() => {
            content.style.transition = 'opacity 0.3s ease';
            content.style.opacity = '1';
        });
        currentPage = route;
    }

    function init() {
        if (window.ShortcutsManager) window.ShortcutsManager.init();
        window.addEventListener('hashchange', handleRoute);
        if (!window.location.hash || window.location.hash === '#') {
            window.location.hash = '#overview';
            // hashchange fires automatically since we changed the hash
        } else {
            // Hash already set (e.g. page refresh on #orders) — hashchange won't fire
            handleRoute();
        }
    }

    return { register, navigate, getCurrentRoute, init, handleRoute };
})();
