window.Timeline = (() => {
    function render(containerId, entityType, entityId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = \`
            <div class="timeline-container">
                <div class="timeline-header">
                    <h4>\${window.t('Audit Timeline')}</h4>
                    <button class="btn btn-sm btn-secondary" onclick="Timeline.load('\${containerId}', '\${entityType}', '\${entityId}')">
                        \${window.t('Refresh')}
                    </button>
                </div>
                <div class="timeline-content" id="\${containerId}-content">
                    <div class="text-center text-muted" style="padding: 20px;">\${window.t('Loading timeline...')}</div>
                </div>
            </div>
        \`;

        load(containerId, entityType, entityId);
    }

    async function load(containerId, entityType, entityId) {
        const content = document.getElementById(\`\${containerId}-content\`);
        if (!content) return;

        try {
            const res = await API.get(\`/api/audit/logs/?entity_type=\${entityType}&entity_id=\${entityId}\`);
            
            let logs = [];
            if (res && res.results) {
                logs = res.results;
            } else if (Array.isArray(res)) {
                logs = res;
            }

            if (!logs || logs.length === 0) {
                content.innerHTML = \`<div class="text-center text-muted" style="padding: 20px;">\${window.t('No events recorded for this entity.')}</div>\`;
                return;
            }

            let html = '<ul class="timeline-list">';
            logs.forEach(log => {
                const actionColor = getActionColor(log.action);
                const userText = log.user_details ? \`\${log.user_details.first_name} \${log.user_details.last_name}\` : 'System';
                
                html += \`
                    <li class="timeline-item">
                        <div class="timeline-marker bg-\${actionColor}"></div>
                        <div class="timeline-item-content">
                            <div class="timeline-time">\${Utils.formatDate(log.timestamp, true)}</div>
                            <div class="timeline-title">
                                <span class="badge badge-\${actionColor}">\${window.t(log.action)}</span>
                            </div>
                            <div class="timeline-desc">
                                \${window.t('Performed by')}: <strong>\${userText}</strong>
                            </div>
                        </div>
                    </li>
                \`;
            });
            html += '</ul>';
            
            content.innerHTML = html;
        } catch (err) {
            content.innerHTML = \`<div class="text-center text-danger" style="padding: 20px;">\${window.t('Failed to load timeline.')}</div>\`;
        }
    }

    function getActionColor(action) {
        action = action.toLowerCase();
        if (action.includes('create')) return 'success';
        if (action.includes('delete') || action.includes('reject')) return 'danger';
        if (action.includes('update') || action.includes('edit')) return 'warning';
        if (action.includes('approve')) return 'primary';
        return 'secondary';
    }

    // Add some simple CSS for the timeline if not already in styles
    if (!document.getElementById('timeline-styles')) {
        const style = document.createElement('style');
        style.id = 'timeline-styles';
        style.innerHTML = \`
            .timeline-container { border: 1px solid var(--clr-border); border-radius: var(--radius-md); background: var(--clr-surface); }
            .timeline-header { padding: 15px; border-bottom: 1px solid var(--clr-border); display: flex; justify-content: space-between; align-items: center; }
            .timeline-header h4 { margin: 0; font-size: 16px; }
            .timeline-content { padding: 20px; max-height: 400px; overflow-y: auto; }
            .timeline-list { list-style: none; padding: 0; margin: 0; position: relative; }
            .timeline-list::before { content: ''; position: absolute; top: 0; bottom: 0; left: 15px; width: 2px; background: var(--clr-border); }
            .timeline-item { position: relative; padding-left: 40px; margin-bottom: 20px; }
            .timeline-item:last-child { margin-bottom: 0; }
            .timeline-marker { position: absolute; left: 10px; top: 2px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--clr-surface); }
            .timeline-time { font-size: 12px; color: var(--clr-text-muted); margin-bottom: 4px; }
            .timeline-title { margin-bottom: 4px; }
            .timeline-desc { font-size: 13px; }
            .bg-success { background-color: var(--clr-success); }
            .bg-danger { background-color: var(--clr-danger); }
            .bg-warning { background-color: var(--clr-warning); }
            .bg-primary { background-color: var(--clr-primary); }
            .bg-secondary { background-color: var(--clr-text-muted); }
        \`;
        document.head.appendChild(style);
    }

    return { render, load };
})();
