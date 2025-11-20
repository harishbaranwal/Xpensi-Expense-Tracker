/**
 * Dashboard JavaScript - xpensi App
 * Handles Chart.js charts and dashboard functionality
 */

// Global Chart.js configuration
Chart.defaults.font.family = 'Nunito, system-ui, sans-serif';
Chart.defaults.color = '#6B7280';
// Force Chart.js locale to English to avoid browser/Django locale affecting chart labels
// (prevents labels like "Fecha" when the browser locale is Spanish)
Chart.defaults.locale = 'en';

// Event listener para auto-refresh del dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Listener to reload the page after adding an expense from the dashboard
    document.body.addEventListener('refreshDashboard', function() {
        setTimeout(function() {
            window.location.reload();
        }, 1500); // Esperar 1.5 segundos para ver el mensaje
    });
});

/**
 * Initialize the categories doughnut chart
 * @param {Object} data - Data for the chart
 */
function initCategoryChart(data) {
    const categoryCtx = document.getElementById('categoryChart');
    if (!categoryCtx) return;
    
    new Chart(categoryCtx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.amounts,
                backgroundColor: data.colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return context.label + ': ₹' + value.toLocaleString() + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize the trend line chart
 * @param {Object} data - Data for the chart
 */
function initTrendChart(data) {
    const trendCtx = document.getElementById('trendChart');
    if (!trendCtx) return;
    
    new Chart(trendCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Daily Expenses',
                data: data.amounts,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3B82F6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Expense: ₹' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Amountakds (₹)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize all dashboard charts
 * @param {Object} chartData - All chart data
 */
function initDashboardCharts(chartData) {
    // Initialize categories chart if there is data
    if (chartData.categories && chartData.categories.length > 0) {
        initCategoryChart({
            categories: chartData.categories,
            amounts: chartData.amounts,
            colors: chartData.colors
        });
    }
    
    // Initialize trend chart if there is data
    if (chartData.dates && chartData.dates.length > 0) {
        initTrendChart({
            dates: chartData.dates,
            amounts: chartData.dailyAmounts
        });
    }
} 