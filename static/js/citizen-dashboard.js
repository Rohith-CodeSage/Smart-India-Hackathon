// Citizen Dashboard JavaScript
class CitizenDashboard {
    constructor() {
        this.reports = [];
        this.filteredReports = [];
        this.currentFilters = {
            status: '',
            category: ''
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadReports();
    }

    setupEventListeners() {
        // Filter event listeners
        const statusFilter = document.getElementById('status-filter');
        const categoryFilter = document.getElementById('category-filter');
        
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value;
                this.applyFilters();
            });
        }
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', (e) => {
                this.currentFilters.category = e.target.value;
                this.applyFilters();
            });
        }
    }

    async loadReports() {
        try {
            const response = await fetch('/api/reports/user/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load reports');
            }
            
            const data = await response.json();
            this.reports = data;
            this.updateStats();
            this.applyFilters();
            
        } catch (error) {
            console.error('Error loading reports:', error);
            showToast('Failed to load reports', 'error');
            this.showNoReports();
        } finally {
            this.hideLoading();
        }
    }

    updateStats() {
        const stats = {
            total: this.reports.length,
            submitted: this.reports.filter(r => r.status === 'submitted').length,
            in_progress: this.reports.filter(r => r.status === 'in_progress').length,
            resolved: this.reports.filter(r => r.status === 'resolved').length
        };

        document.getElementById('total-reports').textContent = stats.total;
        document.getElementById('pending-reports').textContent = stats.submitted;
        document.getElementById('in-progress-reports').textContent = stats.in_progress;
        document.getElementById('resolved-reports').textContent = stats.resolved;
    }

    applyFilters() {
        this.filteredReports = this.reports.filter(report => {
            if (this.currentFilters.status && report.status !== this.currentFilters.status) {
                return false;
            }
            if (this.currentFilters.category && report.category !== this.currentFilters.category) {
                return false;
            }
            return true;
        });

        this.renderReports();
    }

    renderReports() {
        const container = document.getElementById('reports-container');
        const noReportsEl = document.getElementById('no-reports');

        if (!container) return;

        if (this.filteredReports.length === 0) {
            container.classList.add('hidden');
            if (noReportsEl) {
                noReportsEl.classList.remove('hidden');
            }
            return;
        }

        if (noReportsEl) {
            noReportsEl.classList.add('hidden');
        }
        container.classList.remove('hidden');

        container.innerHTML = this.filteredReports.map(report => this.renderReportItem(report)).join('');
    }

    renderReportItem(report) {
        const statusClass = `status-${report.status.replace('_', '-')}`;
        const priorityClass = `priority-${report.priority}`;
        
        return `
            <div class="report-item" data-report-id="${report.id}">
                <div class="report-header">
                    <div>
                        <div class="report-title">${report.title}</div>
                        <div class="report-meta">
                            <span><i class="fas fa-tag"></i> ${report.category_display}</span>
                            <span><i class="fas fa-calendar"></i> ${this.formatDate(report.created_at)}</span>
                            <span><i class="fas fa-map-marker-alt"></i> ${report.address || 'Location provided'}</span>
                        </div>
                    </div>
                    <div class="d-flex gap-1" style="flex-direction: column; align-items: flex-end;">
                        <span class="status-badge ${statusClass}">
                            ${this.getStatusIcon(report.status)} ${report.status_display}
                        </span>
                        <span class="status-badge ${priorityClass}">
                            ${this.getPriorityIcon(report.priority)} ${report.priority_display}
                        </span>
                    </div>
                </div>
                
                <div class="report-description">
                    ${report.description}
                </div>
                
                ${report.image ? `
                    <div class="report-image mb-2">
                        <img src="${report.image}" alt="Report image" style="max-width: 200px; border-radius: 8px;">
                    </div>
                ` : ''}
                
                <div class="report-actions">
                    <button onclick="viewReportDetails(${report.id})" class="btn btn-outline">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    ${report.status === 'submitted' ? `
                        <button onclick="editReport(${report.id})" class="btn btn-secondary">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    getStatusIcon(status) {
        const icons = {
            'submitted': 'fas fa-clock',
            'in_progress': 'fas fa-cog',
            'resolved': 'fas fa-check-circle',
            'rejected': 'fas fa-times-circle'
        };
        return `<i class="${icons[status] || 'fas fa-question-circle'}"></i>`;
    }

    getPriorityIcon(priority) {
        const icons = {
            'low': 'fas fa-arrow-down',
            'medium': 'fas fa-minus',
            'high': 'fas fa-arrow-up',
            'urgent': 'fas fa-exclamation'
        };
        return `<i class="${icons[priority] || 'fas fa-minus'}"></i>`;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    hideLoading() {
        const loadingEl = document.getElementById('reports-loading');
        if (loadingEl) {
            loadingEl.classList.add('hidden');
        }
    }

    showNoReports() {
        const container = document.getElementById('reports-container');
        const noReportsEl = document.getElementById('no-reports');
        
        if (container) container.classList.add('hidden');
        if (noReportsEl) noReportsEl.classList.remove('hidden');
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Global functions
function refreshReports() {
    if (window.citizenDashboard) {
        showToast('Refreshing reports...', 'info');
        window.citizenDashboard.loadReports();
    }
}

function viewReportDetails(reportId) {
    // TODO: Implement report details modal or page
    showToast('Report details view coming soon', 'info');
}

function editReport(reportId) {
    // TODO: Implement report editing
    showToast('Report editing coming soon', 'info');
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.citizenDashboard = new CitizenDashboard();
});