/* Coupons Page */
const CouponsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header"><div><h1>Coupons</h1><p>Manage promotional coupon codes</p></div></div>
            <div id="coupons-table"></div>`;
        try {
            const data = await API.get('/admin-api/coupons/');
            const coupons = data || [];
            DataTable.render('coupons-table', {
                columns: [
                    { key: 'code', label: 'Code', render: v => `<span style="font-family:var(--font-mono);font-weight:var(--fw-semibold);color:var(--clr-accent)">${v}</span>` },
                    { key: 'supplier_name', label: 'Supplier', render: (v, r) => v || r.supplier || '—' },
                    { key: 'discount', label: 'Discount', render: (v, r) => r.discount_type === 'percentage' ? `${v}%` : `EGP ${parseFloat(v||0).toFixed(2)}` },
                    { key: 'discount_type', label: 'Type', render: v => `<span class="badge badge-neutral">${(v||'').replace(/_/g,' ')}</span>` },
                    { key: 'uses_count', label: 'Used', render: (v, r) => `${v || 0} / ${r.max_uses || '∞'}` },
                    { key: 'active', label: 'Active', render: v => v ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-neutral">Inactive</span>' },
                    { key: 'valid_to', label: 'Expires', render: v => {
                        if (!v) return '—';
                        const d = new Date(v);
                        const expired = d < new Date();
                        return `<span class="${expired ? 'text-danger' : ''}">${d.toLocaleDateString()}${expired ? ' (expired)' : ''}</span>`;
                    }},
                ],
                data: coupons
            });
        } catch(e) { document.getElementById('coupons-table').innerHTML = `<div class="empty-state"><h3>Could not load coupons</h3><p>${e.message}</p></div>`; }
    }
    return { render };
})();
