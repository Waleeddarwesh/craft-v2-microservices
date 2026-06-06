/* Reviews Page */
const ReviewsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header"><div><h1>Reviews</h1><p>Monitor customer reviews and ratings</p></div></div>
            <div id="reviews-table"></div>`;
        try {
            const data = await API.get('/admin-api/reviews/');
            const reviews = data || [];
            DataTable.render('reviews-table', {
                columns: [
                    { key: 'customer_name', label: 'Customer', render: (v, r) => v || r.customer || '—' },
                    { key: 'product_name', label: 'Product', render: (v, r) => v || r.course_name || '—' },
                    { key: 'rating', label: 'Rating', render: v => '⭐'.repeat(v || 0) + '<span class="text-muted">' + '☆'.repeat(5 - (v || 0)) + '</span>' },
                    { key: 'comment', label: 'Comment', render: v => `<span style="max-width:300px;display:inline-block" class="truncate">${v || ''}</span>` },
                    { key: 'created_at', label: 'Date', render: v => v ? new Date(v).toLocaleDateString() : '—' },
                ],
                data: reviews
            });
        } catch(e) { document.getElementById('reviews-table').innerHTML = `<div class="empty-state"><h3>Could not load reviews</h3><p>${e.message}</p></div>`; }
    }
    return { render };
})();
