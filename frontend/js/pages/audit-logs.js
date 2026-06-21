/* Audit Logs Page */
const AuditLogsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>${window.t('Audit Logs')}</h1><p>${window.t('System activity and security trail')}</p></div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-outline" onclick="AuditLogsPage.exportPDF()">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        ${window.t('Export PDF')}
                    </button>
                    <button class="btn btn-outline" onclick="AuditLogsPage.exportData()">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Export CSV
                    </button>
                </div>
            </div>

            <!-- KPIs -->
            <div class="kpi-row" style="margin-bottom: 24px;">
                <div class="kpi-card">
                    <div class="kpi-label"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:middle;color:var(--primary-color)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>${window.t('TOTAL AUDIT LOGS')}</div>
                    <div class="kpi-value" id="kpi-total-logs">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:middle;color:var(--primary-color)"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>${window.t('LOGS TODAY')}</div>
                    <div class="kpi-value" id="kpi-logs-today">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;vertical-align:middle;color:var(--primary-color)"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>${window.t('UNIQUE ACTORS')}</div>
                    <div class="kpi-value" id="kpi-unique-actors">0</div>
                </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-2" style="margin-bottom: 24px; gap: 24px; grid-template-columns: 2fr 1fr;">
                <div class="card">
                    <h3 style="margin-top:0; margin-bottom:15px; font-size: 14px;">${window.t('Activity Over Last 7 Days')}</h3>
                    <div style="height: 250px;">
                        <canvas id="auditActivityChart"></canvas>
                    </div>
                </div>
                <div class="card">
                    <h3 style="margin-top:0; margin-bottom:15px; font-size: 14px;">${window.t('Action Distribution')}</h3>
                    <div style="height: 250px; display:flex; justify-content:center;">
                        <canvas id="auditActionChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="filter-bar mb-6">
                <input type="text" id="audit-search" class="form-control" placeholder="${window.t('Search logs (user, action)...')}" style="width:300px" oninput="AuditLogsPage.applyFilter()">
            </div>
            <div id="audit-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadLogs();
    }

    let allLogs = [];
    let activityChartInstance = null;
    let actionChartInstance = null;

    async function loadLogs() {
        try {
            const res = await API.get('/admin-api/audit-logs/');
            console.log("Audit Logs API Response:", res);
            
            if (res.kpis) {
                document.getElementById('kpi-total-logs').innerText = res.kpis.total_logs;
                document.getElementById('kpi-logs-today').innerText = res.kpis.logs_today;
                document.getElementById('kpi-unique-actors').innerText = res.kpis.unique_actors;
            }

            if (res.charts) {
                renderCharts(res.charts);
            }

            allLogs = Array.isArray(res.logs) ? res.logs : (res.logs ? Object.values(res.logs) : []);
            renderTable(allLogs);
        } catch(e) { 
            document.getElementById('audit-table').innerHTML = `<div class="empty-state"><h3>Could not load audit logs</h3><p>${e.message}</p></div>`; 
        }
    }

    function renderCharts(chartsData) {
        // Destroy old instances
        if (activityChartInstance) activityChartInstance.destroy();
        if (actionChartInstance) actionChartInstance.destroy();

        const activityCtx = document.getElementById('auditActivityChart').getContext('2d');
        const actionCtx = document.getElementById('auditActionChart').getContext('2d');

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const gridColor = isDark ? '#333' : '#eee';
        const textColor = isDark ? '#888' : '#666';

        // 1. Line Chart
        const activityData = Array.isArray(chartsData.activity_7_days) ? chartsData.activity_7_days : Object.values(chartsData.activity_7_days || {});
        const labels7 = activityData.map(d => {
            const date = new Date(d.date || d);
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        });
        const data7 = activityData.map(d => d.count || 0);

        activityChartInstance = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: labels7,
                datasets: [{
                    label: 'Logs',
                    data: data7,
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4ade80',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: gridColor }, ticks: { color: textColor } },
                    y: { grid: { color: gridColor }, ticks: { color: textColor, precision: 0 }, beginAtZero: true }
                }
            }
        });

        // 2. Doughnut Chart
        const actionData = Array.isArray(chartsData.action_distribution) ? chartsData.action_distribution : Object.values(chartsData.action_distribution || {});
        const actionLabels = actionData.map(d => window.t(d.action || 'Unknown'));
        const actionCounts = actionData.map(d => d.count || 0);
        
        // Map specific actions to consistent colors so they never shuffle when data order changes
        const colorMap = {
            'Changed Settings': '#8b5cf6', // Purple
            'User Login': '#3b82f6',       // Blue
            'Updated Password': '#f59e0b', // Amber
            'Processed Refund': '#ef4444', // Red
            'Approved Supplier': '#10b981',// Green
            'Created Order': '#6366f1',    // Indigo
            'Admin approved supplier': '#ec4899', // Pink
            'Updated Settings': '#14b8a6', // Teal
            'User Logout': '#f43f5e'       // Rose
        };
        const fallbackColors = ['#8b5cf6', '#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#6366f1', '#ec4899', '#14b8a6'];
        const actionColors = actionData.map((d, i) => colorMap[d.action] || fallbackColors[i % fallbackColors.length]);

        actionChartInstance = new Chart(actionCtx, {
            type: 'doughnut',
            data: {
                labels: actionLabels,
                datasets: [{
                    data: actionCounts,
                    backgroundColor: actionColors,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                layout: { padding: 15 }, // <-- Prevent canvas clipping
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, usePointStyle: true, boxWidth: 8, padding: 15, font: { size: 11 } }
                    }
                }
            }
        });
    }

    function renderTable(logs) {
        DataTable.render('audit-table', {
            columns: [
                { key: 'timestamp', label: 'Time', render: v => {
                    const d = new Date(v);
                    return `<span style="font-family:var(--font-mono);font-size:var(--fs-xs)">${d.toLocaleDateString()} ${d.toLocaleTimeString()}</span>`;
                }},
                { key: 'user', label: 'User', render: (v, r) => `<span class="badge badge-neutral">${r.user_details ? r.user_details.email : v}</span>` },
                { key: 'action', label: 'Action', render: v => `<span style="font-weight:var(--fw-medium)">${window.t(v)}</span>` },
                { key: 'model', label: 'Resource', render: (v, r) => v ? `${v} <span style="color:var(--clr-text-muted);font-size:var(--fs-xs)">#${r.object_id||''}</span>` : '—' },
                { key: 'ip_address', label: 'IP Address', render: v => `<span style="font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--clr-text-muted)">${v||'—'}</span>` },
                { key: 'actions', label: '', render: (v, r) => r.model ? `<button class="btn btn-sm btn-outline" onclick="AuditLogsPage.showTimeline('${r.model}', '${r.object_id}')">${window.t('View Timeline')}</button>` : '' }
            ],
            data: logs
        });
    }

    async function showTimeline(entityType, entityId) {
        Modal.open(
            `${window.t('Timeline for')} ${window.t(entityType)} #${entityId}`,
            `<div id="timeline-modal-container"><div class="text-center text-muted" style="padding: 20px;">${window.t('Loading component...')}</div></div>`,
            '',
            'modal-lg'
        );
        
        if (!window.Timeline) {
            try {
                await loadScript('js/components/timeline.js');
            } catch (e) {
                document.getElementById('timeline-modal-container').innerHTML = `<div class="text-danger text-center p-4">Failed to load timeline module</div>`;
                return;
            }
        }
        
        setTimeout(() => {
            if (window.Timeline) {
                window.Timeline.render('timeline-modal-container', entityType, entityId);
            }
        }, 100);
    }

    function applyFilter() {
        const q = document.getElementById('audit-search').value.toLowerCase();
        if (!q) return renderTable(allLogs);
        
        const filtered = allLogs.filter(l => 
            (l.user && l.user.toLowerCase().includes(q)) || 
            (l.action && l.action.toLowerCase().includes(q)) ||
            (l.model && l.model.toLowerCase().includes(q))
        );
        renderTable(filtered);
    }

    function exportData() {
        const headers = ['Time', 'User', 'Action', 'Resource', 'Resource ID', 'IP Address'];
        const dataRows = allLogs.map(l => [
            l.timestamp ? new Date(l.timestamp).toLocaleString() : '',
            l.user || '',
            l.action || '',
            l.model || '',
            l.object_id || '',
            l.ip_address || ''
        ]);
        DataExport.exportToCSV('audit_logs_export.csv', headers, dataRows);
    }

    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    async function exportPDF(event) {
        let btn = event ? event.currentTarget : document.querySelector('[onclick="AuditLogsPage.exportPDF()"]');
        let originalText = btn ? btn.innerHTML : '';
        try {
            if (btn) {
                btn.innerHTML = `<span class="spinner spinner-sm" style="margin-right: 6px;"></span> Exporting...`;
                btn.disabled = true;
            }

            if (!window.jspdf) await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
            if (!window.html2canvas) await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');

            const { jsPDF } = window.jspdf;
            
            // Clean up any old ghost wrappers first!
            document.querySelectorAll('.pdf-export-wrapper').forEach(w => w.remove());

            const exportWrapper = document.createElement('div');
            exportWrapper.className = 'pdf-export-wrapper';
            // Pure inline styling, isolated from classes, positioned far off-screen so it's invisible even on failure
            exportWrapper.style.cssText = 'position: absolute; top: -9999px; left: -9999px; width: 1200px; padding: 40px; background: #ffffff; color: #111827; font-family: sans-serif; box-sizing: border-box;';
            exportWrapper.dir = document.documentElement.dir || 'ltr';
            
            const totalLogs = document.getElementById('kpi-total-logs').innerText;
            const logsToday = document.getElementById('kpi-logs-today').innerText;
            const uniqueActors = document.getElementById('kpi-unique-actors').innerText;
            
            const activityCanvas = document.getElementById('auditActivityChart');
            const actionCanvas = document.getElementById('auditActionChart');
            const activityImgData = activityCanvas ? activityCanvas.toDataURL('image/png') : '';
            const actionImgData = actionCanvas ? actionCanvas.toDataURL('image/png') : '';

            // Notice: NO class names used here to prevent Dark Theme CSS bleeding!
            exportWrapper.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; border-bottom: 1px solid #e5e7eb; padding-bottom: 20px;">
                    <div>
                        <h1 style="margin: 0; font-size: 28px; color: #16a34a;">${window.t('Craft Dashboard')}</h1>
                        <h2 style="margin: 5px 0 0 0; font-size: 20px; font-weight: normal; color: #4b5563;">${window.t('Audit Logs & System Activity Report')}</h2>
                    </div>
                    <div style="text-align: ${exportWrapper.dir === 'rtl' ? 'left' : 'right'}; color: #6b7280;">
                        <p style="margin: 0;">${window.t('Generated by Admin')}</p>
                        <p style="margin: 5px 0 0 0;">${new Date().toLocaleString()}</p>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; gap: 24px; margin-bottom: 30px; width: 100%;">
                    <div style="flex: 1; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
                        <div style="color: #6b7280; font-size: 14px; font-weight: 500; display: flex; align-items: center; margin-bottom: 10px;">
                            <svg style="color: #16a34a; margin-right: 8px; width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path></svg>
                            ${window.t('TOTAL AUDIT LOGS')}
                        </div>
                        <div style="color: #111827; font-size: 28px; font-weight: bold;">${totalLogs}</div>
                    </div>
                    <div style="flex: 1; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
                        <div style="color: #6b7280; font-size: 14px; font-weight: 500; display: flex; align-items: center; margin-bottom: 10px;">
                            <svg style="color: #16a34a; margin-right: 8px; width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>
                            ${window.t('LOGS TODAY')}
                        </div>
                        <div style="color: #111827; font-size: 28px; font-weight: bold;">${logsToday}</div>
                    </div>
                    <div style="flex: 1; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
                        <div style="color: #6b7280; font-size: 14px; font-weight: 500; display: flex; align-items: center; margin-bottom: 10px;">
                            <svg style="color: #16a34a; margin-right: 8px; width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="7" r="4"></circle></svg>
                            ${window.t('UNIQUE ACTORS')}
                        </div>
                        <div style="color: #111827; font-size: 28px; font-weight: bold;">${uniqueActors}</div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; gap: 24px; width: 100%;">
                    <div style="flex: 2; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
                        <h3 style="color: #111827; font-size: 16px; margin-top: 0; margin-bottom: 15px;">${window.t('Activity Over Last 7 Days')}</h3>
                        <div style="text-align: center;"><img src="${activityImgData}" style="max-width: 100%; height: auto;"></div>
                    </div>
                    <div style="flex: 1; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
                        <h3 style="color: #111827; font-size: 16px; margin-top: 0; margin-bottom: 15px;">${window.t('Action Distribution')}</h3>
                        <div style="text-align: center;"><img src="${actionImgData}" style="max-width: 100%; height: auto;"></div>
                    </div>
                </div>
            `;

            document.body.appendChild(exportWrapper);

            // Give it a moment to render layout
            await new Promise(r => setTimeout(r, 200));

            // Race html2canvas against a 10-second timeout to prevent infinite hanging bug
            const canvasPromise = window.html2canvas(exportWrapper, { 
                backgroundColor: '#ffffff',
                scale: 2,
                windowWidth: 1200,
                width: 1200,
                logging: false
            });

            const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error("html2canvas engine timeout")), 10000));
            
            const canvas = await Promise.race([canvasPromise, timeoutPromise]);
            
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('l', 'mm', 'a4'); 
            
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfPageHeight = pdf.internal.pageSize.getHeight();
            const imgProps = pdf.getImageProperties(imgData);
            const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;
            
            pdf.setFillColor(255, 255, 255); 
            pdf.rect(0, 0, pdfWidth, pdfPageHeight, 'F');
            const yPos = imgHeight < pdfPageHeight ? (pdfPageHeight - imgHeight) / 2 : 0;
            pdf.addImage(imgData, 'PNG', 0, yPos, pdfWidth, imgHeight);
            
            const d = new Date();
            const dateStr = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
            pdf.save(`Craft-Audit-Report-${dateStr}.pdf`);

        } catch (error) {
            console.error("PDF Export failed:", error);
            if (window.Toast && window.Toast.error) window.Toast.error("Failed to export PDF: " + error.message);
        } finally {
            // ALWAYS clean up all ghost wrappers
            document.querySelectorAll('.pdf-export-wrapper').forEach(w => w.remove());
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    }

    return { render, applyFilter, exportData, exportPDF, showTimeline };
})();

window.AuditLogsPage = AuditLogsPage;
