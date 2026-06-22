window.TasksPage = (() => {
    let currentPage = 1;

    async function render(container) {
        const html = `
            <div class="page-header">
                <div>
                    <h2 class="page-title">${window.t('My Tasks')}</h2>
                    <p class="page-description">${window.t('Manage your assigned departmental tasks and operations.')}</p>
                </div>
            </div>

            <div class="card">
                <div class="table-toolbar">
                    <div class="form-search" style="width: 320px; max-width: 100%;">
                        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" class="form-input" placeholder="${window.t('Search tasks...')}" id="search-tasks">
                    </div>
                    <div class="table-actions">
                        <select class="form-input" id="filter-status">
                            <option value="">${window.t('All Statuses')}</option>
                            <option value="open">${window.t('Open')}</option>
                            <option value="in_progress">${window.t('In Progress')}</option>
                            <option value="waiting_approval">${window.t('Waiting Approval')}</option>
                        </select>
                        <select class="form-input" id="filter-priority">
                            <option value="">${window.t('All Priorities')}</option>
                            <option value="critical">${window.t('Critical')}</option>
                            <option value="high">${window.t('High')}</option>
                            <option value="medium">${window.t('Medium')}</option>
                            <option value="low">${window.t('Low')}</option>
                        </select>
                        <button class="btn btn-secondary" onclick="TasksPage.loadTasks()">
                            ${window.t('Refresh')}
                        </button>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="data-table" id="tasks-table">
                        <thead>
                            <tr>
                                <th>${window.t('Task ID')}</th>
                                <th>${window.t('Title')}</th>
                                <th>${window.t('Department')}</th>
                                <th>${window.t('Priority')}</th>
                                <th>${window.t('Status')}</th>
                                <th>${window.t('Due Date')}</th>
                                <th class="text-right">${window.t('Actions')}</th>
                            </tr>
                        </thead>
                        <tbody id="tasks-body">
                            <tr><td colspan="7" class="text-center">${window.t('Loading tasks...')}</td></tr>
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="tasks-pagination"></div>
            </div>
        `;

        container.innerHTML = html;
        window.I18n.translateDOM(container);
        
        document.getElementById('search-tasks').addEventListener('input', Utils.debounce(() => {
            currentPage = 1;
            loadTasks();
        }, 500));
        
        document.getElementById('filter-status').addEventListener('change', () => { currentPage = 1; loadTasks(); });
        document.getElementById('filter-priority').addEventListener('change', () => { currentPage = 1; loadTasks(); });

        await loadTasks();
    }

    async function loadTasks() {
        const tbody = document.getElementById('tasks-body');
        const search = document.getElementById('search-tasks').value;
        const status = document.getElementById('filter-status').value;
        const priority = document.getElementById('filter-priority').value;

        try {
            let url = `/api/workflows/tasks/my_tasks/?page=${currentPage}`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (status) url += `&status=${status}`;
            if (priority) url += `&priority=${priority}`;

            const res = await API.get(url);
            
            // Handle both paginated and unpaginated responses
            let tasks = [];
            if (res && res.results) {
                tasks = res.results;
            } else if (Array.isArray(res)) {
                tasks = res;
            }

            if (!tasks || tasks.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center">${window.t('No tasks found.')}</td></tr>`;
                document.getElementById('tasks-pagination').innerHTML = '';
                return;
            }

            tbody.innerHTML = tasks.map(task => `
                <tr>
                    <td>#${task.id}</td>
                    <td>
                        <div class="fw-medium">${task.title}</div>
                        <div class="text-xs text-muted">${task.description || ''}</div>
                    </td>
                    <td>${task.department}</td>
                    <td><span class="badge badge-${getPriorityColor(task.priority)}">${window.t(task.priority)}</span></td>
                    <td><span class="badge badge-${getStatusColor(task.status)}">${window.t(task.status)}</span></td>
                    <td>${task.due_at ? Utils.formatDate(task.due_at) : '-'}</td>
                    <td class="text-right">
                        <button class="btn btn-secondary btn-sm" onclick="TasksPage.viewDetails(${task.id})">${window.t('View')}</button>
                    </td>
                </tr>
            `).join('');

            // Basic pagination handling if paginated
            if (res && res.count) {
                renderPagination(res.count);
            } else {
                document.getElementById('tasks-pagination').innerHTML = '';
            }
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">${window.t('Error loading tasks')}</td></tr>`;
        }
        window.I18n.translateDOM(tbody);
    }

    function getPriorityColor(priority) {
        return {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'primary',
            'low': 'secondary'
        }[priority] || 'secondary';
    }

    function getStatusColor(status) {
        return {
            'open': 'primary',
            'in_progress': 'warning',
            'waiting_approval': 'secondary',
            'completed': 'success',
            'cancelled': 'danger'
        }[status] || 'secondary';
    }

    function renderPagination(totalCount) {
        const totalPages = Math.ceil(totalCount / 10);
        let html = '';
        
        if (currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="TasksPage.changePage(${currentPage - 1})">${window.t('Previous')}</button>`;
        }
        
        html += `<span class="page-info">${window.t('Page')} ${currentPage} ${window.t('of')} ${totalPages}</span>`;
        
        if (currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="TasksPage.changePage(${currentPage + 1})">${window.t('Next')}</button>`;
        }
        
        document.getElementById('tasks-pagination').innerHTML = html;
        window.I18n.translateDOM(document.getElementById('tasks-pagination'));
    }

    function changePage(page) {
        currentPage = page;
        loadTasks();
    }

    function viewDetails(id) {
        alert(window.t("Task detail view coming soon for task #") + id);
    }

    return { render, loadTasks, changePage, viewDetails };
})();

window.TasksPage = TasksPage;

Router.register('tasks', window.TasksPage.render);
