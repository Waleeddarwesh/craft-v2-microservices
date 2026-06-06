window.ProductModerationPage = async function(container) {
    const html = `
        <div class="page-header">
            <div>
                <h1 class="page-title">${window.t('Product Moderation Queue')}</h1>
                <p class="page-subtitle">${window.t('Approve or reject pending product listings from suppliers.')}</p>
            </div>
            <div class="page-actions">
                <button class="btn btn-outline" onclick="ProductModerationPage.load()">${window.t('Refresh Queue')}</button>
            </div>
        </div>

        <div class="kpi-row" id="mod-kpi-container" style="display: none;">
            <div class="kpi-card">
                <div class="kpi-label"><div class="kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div> ${window.t('Pending Products')}</div>
                <div class="kpi-value text-warning" id="kpi-pending-prods">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><div class="kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></div> ${window.t('Unique Suppliers')}</div>
                <div class="kpi-value" id="kpi-unique-sups">0</div>
            </div>
        </div>

        <div class="premium-table-wrapper">
            <div class="table-responsive">
                <table class="premium-table" id="product-moderation-table">
                    <thead>
                        <tr>
                            <th>${window.t('Product ID')}</th>
                            <th>${window.t('Product Name')}</th>
                            <th>${window.t('Supplier')}</th>
                            <th>${window.t('Unit Price')}</th>
                            <th>${window.t('Submitted Date')}</th>
                            <th>${window.t('Actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="6" class="text-center py-4">${window.t('Loading queue...')}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;

    window.ProductModerationPage.load = async () => {
        try {
            const data = await API.get('/admin-api/moderation/products/');
            const tbody = document.querySelector('#product-moderation-table tbody');
            
            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">${window.t('No products pending approval.')}</td></tr>`;
                return;
            }

            document.getElementById('mod-kpi-container').style.display = 'grid';
            document.getElementById('kpi-pending-prods').innerText = data.length;
            const uniqueSuppliers = new Set(data.map(p => p.Supplier)).size;
            document.getElementById('kpi-unique-sups').innerText = uniqueSuppliers;


            tbody.innerHTML = data.map(product => `
                <tr>
                    <td>#${product.id}</td>
                    <td><strong>${product.ProductName}</strong></td>
                    <td>${product.Supplier}</td>
                    <td>${window.formatCurrency(product.UnitPrice)}</td>
                    <td>${new Date(product.Publish_Date).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="ProductModerationPage.action(${product.id}, 'approve')">Approve</button>
                        <button class="btn btn-sm btn-danger" onclick="ProductModerationPage.action(${product.id}, 'reject')">Reject</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            window.Toast.show('Error loading moderation queue', 'error');
            console.error(err);
        }
    };

    window.ProductModerationPage.action = async (id, action) => {
        const confirmMsg = action === 'approve' ? 'Approve this product for the marketplace?' : 'Reject this product listing?';
        if (!confirm(confirmMsg)) return;
        try {
            await API.post(`/admin-api/moderation/products/${id}/action/`, { action: action });
            window.Toast.show('Moderation action saved', 'success');
            window.ProductModerationPage.load();
        } catch (err) {
            window.Toast.show('Error updating product status', 'error');
            console.error(err);
        }
    };

    await window.ProductModerationPage.load();
};
Router.register('product-moderation', window.ProductModerationPage);
