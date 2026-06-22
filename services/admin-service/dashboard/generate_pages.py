import os

pages = [
    ('services', 'Services Registry', 'Manage all system services from one place.'),
    ('users-linux', 'Linux User Administration', 'Manage system user accounts, groups, and sudo access.'),
    ('system-logs', 'System Logs', 'Centralized search and live view of application and system logs.'),
    ('storage', 'Storage Administration', 'Manage disks, mounts, and LVM volumes.'),
    ('backups', 'Backup & Recovery', 'Manage database, media, and configuration backups.'),
    ('cron-jobs', 'Cron Job Administration', 'Create, edit, and disable scheduled tasks.'),
    ('security-center', 'Security Center', 'Manage Firewall rules, SELinux, and view security alerts.'),
    ('config-management', 'Configuration Management', 'Manage environment variables and config files.'),
    ('file-explorer', 'File Explorer', 'Browse directories and manage file permissions.'),
    ('containers', 'Container Operations', 'Administer Docker/Podman containers and OpenShift/Kubernetes.'),
    ('incidents', 'Incident Management', 'Track alerts, root causes, and resolution workflows.'),
    ('automation', 'Operational Scripts', 'Store, execute, and schedule operational scripts.')
]

base_dir = r"r:\Craft\MicroServices Craft\services\admin-service\dashboard\js\pages"

template = """const {PageClass} = (() => {{
    function render(container) {{
        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>${{window.t('{title}')}}</h2>
                    <p class="text-secondary">${{window.t('{desc}')}}</p>
                </div>
                <div class="header-actions">
                    <button class="btn btn-primary" onclick="Toast.show('Action not implemented yet.', 'info')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        ${{window.t('Add New')}}
                    </button>
                </div>
            </div>

            <div class="card">
                <div class="table-actions">
                    <div class="search-box">
                        <input type="text" placeholder="${{window.t('Search...')}}">
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>${{window.t('Name')}}</th>
                                <th>${{window.t('Status')}}</th>
                                <th>${{window.t('Actions')}}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="3" class="text-center py-4">No data available in this phase.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }}

    return {{ render }};
}})();

window.{PageClass} = {PageClass};
"""

for slug, title, desc in pages:
    class_name = ''.join(word.capitalize() for word in slug.split('-')) + "Page"
    file_path = os.path.join(base_dir, f"{slug}.js")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template.format(PageClass=class_name, title=title, desc=desc))

print("All files generated successfully.")
