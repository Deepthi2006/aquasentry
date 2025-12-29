let phChart = null;
let turbidityChart = null;
let temperatureChart = null;

const chartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false
        }
    },
    scales: {
        x: {
            grid: {
                color: 'rgba(14, 165, 233, 0.1)'
            },
            ticks: {
                color: '#475569'
            }
        },
        y: {
            grid: {
                color: 'rgba(14, 165, 233, 0.1)'
            },
            ticks: {
                color: '#475569'
            }
        }
    }
};

function createLineChart(ctx, labels, data, label, color, min = null, max = null) {
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: color,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            ...chartConfig,
            scales: {
                ...chartConfig.scales,
                y: {
                    ...chartConfig.scales.y,
                    min: min,
                    max: max
                }
            }
        }
    };
    
    return new Chart(ctx, config);
}

function initCharts(historyData) {
    const labels = historyData.map(h => h.date.split('-').slice(1).join('/'));
    
    const phCtx = document.getElementById('phChart');
    if (phCtx) {
        if (phChart) phChart.destroy();
        phChart = createLineChart(
            phCtx.getContext('2d'),
            labels,
            historyData.map(h => h.ph),
            'pH Level',
            '#0284C7',
            5,
            10
        );
    }
    
    const turbidityCtx = document.getElementById('turbidityChart');
    if (turbidityCtx) {
        if (turbidityChart) turbidityChart.destroy();
        turbidityChart = createLineChart(
            turbidityCtx.getContext('2d'),
            labels,
            historyData.map(h => h.turbidity),
            'Turbidity (NTU)',
            '#0EA5E9',
            0,
            10
        );
    }
    
    const tempCtx = document.getElementById('temperatureChart');
    if (tempCtx) {
        if (temperatureChart) temperatureChart.destroy();
        temperatureChart = createLineChart(
            tempCtx.getContext('2d'),
            labels,
            historyData.map(h => h.temperature),
            'Temperature (°C)',
            '#38BDF8',
            10,
            30
        );
    }
}

function createOverviewChart(tanks) {
    const ctx = document.getElementById('overviewChart');
    if (!ctx) return;
    
    const statusCounts = {
        normal: tanks.filter(t => t.status === 'normal').length,
        warning: tanks.filter(t => t.status === 'warning').length,
        critical: tanks.filter(t => t.status === 'critical').length
    };
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Normal', 'Warning', 'Critical'],
            datasets: [{
                data: [statusCounts.normal, statusCounts.warning, statusCounts.critical],
                backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#475569',
                        padding: 20,
                        usePointStyle: true
                    }
                }
            },
            cutout: '70%'
        }
    });
}

function destroyCharts() {
    if (phChart) { phChart.destroy(); phChart = null; }
    if (turbidityChart) { turbidityChart.destroy(); turbidityChart = null; }
    if (temperatureChart) { temperatureChart.destroy(); temperatureChart = null; }
}

export { initCharts, createOverviewChart, destroyCharts };
