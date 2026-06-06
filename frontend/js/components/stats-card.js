/* Stats Card Component */
const StatsCard = (() => {
    function render(label, value, icon, colorClass = 'primary', change = null) {
        const changeHTML = change !== null ? `<div class="stat-card-change ${change >= 0 ? 'up' : 'down'}">${change >= 0 ? '↑' : '↓'} ${Math.abs(change)}%</div>` : '';
        return `<div class="stat-card animate-fade-in-up">
            <div class="stat-card-icon ${colorClass}">${icon}</div>
            <div class="stat-card-label">${label}</div>
            <div class="stat-card-value">${value}</div>
            ${changeHTML}
        </div>`;
    }
    return { render };
})();
