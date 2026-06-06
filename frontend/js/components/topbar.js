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
        const user = Auth.getUser() || { full_name: 'Admin', email: 'admin@craft.com' };
        const initials = user.full_name ? user.full_name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase() : 'A';
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
                            <div class="topbar-profile-name">${user.full_name || 'Admin'}</div>
                            <div class="topbar-profile-role">${window.t('Administrator')}</div>
                        </div>
                        <div class="avatar">${initials}</div>
                    </div>
                    <div class="dropdown-menu">
                        <div class="dropdown-item" onclick="Router.navigate('#reports')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                            ${window.t('Reports')}
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
    }
    return { render };
})();
