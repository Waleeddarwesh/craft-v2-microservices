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
        </div>

        <!-- Product Details Modal -->
        <div id="product-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; align-items:center; justify-content:center;">
            <div class="card" style="max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; position:relative; padding: 24px;">
                <button onclick="ProductModerationPage.closeModal()" style="position:absolute; right:20px; top:20px; background:none; border:none; font-size:24px; cursor:pointer; color: var(--text-color);">&times;</button>
                <h2 id="modal-title" style="margin-top:0; padding-right: 30px;"></h2>
                <div id="modal-body" style="margin-top: 20px;"></div>
                <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;" id="modal-actions"></div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;

    window.ProductModerationPage.load = async () => {
        try {
            const data = await API.get('/admin-api/moderation/products/');
            window.ProductModerationPage.currentData = data;
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
                    <td>EGP ${product.UnitPrice}</td>
                    <td>${new Date(product.Publish_Date).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="ProductModerationPage.viewDetails(${product.id})">View</button>
                        <button class="btn btn-sm btn-primary" onclick="ProductModerationPage.action(${product.id}, 'approve')">Approve</button>
                        <button class="btn btn-sm btn-danger" onclick="ProductModerationPage.action(${product.id}, 'reject')">Reject</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            Toast.error(window.t('Error loading moderation queue'));
            console.error(err);
        }
    };

    window.ProductModerationPage.action = async (id, action) => {
        const confirmMsg = action === 'approve' ? window.t('Approve this product for the marketplace?') : window.t('Reject this product listing?');
        if (!confirm(confirmMsg)) return;
        try {
            await API.post(`/admin-api/moderation/products/${id}/action/`, { action: action });
            Toast.success(window.t('Moderation action saved'));
            window.ProductModerationPage.load();
        } catch (err) {
            Toast.error(window.t('Error updating product status'));
            console.error(err);
        }
    };

    window.ProductModerationPage.viewDetails = (id) => {
        const product = window.ProductModerationPage.currentData.find(p => p.id === id);
        if (!product) return;
        
        document.getElementById('modal-title').innerText = product.ProductName;
        
        let imagesHtml = '';
        if (product.images && product.images.length > 0) {
            imagesHtml = `<div style="display: flex; gap: 10px; overflow-x: auto; margin-bottom: 15px;">
                ${product.images.map(img => `<img src="${img}" style="max-height: 200px; border-radius: 4px; object-fit: contain; background: #eee;">`).join('')}
            </div>`;
        } else {
            imagesHtml = `<div style="margin-bottom: 15px; padding: 20px; background: #333; text-align: center; border-radius: 4px;">No images available</div>`;
        }

        document.getElementById('modal-body').innerHTML = `
            ${imagesHtml}
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div><strong>Supplier:</strong> ${product.Supplier}</div>
                <div><strong>Price:</strong> EGP ${product.UnitPrice}</div>
                <div><strong>Category:</strong> ${product.Category || 'N/A'}</div>
                <div><strong>Stock:</strong> ${product.Stock || 0}</div>
                <div><strong>Submitted:</strong> ${new Date(product.Publish_Date).toLocaleDateString()}</div>
            </div>
            <div>
                <strong>Description:</strong>
                <p style="white-space: pre-wrap; margin-top: 5px;">${product.ProductDescription || 'No description provided.'}</p>
            </div>
        `;

        document.getElementById('modal-actions').innerHTML = `
            <button class="btn btn-secondary" onclick="ProductModerationPage.closeModal()">Close</button>
            <button class="btn btn-danger" onclick="ProductModerationPage.action(${product.id}, 'reject'); ProductModerationPage.closeModal();">Reject</button>
            <button class="btn btn-primary" onclick="ProductModerationPage.action(${product.id}, 'approve'); ProductModerationPage.closeModal();">Approve</button>
        `;

        document.getElementById('product-modal').style.display = 'flex';
    };

    window.ProductModerationPage.closeModal = () => {
        document.getElementById('product-modal').style.display = 'none';
    };

    await window.ProductModerationPage.load();
};
Router.register('product-moderation', window.ProductModerationPage);
