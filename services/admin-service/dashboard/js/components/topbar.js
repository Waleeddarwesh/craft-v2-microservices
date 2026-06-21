/* Topbar Component */
const Topbar = (() => {
    let searchTimeout = null;

    async function performSearch(query) {
        const resultsContainer = document.getElementById('search-results');
        if (!query.trim()) {
            resultsContainer.style.display = 'none';
            resultsContainer.style.opacity = '0';
            resultsContainer.style.visibility = 'hidden';
            return;
        }
        try {
            const data = await API.get('/admin-api/search/', { q: query });
            const results = data.results || [];
            if (results.length === 0) {
                resultsContainer.innerHTML = `<div class="dropdown-item" style="justify-content:center;color:var(--clr-text-muted);cursor:default">${window.t('No results found')}</div>`;
            } else {
                resultsContainer.innerHTML = results.map(r => `
                    <div class="dropdown-item" onclick="Router.navigate('${r.url}'); document.getElementById('search-results').style.display='none'; document.getElementById('global-search').value='';" style="display:flex; flex-direction:column; align-items:flex-start;">
                        <div style="font-weight:var(--fw-medium); color:var(--clr-text)">${r.title}</div>
                        <div style="font-size:var(--fs-xs); color:var(--clr-text-muted)">${r.subtitle}</div>
                    </div>
                `).join('');
            }
            resultsContainer.style.display = 'block';
            resultsContainer.style.opacity = '1';
            resultsContainer.style.visibility = 'visible';
            resultsContainer.style.transform = 'translateY(0)';
        } catch (e) {
            console.error('Search failed', e);
        }
    }

    function render(container) {
        const identUser = window.UserIdentity && window.UserIdentity.user ? window.UserIdentity.user : null;
        const user = identUser || Auth.getUser() || { full_name: 'Admin', email: 'admin@craft.com', first_name: 'Admin', last_name: '' };
        const fullName = user.full_name || [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Admin';
        const initials = fullName.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
        let roleName = window.t('Administrator');
        if (identUser) {
            if (identUser.role_name) {
                roleName = identUser.role_name;
            } else if (identUser.is_superuser) roleName = window.t('Administrator');
            else if (identUser.is_supplier) roleName = window.t('Supplier');
            else if (identUser.is_delivery) roleName = window.t('Delivery Partner');
            else if (identUser.is_staff) roleName = window.t('Support Administrator');
        }

        container.innerHTML = `
            <div class="topbar-left">
                <div class="topbar-toggle" onclick="Sidebar.toggleCollapse();document.getElementById('mobile-overlay').style.display=document.getElementById('sidebar').classList.contains('mobile-open')?'block':'none'" id="sidebar-toggle">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
                </div>
                <div class="topbar-search" style="position:relative;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <input type="text" placeholder="${window.t('Search orders, users, products...')}" id="global-search" autocomplete="off">
                    <div id="search-results" class="dropdown-menu" style="display:none; position:absolute; top:100%; left:0; width:300px; max-height:400px; overflow-y:auto; margin-top:8px; z-index:100;"></div>
                </div>
            </div>
            <div class="topbar-right">
                <div class="topbar-btn" onclick="window.I18n.toggle()" title="Toggle Language">
                    <span style="font-weight:bold;font-size:12px;letter-spacing:1px">${window.I18n ? (window.I18n.getLang() === 'ar' ? 'EN' : 'AR') : 'AR'}</span>
                </div>
                <div class="theme-toggle" id="theme-toggle-btn" onclick="ThemeManager.toggle()" title="Toggle Theme">
                    ${ThemeManager.ICONS.sun}
                </div>
                <div class="topbar-btn" onclick="Router.navigate('#notifications')" title="Notifications">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
                    <span class="notif-dot" id="notif-dot" style="display:none"></span>
                </div>
                <div class="dropdown" id="profile-dropdown">
                    <div class="topbar-profile" onclick="document.getElementById('profile-dropdown').classList.toggle('open')">
                        <div class="topbar-profile-info">
                            <div class="topbar-profile-name">${fullName}</div>
                            <div class="topbar-profile-role">${roleName}</div>
                        </div>
                        <div class="avatar" style="overflow:hidden">${user.profile_picture ? `<img src="${user.profile_picture}" style="width:100%;height:100%;object-fit:cover;">` : initials}</div>
                    </div>
                    <div class="dropdown-menu">
                        <div style="padding: 12px 16px; border-bottom: 1px solid var(--clr-border); display: flex; align-items: center; gap: 12px;">
                            <div class="avatar" style="width: 40px; height: 40px; flex-shrink: 0; overflow:hidden">${user.profile_picture ? `<img src="${user.profile_picture}" style="width:100%;height:100%;object-fit:cover;">` : initials}</div>
                            <div style="overflow: hidden;">
                                <div style="font-size: 14px; font-weight: 600; color: var(--clr-text); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${fullName}</div>
                                <div style="font-size: 12px; color: var(--clr-text-muted); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${user.email || 'admin@craft.com'}</div>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="Router.navigate('#reports')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                            ${window.t('Reports')}
                        </div>
                        <div class="dropdown-item" onclick="window.location.href='/admin/profile-settings/'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                            ${window.t('Account Settings')}
                        </div>
                        <div class="dropdown-item" onclick="window.location.href='/developer/'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                            ${window.t('Developer Portal')}
                        </div>
                        <div class="dropdown-divider"></div>
                        <div class="dropdown-item" onclick="Auth.logout()" style="color:var(--clr-danger)">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                            ${window.t('Sign Out')}
                        </div>
                    </div>
                </div>
            </div>`;
        
        // Setup Search listener
        const searchInput = document.getElementById('global-search');
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => performSearch(e.target.value), 300);
        });

        // Close dropdowns on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#profile-dropdown')) {
                document.getElementById('profile-dropdown')?.classList.remove('open');
            }
            if (!e.target.closest('.topbar-search')) {
                const sr = document.getElementById('search-results');
                if (sr) {
                    sr.style.display = 'none';
                    sr.style.opacity = '0';
                    sr.style.visibility = 'hidden';
                }
            }
        });
        // Mobile toggle behavior
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                const sb = document.getElementById('sidebar');
                sb.classList.toggle('mobile-open');
                document.getElementById('mobile-overlay').style.display = sb.classList.contains('mobile-open') ? 'block' : 'none';
            }
        });
        // Set correct theme toggle icon for current theme
        ThemeManager.updateToggleIcon(ThemeManager.getTheme());
        // Fetch unread notifications logic
        async function updateNotifications() {
            try {
                // Since this is the Dashboard, use admin-api proxy
                const res = await API.get('/admin-api/notifications/');
                const unreadCount = res.filter(n => !n.is_read).length;
                const dot = document.getElementById('notif-dot');
                if (dot) {
                    dot.style.display = unreadCount > 0 ? 'inline-block' : 'none';
                    dot.textContent = unreadCount > 9 ? '9+' : (unreadCount > 0 ? unreadCount : '');
                }
            } catch (e) {
                console.error("Failed to fetch notifications:", e);
            }
        }
        
        // Initial fetch
        updateNotifications();
        
        // Optional: Poll every 30 seconds
        setInterval(updateNotifications, 30000);

    }
    return { render };
})();
