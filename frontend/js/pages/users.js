/* User Management Page */
const UsersPage = (() => {
    let currentTab = 'customers';
    let userData = { customers: [], suppliers: [], delivery: [] };

    async function render(container) {
        container.innerHTML = `
            <div class="page-header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1>User Management</h1><p>Manage customers, suppliers, and delivery personnel</p></div>
                <button class="btn btn-outline" onclick="UsersPage.exportData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
            </div>
            <div class="tabs">
                <div class="tab active" data-tab="customers" onclick="UsersPage.switchTab('customers')">Customers</div>
                <div class="tab" data-tab="suppliers" onclick="UsersPage.switchTab('suppliers')">Suppliers</div>
                <div class="tab" data-tab="delivery" onclick="UsersPage.switchTab('delivery')">Delivery</div>
            </div>
            <div id="users-table">
                <div class="skeleton" style="height:400px; border-radius:var(--radius-lg)"></div>
            </div>`;
        await loadUsers();
    }

    async function loadUsers() {
        try {
            const data = await API.get('/admin-api/users/');
            if (data) {
                userData.customers = (data.customers || []);
                userData.suppliers = (data.suppliers || []);
                userData.delivery = (data.delivery || []);
            }
        } catch {
            // fallback: try individual endpoints
            try { const d = await API.get('/accounts/suppliers/'); userData.suppliers = d.results || d || []; } catch {}
        }
        renderTab();
    }

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
        renderTab();
    }

    function renderTab() {
        const data = userData[currentTab] || [];
        if (currentTab === 'suppliers') renderSuppliers(data);
        else if (currentTab === 'delivery') renderDelivery(data);
        else renderCustomers(data);
    }

    function renderCustomers(customers) {
        DataTable.render('users-table', {
            columns: [
                { key: 'email', label: 'Email' },
                { key: 'full_name', label: 'Name', render: (v, r) => v || `${r.first_name || ''} ${r.last_name || ''}` },
                { key: 'PhoneNO', label: 'Phone' },
                { key: 'is_verified', label: 'Verified', render: v => v ? '<span class="text-success">✓</span>' : '<span class="text-danger">✗</span>' },
                { key: 'Balance', label: 'Balance', render: v => `EGP ${parseFloat(v||0).toFixed(2)}` },
                { key: 'date_joined', label: 'Joined', render: v => v ? new Date(v).toLocaleDateString() : '—' },
                { key: 'id', label: 'Actions', render: (v, row) => `<button class="btn btn-sm btn-ghost" onclick="UsersPage.viewUser('${row.user_id || row.id}')">View</button>` },
            ],
            data: customers,
            onRowClick: row => UsersPage.viewUser(row.user_id || row.id)
        });
    }

    function renderSuppliers(suppliers) {
        DataTable.render('users-table', {
            columns: [
                { key: 'name', label: 'Name', render: (v, r) => v || r.user_name || `${r.first_name || ''} ${r.last_name || ''}` },
                { key: 'CategoryTitle', label: 'Category' },
                { key: 'Rating', label: 'Rating', render: v => `⭐ ${parseFloat(v||0).toFixed(1)}` },
                { key: 'FollowersNo', label: 'Followers' },
                { key: 'Orders', label: 'Orders', render: v => v || 0 },
                { key: 'accepted_supplier', label: 'Approved', render: (v, row) => v
                    ? '<span class="badge badge-success">Approved</span>'
                    : `<div style="display:flex; gap:4px;"><button class="btn btn-sm btn-success" onclick="UsersPage.approveSupplier('${row.id}')">Approve</button>
                       <button class="btn btn-sm btn-danger" onclick="UsersPage.denySupplier('${row.id}')">Deny</button></div>` },
                { key: 'id', label: 'Actions', render: (v, row) => `<button class="btn btn-sm btn-ghost" onclick="UsersPage.viewUser('${row.user_id || row.id}')">View</button>` },
            ],
            data: suppliers,
            onRowClick: row => { if(row.user_id || row.id) UsersPage.viewUser(row.user_id || row.id) }
        });
    }

    function renderDelivery(delivery) {
        DataTable.render('users-table', {
            columns: [
                { key: 'name', label: 'Name', render: (v, r) => v || r.user_name || '' },
                { key: 'VehicleModel', label: 'Vehicle' },
                { key: 'plateNO', label: 'Plate No' },
                { key: 'governorate', label: 'Area', render: v => window.t(v || 'default_governorate') },
                { key: 'Rating', label: 'Rating', render: v => `⭐ ${parseFloat(v||0).toFixed(1)}` },
                { key: 'accepted_delivery', label: 'Approved', render: (v, row) => v
                    ? '<span class="badge badge-success">Approved</span>'
                    : `<div style="display:flex; gap:4px;"><button class="btn btn-sm btn-success" onclick="UsersPage.approveDelivery('${row.id}')">Approve</button>
                       <button class="btn btn-sm btn-danger" onclick="UsersPage.denyDelivery('${row.id}')">Deny</button></div>` },
                { key: 'id', label: 'Actions', render: (v, row) => `<button class="btn btn-sm btn-ghost" onclick="UsersPage.viewUser('${row.user_id || row.id}')">View</button>` },
            ],
            data: delivery,
            onRowClick: row => { if(row.user_id || row.id) UsersPage.viewUser(row.user_id || row.id) }
        });
    }

    async function viewUser(id) {
        if (!id || id === 'undefined') {
            Toast.error('Invalid user ID');
            return;
        }
        try {
            const user = await API.get(`/admin-api/users/${id}/`);
            let typeBadge = '';
            let extraInfo = '';
            
            if (user.type === 'supplier' && user.supplier_info) {
                typeBadge = '<span class="badge badge-primary">Supplier</span>';
                let docsHtml = `
                    <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--clr-surface-border)">
                        <h4 style="margin-bottom:8px">${window.t('Verification Documents')}</h4>
                        <div style="display:flex; gap:8px;">
                            ${user.supplier_info.contract_url ? `<a href="${user.supplier_info.contract_url}" target="_blank" class="btn btn-sm btn-outline">${window.t('View Contract')}</a>` : `<span class="badge badge-neutral">${window.t('Contract Not Uploaded')}</span>`}
                            ${user.supplier_info.identity_url ? `<a href="${user.supplier_info.identity_url}" target="_blank" class="btn btn-sm btn-outline">${window.t('View Identity')}</a>` : `<span class="badge badge-neutral">${window.t('Identity Not Uploaded')}</span>`}
                        </div>
                    </div>
                `;
                extraInfo = `
                    <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--clr-surface-border)">
                        <h4 style="margin-bottom:8px">${window.t('Supplier Details')}</h4>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:var(--fs-sm)">
                            <div><span style="color:var(--clr-text-muted)">${window.t('Category')}:</span> ${user.supplier_info.category}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Rating')}:</span> ⭐ ${user.supplier_info.rating}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Orders')}:</span> ${user.supplier_info.orders}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Followers')}:</span> ${user.supplier_info.followers}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Status')}:</span> ${user.supplier_info.accepted ? window.t('Approved') : window.t('Pending')}</div>
                        </div>
                    </div>
                    ${docsHtml}
                `;
            } else if (user.type === 'delivery' && user.delivery_info) {
                typeBadge = '<span class="badge badge-accent">Delivery</span>';
                let docsHtml = `
                    <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--clr-surface-border)">
                        <h4 style="margin-bottom:8px">Verification Documents</h4>
                        <div style="display:flex; gap:8px;">
                            ${user.delivery_info.contract_url ? `<a href="${user.delivery_info.contract_url}" target="_blank" class="btn btn-sm btn-outline">View Contract</a>` : '<span class="badge badge-neutral">Contract Not Uploaded</span>'}
                            ${user.delivery_info.identity_url ? `<a href="${user.delivery_info.identity_url}" target="_blank" class="btn btn-sm btn-outline">View Identity</a>` : '<span class="badge badge-neutral">Identity Not Uploaded</span>'}
                        </div>
                    </div>
                `;
                extraInfo = `
                    <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--clr-surface-border)">
                        <h4 style="margin-bottom:8px">${window.t('Delivery Details')}</h4>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:var(--fs-sm)">
                            <div><span style="color:var(--clr-text-muted)">${window.t('Vehicle')}:</span> ${user.delivery_info.vehicle}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Plate')}:</span> ${user.delivery_info.plate}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Area')}:</span> ${window.t(user.delivery_info.area || 'default_governorate')}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Rating')}:</span> ⭐ ${user.delivery_info.rating}</div>
                            <div><span style="color:var(--clr-text-muted)">${window.t('Status')}:</span> ${user.delivery_info.accepted ? window.t('Approved') : window.t('Pending')}</div>
                        </div>
                    </div>
                    ${docsHtml}
                `;
            } else {
                typeBadge = '<span class="badge badge-info">Customer</span>';
            }
            
            const body = `
                <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
                    <div style="width:64px; height:64px; border-radius:50%; background:var(--clr-primary); color:white; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:bold;">
                        ${(user.first_name?.[0] || user.email[0] || 'U').toUpperCase()}
                    </div>
                    <div>
                        <h3 style="margin:0; font-size:18px;">${user.full_name || 'No Name'}</h3>
                        <p style="margin:4px 0 0 0; color:var(--clr-text-muted);">${user.email}</p>
                        <div style="margin-top:4px; display:flex; gap:8px;">${typeBadge} ${user.is_verified ? `<span class="badge badge-success">${window.t('Verified')}</span>` : ''}</div>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:var(--fs-sm)">
                    <div><span style="color:var(--clr-text-muted)">${window.t('Phone')}:</span> ${user.phone || 'N/A'}</div>
                    <div><span style="color:var(--clr-text-muted)">${window.t('Joined')}:</span> ${user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}</div>
                    <div><span style="color:var(--clr-text-muted)">${window.t('Balance')}:</span> EGP ${user.balance.toFixed(2)}</div>
                    <div><span style="color:var(--clr-text-muted)">${window.t('Active')}:</span> ${user.is_active ? window.t('Yes') : window.t('No')}</div>
                </div>
                ${extraInfo}
                <div style="margin-top:24px; display:flex; justify-content:flex-end; gap:8px;">
                    <button class="btn btn-outline" onclick="Modal.close()">${window.t('Close')}</button>
                </div>
            `;
            Modal.open(window.t('User Details'), body, '');
        } catch(e) {
            Toast.error('Could not load user details');
        }
    }

    async function approveSupplier(id) {
        try {
            await API.patch(`/admin-api/users/supplier/${id}/`, { accepted_supplier: true });
            Toast.success('Supplier approved');
            await loadUsers();
        } catch(e) { Toast.error(e.message); }
    }

    async function approveDelivery(id) {
        try {
            await API.patch(`/admin-api/users/delivery/${id}/`, { accepted_delivery: true });
            Toast.success('Delivery person approved');
            await loadUsers();
        } catch(e) { Toast.error(e.message); }
    }

    async function denySupplier(id) {
        if (!confirm('Are you sure you want to deny this supplier? This will completely remove their pending account.')) return;
        try {
            await API.delete(`/admin-api/users/supplier/${id}/`);
            Toast.success('Supplier application denied and removed');
            await loadUsers();
        } catch(e) { Toast.error(e.message); }
    }

    async function denyDelivery(id) {
        if (!confirm('Are you sure you want to deny this delivery person? This will completely remove their pending account.')) return;
        try {
            await API.delete(`/admin-api/users/delivery/${id}/`);
            Toast.success('Delivery application denied and removed');
            await loadUsers();
        } catch(e) { Toast.error(e.message); }
    }

    function exportData() {
        const data = userData[currentTab] || [];
        if (currentTab === 'suppliers') {
            const headers = ['Name', 'Category', 'Rating', 'Followers', 'Orders', 'Approved'];
            const rows = data.map(r => [
                r.name || r.user_name || `${r.first_name || ''} ${r.last_name || ''}`,
                r.CategoryTitle || '',
                parseFloat(r.Rating||0).toFixed(1),
                r.FollowersNo || 0,
                r.Orders || 0,
                r.accepted_supplier ? 'Yes' : 'No'
            ]);
            DataExport.exportToCSV('suppliers_export.csv', headers, rows);
        } else if (currentTab === 'delivery') {
            const headers = ['Name', 'Vehicle Model', 'Plate No', 'Area', 'Rating', 'Approved'];
            const rows = data.map(r => [
                r.name || r.user_name || '',
                r.VehicleModel || '',
                r.plateNO || '',
                r.governorate || '',
                parseFloat(r.Rating||0).toFixed(1),
                r.accepted_delivery ? 'Yes' : 'No'
            ]);
            DataExport.exportToCSV('delivery_export.csv', headers, rows);
        } else {
            const headers = ['Email', 'Name', 'Phone', 'Verified', 'Balance', 'Joined'];
            const rows = data.map(r => [
                r.email || '',
                r.full_name || `${r.first_name || ''} ${r.last_name || ''}`,
                r.PhoneNO || '',
                r.is_verified ? 'Yes' : 'No',
                parseFloat(r.Balance||0).toFixed(2),
                r.date_joined ? new Date(r.date_joined).toLocaleDateString() : ''
            ]);
            DataExport.exportToCSV('customers_export.csv', headers, rows);
        }
    }

    return { render, switchTab, approveSupplier, approveDelivery, denySupplier, denyDelivery, exportData, viewUser };
})();
