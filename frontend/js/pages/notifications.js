/* Notifications Page */
const NotificationsPage = (() => {
    let currentTab = 'all';
    let allNotifications = [];

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Notifications')}</h1><p>${window.t('System notifications and alerts')}</p></div>
                <div class="page-header-actions" style="display:flex; gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="NotificationsPage.openSendModal()">${window.t('Send Notification')}</button>
                    <button class="btn btn-sm btn-ghost" onclick="NotificationsPage.markAllRead()">${window.t('Mark all read')}</button>
                </div>
            </div>
            <div class="tabs">
                <div class="tab active" data-tab="all" onclick="NotificationsPage.switchTab('all')">${window.t('All')}</div>
                <div class="tab" data-tab="unread" onclick="NotificationsPage.switchTab('unread')">${window.t('Unread')}</div>
            </div>
            <div id="notifications-list"></div>`;
        await loadNotifications();
    }

    async function loadNotifications() {
        document.getElementById('notifications-list').innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
        try {
            const data = await API.get('/admin-api/notifications/');
            allNotifications = data || [];
            
            // Update notification dot
            const unread = allNotifications.filter(n => !n.is_read).length;
            const dot = document.getElementById('notif-dot');
            if (dot) dot.style.display = unread > 0 ? 'block' : 'none';

            renderList();
        } catch(e) { document.getElementById('notifications-list').innerHTML = `<div class="empty-state"><h3>Could not load notifications</h3><p>${e.message}</p></div>`; }
    }

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
        renderList();
    }

    function renderList() {
        const notifs = currentTab === 'unread' ? allNotifications.filter(n => !n.is_read) : allNotifications;
        
        if (notifs.length === 0) {
            document.getElementById('notifications-list').innerHTML = `<div class="empty-state" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:32px 0;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--clr-border);margin-bottom:16px;">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <h3 style="margin-bottom:8px;color:var(--clr-text);font-size:var(--fs-md);font-weight:var(--fw-semibold);">${window.t('No notifications')}</h3>
                <p style="color:var(--clr-text-muted);font-size:var(--fs-sm);">${window.t("You're all caught up!")}</p>
            </div>`;
            return;
        }

        document.getElementById('notifications-list').innerHTML = notifs.map(n => `
            <div class="card" style="margin-bottom:var(--space-3);padding:var(--space-4) var(--space-5);${!n.is_read ? 'border-left:3px solid var(--clr-primary)' : ''}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        ${n.title ? `<p dir="auto" style="font-size:var(--fs-md);font-weight:var(--fw-bold);margin-bottom:4px;">${window.t(n.title)}</p>` : ''}
                        <p dir="auto" style="font-size:var(--fs-sm);${!n.is_read && !n.title ? 'font-weight:var(--fw-semibold)' : 'color:var(--clr-text-secondary)'}">${window.t(n.message).replace(/\n/g, '<br>')}</p>
                        ${n.image_url ? `<div style="margin-top:12px"><img src="${Auth.getApiBase()}${n.image_url}" style="max-width:100%; max-height:200px; border-radius:var(--radius-md); border:1px solid var(--clr-surface-border);"></div>` : ''}
                        <div style="display:flex;gap:var(--space-3);margin-top:var(--space-1)">
                            <span style="font-size:var(--fs-xs);color:var(--clr-text-muted)">${n.timestamp ? new Date(n.timestamp).toLocaleString(window.I18n.getLang() === 'ar' ? 'ar-EG' : 'en-US') : ''}</span>
                            ${n.department ? `<span style="font-size:var(--fs-xs);color:var(--clr-primary)">· ${window.t('Dept')}: ${n.department}</span>` : ''}
                            ${n.user_email ? `<span style="font-size:var(--fs-xs);color:var(--clr-text-muted)">· ${n.user_email}</span>` : ''}
                        </div>
                    </div>
                    ${!n.is_read ? `<span class="badge badge-primary" style="font-size:10px">${window.t('New')}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    async function markAllRead() {
        try {
            await API.post('/admin-api/notifications/');
            Toast.success(window.t('All notifications marked as read'));
            await loadNotifications();
        } catch { Toast.info(window.t('Mark all read — could not complete')); }
    }

    function openSendModal() {
        const body = `
            <div class="form-group mb-4">
                <label class="form-label" style="display:block;margin-bottom:8px">${window.t("Recipient User Email (Leave 'all' for everyone)")}</label>
                <input type="text" id="notif-user-email" class="form-input" style="width:100%" value="all">
            </div>
            <div class="form-group mb-4">
                <label class="form-label" style="display:block;margin-bottom:8px">${window.t('Notification Title')}</label>
                <input type="text" id="notif-title" class="form-input" style="width:100%">
            </div>
            <div class="form-group mb-4">
                <label class="form-label" style="display:block;margin-bottom:8px">${window.t('Message')}</label>
                <textarea id="notif-msg" class="form-input" style="width:100%;height:100px;resize:vertical"></textarea>
            </div>
            <div class="form-group mb-4">
                <label class="form-label" style="display:block;margin-bottom:8px">${window.t('Type')}</label>
                <select id="notif-type" class="form-input" style="width:100%">
                    <option value="system">${window.t('System Alert')}</option>
                    <option value="promotion">${window.t('Promotion')}</option>
                    <option value="order">${window.t('Order Update')}</option>
                    <option value="alert">${window.t('Important Alert')}</option>
                </select>
            </div>
            <div class="form-group mb-4">
                <label class="form-label" style="display:block;margin-bottom:8px">${window.t('Attach Image (Optional)')}</label>
                <input type="file" id="notif-image" class="form-input" style="width:100%" accept="image/*">
            </div>
            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
                <button class="btn btn-outline" onclick="Modal.close()">${window.t('Cancel')}</button>
                <button class="btn btn-primary" onclick="NotificationsPage.sendNotification()">${window.t('Send')}</button>
            </div>
        `;
        Modal.open(window.t('Send Notification'), body, '');
    }

    async function sendNotification() {
        const userEmail = document.getElementById('notif-user-email').value.trim();
        const title = document.getElementById('notif-title').value.trim();
        const message = document.getElementById('notif-msg').value.trim();
        const type = document.getElementById('notif-type').value;

        if (!title || !message) {
            Toast.error(window.t('Title and message are required'));
            return;
        }

        try {
            const formData = new FormData();
            formData.append('user_email', userEmail);
            formData.append('title', title);
            formData.append('message', message);
            formData.append('type', type);
            
            const imgInput = document.getElementById('notif-image');
            if (imgInput && imgInput.files.length > 0) {
                formData.append('image', imgInput.files[0]);
            }

            await API.request('/admin-api/notifications/send/', {
                method: 'POST',
                body: formData
            });
            Toast.success(window.t('Notification sent successfully'));
            Modal.close();
            await loadNotifications();
        } catch (e) {
            Toast.error(window.t('Failed to send: ') + e.message);
        }
    }

    return { render, switchTab, markAllRead, openSendModal, sendNotification };
})();

window.NotificationsPage = NotificationsPage;
