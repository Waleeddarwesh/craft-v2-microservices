window.ApprovalsPage = (() => {
    let currentPage = 1;

    async function render(container) {
        const html = `
            <div class="page-header">
                <div>
                    <h2 class="page-title">${window.t('Pending Approvals')}</h2>
                    <p class="page-description">${window.t('Review and manage pending approval requests for your department.')}</p>
                </div>
            </div>

            <div class="card">
                <div class="table-toolbar">
                    <div class="form-search" style="width: 320px; max-width: 100%;">
                        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" class="form-input" placeholder="${window.t('Search approvals...')}" id="search-approvals">
                    </div>
                    <div class="table-actions">
                        <select class="form-input" id="filter-status">
                            <option value="">${window.t('All Statuses')}</option>
                            <option value="pending" selected>${window.t('Pending')}</option>
                            <option value="approved">${window.t('Approved')}</option>
                            <option value="rejected">${window.t('Rejected')}</option>
                        </select>
                        <button class="btn btn-secondary" onclick="ApprovalsPage.loadApprovals()">
                            ${window.t('Refresh')}
                        </button>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="data-table" id="approvals-table">
                        <thead>
                            <tr>
                                <th>${window.t('Request ID')}</th>
                                <th>${window.t('Type')}</th>
                                <th>${window.t('Related Object')}</th>
                                <th>${window.t('Department')}</th>
                                <th>${window.t('Requested By')}</th>
                                <th>${window.t('Status')}</th>
                                <th>${window.t('Date')}</th>
                                <th class="text-right">${window.t('Actions')}</th>
                            </tr>
                        </thead>
                        <tbody id="approvals-body">
                            <tr><td colspan="8" class="text-center">${window.t('Loading approvals...')}</td></tr>
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="approvals-pagination"></div>
            </div>
        `;

        container.innerHTML = html;
        window.I18n.translateDOM(container);
        
        document.getElementById('search-approvals').addEventListener('input', Utils.debounce(() => {
            currentPage = 1;
            loadApprovals();
        }, 500));
        
        document.getElementById('filter-status').addEventListener('change', () => { currentPage = 1; loadApprovals(); });

        await loadApprovals();
    }

    async function loadApprovals() {
        const tbody = document.getElementById('approvals-body');
        const search = document.getElementById('search-approvals').value;
        const status = document.getElementById('filter-status').value;

        try {
            let url = `/api/workflows/approvals/?page=${currentPage}`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (status) url += `&status=${status}`;

            const res = await API.get(url);
            
            let approvals = [];
            if (res && res.results) {
                approvals = res.results;
            } else if (Array.isArray(res)) {
                approvals = res;
            }

            if (!approvals || approvals.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center">${window.t('No approval requests found.')}</td></tr>`;
                document.getElementById('approvals-pagination').innerHTML = '';
                return;
            }

            tbody.innerHTML = approvals.map(approval => `
                <tr>
                    <td>#${approval.id}</td>
                    <td><span class="badge badge-secondary">${window.t(approval.request_type)}</span></td>
                    <td>${approval.related_object_type} (#${approval.related_object_id})</td>
                    <td>${approval.assigned_department}</td>
                    <td>${approval.requested_by_details ? approval.requested_by_details.email : '-'}</td>
                    <td><span class="badge badge-${getStatusColor(approval.status)}">${window.t(approval.status)}</span></td>
                    <td>${Utils.formatDate(approval.created_at)}</td>
                    <td class="text-right">
                        ${approval.status === 'pending' ? `
                            <button class="btn btn-primary btn-sm" onclick="ApprovalsPage.review(${approval.id}, 'approve')">${window.t('Approve')}</button>
                            <button class="btn btn-danger btn-sm" onclick="ApprovalsPage.review(${approval.id}, 'reject')">${window.t('Reject')}</button>
                        ` : `<button class="btn btn-secondary btn-sm" onclick="ApprovalsPage.viewDetails(${approval.id})">${window.t('View')}</button>`}
                    </td>
                </tr>
            `).join('');

            if (res && res.count) {
                renderPagination(res.count);
            } else {
                document.getElementById('approvals-pagination').innerHTML = '';
            }
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">${window.t('Error loading approvals')}</td></tr>`;
        }
        window.I18n.translateDOM(tbody);
    }

    function getStatusColor(status) {
        return {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary'
        }[status] || 'secondary';
    }

    function renderPagination(totalCount) {
        const totalPages = Math.ceil(totalCount / 10);
        let html = '';
        if (currentPage > 1) {
            html += `<button class="btn btn-secondary" onclick="ApprovalsPage.changePage(${currentPage - 1})">${window.t('Previous')}</button>`;
        }
        html += `<span class="page-info">${window.t('Page')} ${currentPage} ${window.t('of')} ${totalPages}</span>`;
        if (currentPage < totalPages) {
            html += `<button class="btn btn-secondary" onclick="ApprovalsPage.changePage(${currentPage + 1})">${window.t('Next')}</button>`;
        }
        document.getElementById('approvals-pagination').innerHTML = html;
        window.I18n.translateDOM(document.getElementById('approvals-pagination'));
    }

    function changePage(page) {
        currentPage = page;
        loadApprovals();
    }

    async function review(id, action) {
        const comment = prompt(window.t('Add an optional comment for this action:'));
        if (comment === null) return; // cancelled

        try {
            await API.post(`/api/workflows/approvals/${id}/review/`, {
                action: action,
                comment: comment
            });
            loadApprovals();
        } catch (err) {
            alert(window.t('Failed to process review: ') + err.message);
        }
    }

    function viewDetails(id) {
        alert(window.t("Approval detail view coming soon for #") + id);
    }

    return { render, loadApprovals, changePage, review, viewDetails };
})();

window.ApprovalsPage = ApprovalsPage;

Router.register('approvals', window.ApprovalsPage.render);
