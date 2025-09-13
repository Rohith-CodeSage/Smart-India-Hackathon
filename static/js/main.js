// Global variables
let map = null;
let userLocation = null;
let apiBaseUrl = '/api';

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// App initialization
function initializeApp() {
    setupNavigation();
    setupLocationServices();
    checkAuthStatus();
}

// Navigation setup
function setupNavigation() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
}

// Location services
function setupLocationServices() {
    if (navigator.geolocation) {
        getCurrentLocation();
    }
}

function getCurrentLocation() {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            };
            console.log('User location obtained:', userLocation);
        },
        (error) => {
            console.warn('Geolocation error:', error.message);
            showToast('Location access denied. You can still submit reports by clicking on the map.', 'warning');
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

// Authentication helper
function getAuthToken() {
    return localStorage.getItem('authToken');
}

function setAuthToken(token) {
    localStorage.setItem('authToken', token);
}

function removeAuthToken() {
    localStorage.removeItem('authToken');
}

function checkAuthStatus() {
    const token = getAuthToken();
    if (token) {
        // Verify token is still valid
        fetch('/api/auth/token/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token })
        })
        .then(response => {
            if (!response.ok) {
                removeAuthToken();
                if (window.location.pathname !== '/login/') {
                    window.location.href = '/login/';
                }
            }
        })
        .catch(() => {
            removeAuthToken();
        });
    }
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    const token = getAuthToken();
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        headers: defaultHeaders,
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        showLoading();
        const response = await fetch(`${apiBaseUrl}${endpoint}`, config);
        
        if (response.status === 401) {
            removeAuthToken();
            window.location.href = '/login/';
            return;
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'API Error');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

// Loading spinner
function showLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.classList.remove('hidden');
    }
}

function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.classList.add('hidden');
    }
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="${iconMap[type]}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, duration);
}

// Form helpers
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const errors = [];
    
    for (const [fieldName, fieldRules] of Object.entries(rules)) {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) continue;
        
        const value = field.value.trim();
        
        if (fieldRules.required && !value) {
            errors.push(`${fieldRules.label || fieldName} is required`);
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
        
        if (value && fieldRules.pattern && !fieldRules.pattern.test(value)) {
            errors.push(`${fieldRules.label || fieldName} format is invalid`);
            field.classList.add('error');
            isValid = false;
        }
        
        if (value && fieldRules.minLength && value.length < fieldRules.minLength) {
            errors.push(`${fieldRules.label || fieldName} must be at least ${fieldRules.minLength} characters`);
            field.classList.add('error');
            isValid = false;
        }
    }
    
    if (!isValid) {
        showToast(errors[0], 'error');
    }
    
    return isValid;
}

// Map utilities
function initializeMap(elementId, options = {}) {
    const element = document.getElementById(elementId);
    if (!element) return null;
    
    const defaultOptions = {
        center: userLocation ? [userLocation.latitude, userLocation.longitude] : [40.7128, -74.0060], // Default to NYC
        zoom: userLocation ? 15 : 10,
        scrollWheelZoom: true
    };
    
    map = L.map(elementId, { ...defaultOptions, ...options });
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    return map;
}

function addMapMarker(lat, lng, options = {}) {
    if (!map) return null;
    
    const marker = L.marker([lat, lng], options).addTo(map);
    
    if (options.popup) {
        marker.bindPopup(options.popup);
    }
    
    return marker;
}

// Date formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffDays > 0) {
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMinutes > 0) {
        return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    } else {
        return 'Just now';
    }
}

// File upload helper
function handleFileUpload(inputElement, options = {}) {
    const file = inputElement.files[0];
    if (!file) return null;
    
    const maxSize = options.maxSize || 5 * 1024 * 1024; // 5MB default
    const allowedTypes = options.allowedTypes || ['image/jpeg', 'image/png', 'image/gif'];
    
    if (file.size > maxSize) {
        showToast('File size too large. Maximum 5MB allowed.', 'error');
        inputElement.value = '';
        return null;
    }
    
    if (!allowedTypes.includes(file.type)) {
        showToast('Invalid file type. Only images are allowed.', 'error');
        inputElement.value = '';
        return null;
    }
    
    return file;
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global use
window.appUtils = {
    apiCall,
    showToast,
    validateForm,
    initializeMap,
    addMapMarker,
    formatDate,
    formatRelativeTime,
    handleFileUpload,
    debounce,
    getCurrentLocation,
    showLoading,
    hideLoading
};