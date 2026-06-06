/* Settings Page */
const SettingsPage = (() => {
    function render(container) {
        const env = (window.UserIdentity && window.UserIdentity.environment) ? window.UserIdentity.environment : 'Production';
        const envClass = env.toLowerCase() === 'development' ? 'badge-warning' : 'badge-success';

        container.innerHTML = `
            <div class="page-header">
                <div><h1>${window.t('Settings')}</h1><p>${window.t('System configuration and preferences')}</p></div>
            </div>
            
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:var(--space-6);">
                
                <!-- Preferences -->
                <div class="card">
                    <div class="card-header"><span class="card-title">${window.t('Preferences')}</span></div>
                    <div class="card-body">
                        <div class="form-group mb-4">
                            <label class="form-label">${window.t('Theme')}</label>
                            <div style="display:flex; gap:var(--space-2);">
                                <button class="btn btn-outline" id="btn-theme-light" onclick="SettingsPage.setTheme('light')">${ThemeManager.ICONS.sun} ${window.t('Light')}</button>
                                <button class="btn btn-outline" id="btn-theme-dark" onclick="SettingsPage.setTheme('dark')">${ThemeManager.ICONS.moon} ${window.t('Dark')}</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${window.t('Language')}</label>
                            <div style="display:flex; gap:var(--space-2);">
                                <button class="btn btn-outline ${window.I18n.getLang() === 'en' ? 'btn-primary' : ''}" onclick="window.I18n.setLang('en');window.location.reload()">${window.t('English (EN)')}</button>
                                <button class="btn btn-outline ${window.I18n.getLang() === 'ar' ? 'btn-primary' : ''}" onclick="window.I18n.setLang('ar');window.location.reload()">${window.t('Arabic (AR)')}</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- System Info -->
                <div class="card">
                    <div class="card-header"><span class="card-title">${window.t('System Information')}</span></div>
                    <div class="card-body">
                        <div class="detail-grid">
                            <div class="detail-item"><span class="detail-label">${window.t('App Version')}</span><span class="detail-value">v1.2.0</span></div>
                            <div class="detail-item"><span class="detail-label">${window.t('API Endpoint')}</span><span class="detail-value" style="font-family:var(--font-mono);font-size:var(--fs-xs)">/admin-api/</span></div>
                            <div class="detail-item"><span class="detail-label">${window.t('Environment')}</span><span class="detail-value"><span class="badge ${envClass}">${window.t(env)}</span></span></div>
                        </div>
                    </div>
                </div>

                ${(window.UserIdentity && window.UserIdentity.user.is_superuser) ? `
                <!-- Advanced / Admin Links -->
                <div class="card">
                    <div class="card-header"><span class="card-title">${window.t('Advanced')}</span></div>
                    <div class="card-body">
                        <p style="color:var(--clr-text-secondary);font-size:var(--fs-sm);margin-bottom:var(--space-4);">${window.t('Access the raw database management interface. Warning: changes here bypass dashboard validation.')}</p>
                        <a href="/admin/" target="_blank" class="btn btn-outline" style="width:100%; justify-content:center;">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                            ${window.t('Open Django Admin')}
                        </a>
                    </div>
                </div>
                ` : ''}

            </div>
        `;
        updateThemeButtons(ThemeManager.getTheme());
    }

    function setTheme(theme) {
        ThemeManager.setTheme(theme);
        updateThemeButtons(theme);
    }

    function updateThemeButtons(theme) {
        document.getElementById('btn-theme-light').className = 'btn ' + (theme === 'light' ? 'btn-primary' : 'btn-outline');
        document.getElementById('btn-theme-dark').className = 'btn ' + (theme === 'dark' ? 'btn-primary' : 'btn-outline');
    }

    return { render, setTheme };
})();
