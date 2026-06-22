/* Chart Helpers — Chart.js Wrappers */
const Charts = (() => {
    const defaultColors = {
        primary: '#7fb04f', primaryLight: 'hsla(94, 42%, 50%, 0.15)',
        accent: 'hsl(42, 85%, 55%)', accentLight: 'hsla(42, 85%, 55%, 0.15)',
        success: 'hsl(152, 60%, 48%)', warning: 'hsl(40, 90%, 55%)',
        danger: 'hsl(0, 68%, 55%)', info: 'hsl(205, 75%, 55%)',
        text: 'hsl(210, 8%, 58%)', grid: 'hsla(210, 10%, 28%, 0.3)'
    };
    const palette = ['#7fb04f','#e6a817','#3b9be0','#e05252','#56c2a8','#c77dba','#e88b4d','#5b8fd9'];
    const stored = {};

    function base(type, canvasId, config) {
        if (stored[canvasId]) stored[canvasId].destroy();
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        Chart.defaults.color = defaultColors.text;
        Chart.defaults.font.family = 'Inter, sans-serif';
        const chart = new Chart(ctx, { type, ...config });
        stored[canvasId] = chart;
        return chart;
    }

    function line(canvasId, labels, datasets, opts = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');
        
        return base('line', canvasId, {
            data: { labels, datasets: datasets.map((ds, i) => {
                const color = palette[i % palette.length];
                let gradient = ctx.createLinearGradient(0, 0, 0, 350);
                gradient.addColorStop(0, color + '66'); // 40% opacity
                gradient.addColorStop(1, color + '00'); // 0% opacity
                
                return {
                    borderColor: color, 
                    backgroundColor: gradient,
                    borderWidth: 3, 
                    pointRadius: 4, 
                    pointBackgroundColor: '#1a1d20', 
                    pointBorderColor: color,
                    pointBorderWidth: 2,
                    pointHoverRadius: 6,
                    tension: 0.4, 
                    fill: true, 
                    ...ds
                };
            })},
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                interaction: { mode: 'index', intersect: false },
                plugins: { 
                    legend: { display: datasets.length > 1, labels: { boxWidth: 12, padding: 16 } },
                    tooltip: {
                        backgroundColor: 'rgba(24, 28, 32, 0.95)',
                        titleColor: '#e2e8f0',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true,
                        usePointStyle: true,
                    }
                },
                scales: { 
                    x: { grid: { display: false } }, 
                    y: { grid: { color: defaultColors.grid, borderDash: [4, 4], drawBorder: false }, beginAtZero: true } 
                }, 
                ...opts 
            }
        });
    }

    function bar(canvasId, labels, datasets, opts = {}) {
        return base('bar', canvasId, {
            data: { labels, datasets: datasets.map((ds, i) => ({
                backgroundColor: palette[i] + 'cc', borderColor: palette[i],
                borderWidth: 1, borderRadius: 6, ...ds
            }))},
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: datasets.length > 1, labels: { boxWidth: 12, padding: 16 } } },
                scales: { x: { grid: { display: false } }, y: { grid: { color: defaultColors.grid }, beginAtZero: true } }, ...opts }
        });
    }

    function doughnut(canvasId, labels, data, opts = {}) {
        return base('doughnut', canvasId, {
            data: { labels, datasets: [{ data, backgroundColor: palette.slice(0, data.length), borderWidth: 0, hoverOffset: 8 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 12 } } }, ...opts }
        });
    }

    return { line, bar, doughnut, palette };
})();
