/* Support Tickets Page */
const SupportTicketsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header">
                <div><h1>${window.t('Support Tickets')}</h1><p>${window.t('Manage customer and supplier support requests')}</p></div>
            </div>
            <div id="tickets-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadTickets();
    }

    async function loadTickets() {
        try {
            const data = await API.get('/admin-api/support-tickets/');
            if (!data || data.length === 0) {
                document.getElementById('tickets-table').innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--clr-text-muted)" stroke-width="1" style="margin-bottom:16px;"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><h3>No Support Tickets</h3><p style="color:var(--clr-text-muted);">All clear here!</p></div>';
                return;
            }
            DataTable.render('tickets-table', {
                columns: [
                    { key: 'id', label: 'ID' },
                    { key: 'user_email', label: 'User' },
                    { key: 'subject', label: 'Subject' },
                    { key: 'status', label: 'Status', render: v => {
                        const map = { open: 'primary', in_progress: 'warning', resolved: 'success', closed: 'neutral' };
                        return `<span class="badge badge-${map[v] || 'neutral'}">${window.t(v.replace('_', ' ').toUpperCase())}</span>`;
                    }},
                    { key: 'priority', label: 'Priority', render: v => {
                        const map = { low: 'neutral', medium: 'info', high: 'warning', critical: 'danger' };
                        return `<span class="badge badge-${map[v] || 'neutral'}">${window.t(v.toUpperCase())}</span>`;
                    }},
                    { key: 'created_at', label: 'Created At', render: v => new Date(v).toLocaleString() },
                    { key: 'actions', label: 'Actions', render: (v, row) => `
                        <button class="btn btn-sm btn-primary" onclick="window.viewTicket(${row.id})">${window.t('View / Reply')}</button>
                    `}
                ],
                data: data
            });
        } catch(e) {
            document.getElementById('tickets-table').innerHTML = `<div class="empty-state"><h3>Could not load tickets</h3><p>${e.message}</p></div>`;
        }
    }

    return { render, loadTickets };
})();

window.viewTicket = async function(id) {
    try {
        const ticket = await API.get(`/admin-api/support-tickets/${id}/`);
        
        const messagesHtml = ticket.messages.map(m => `
            <div style="margin-bottom: 12px; padding: 12px; border-radius: 8px; background: ${m.is_admin ? 'var(--clr-bg-alt)' : 'var(--clr-bg-card)'}; border: 1px solid var(--clr-border);">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:var(--fs-xs); color:var(--clr-text-muted);">
                    <strong>${m.is_admin ? window.t('Admin') + ' ('+m.sender+')' : m.sender}</strong>
                    <span>${new Date(m.created_at).toLocaleString()}</span>
                </div>
                <div>${m.message.replace(/\\n/g, '<br>')}</div>
            </div>
        `).join('');

        const content = `
            <div style="display:flex; flex-direction:column; gap:16px;">
                <div class="ticket-info">
                    <p><strong>${window.t('Customer')}:</strong> ${ticket.user_name} (${ticket.user_email})</p>
                    <p><strong>${window.t('Status')}:</strong> <span class="badge badge-primary">${ticket.status.toUpperCase()}</span></p>
                    <p><strong>${window.t('Description')}:</strong> ${ticket.description}</p>
                </div>
                <hr style="border:0; border-top:1px solid var(--clr-border);">
                <div class="ticket-chat" style="max-height: 300px; overflow-y: auto; padding-right:8px;">
                    ${messagesHtml || '<p style="color:var(--clr-text-muted); font-style:italic;">' + window.t('No messages yet.') + '</p>'}
                </div>
                <hr style="border:0; border-top:1px solid var(--clr-border);">
                <form id="ticket-reply-form" style="display:flex; flex-direction:column; gap:12px;">
                    <div>
                        <label>${window.t('Update Status')}</label>
                        <select id="ticket-status" class="input">
                            <option value="open" ${ticket.status === 'open' ? 'selected' : ''}>${window.t('Open')}</option>
                            <option value="in_progress" ${ticket.status === 'in_progress' ? 'selected' : ''}>${window.t('In Progress')}</option>
                            <option value="resolved" ${ticket.status === 'resolved' ? 'selected' : ''}>${window.t('Resolved')}</option>
                            <option value="closed" ${ticket.status === 'closed' ? 'selected' : ''}>${window.t('Closed')}</option>
                        </select>
                    </div>
                    <div>
                        <label>${window.t('Reply Message (Optional)')}</label>
                        <textarea id="ticket-message" class="input" rows="4" placeholder="${window.t('Type your reply here...')}"></textarea>
                    </div>
                    <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:8px;">
                        <button type="button" class="btn btn-outline" onclick="Modal.close()">${window.t('Cancel')}</button>
                        <button type="submit" class="btn btn-primary">${window.t('Submit Reply')}</button>
                    </div>
                </form>
            </div>
        `;

        Modal.open(`${window.t('Ticket')} #${ticket.id}: ${ticket.subject}`, content);

        document.getElementById('ticket-reply-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const status = document.getElementById('ticket-status').value;
            const message = document.getElementById('ticket-message').value;
            
            try {
                const btn = e.target.querySelector('button[type="submit"]');
                const orig = btn.innerText;
                btn.innerText = window.t('Sending...');
                btn.disabled = true;

                await API.post(`/admin-api/support-tickets/${id}/`, { status, message });
                Toast.show(window.t('Ticket updated successfully'), 'success');
                Modal.close();
                SupportTicketsPage.loadTickets();
            } catch(err) {
                Toast.show(err.message || window.t('Failed to update ticket'), 'error');
            }
        });

    } catch(err) {
        Toast.show(window.t('Failed to load ticket details'), 'error');
    }
};
