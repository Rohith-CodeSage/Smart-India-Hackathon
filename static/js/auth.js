// Authentication management
class AuthManager {
    constructor() {
        this.baseUrl = '/api/auth';
        this.initializeAuth();
    }

    initializeAuth() {
        // Check if user is on login/register page
        const currentPath = window.location.pathname;
        if (['/login/', '/register/'].includes(currentPath)) {
            this.setupAuthForms();
        }
    }

    setupAuthForms() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin(new FormData(loginForm));
            });
        }

        // Register form  
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister(new FormData(registerForm));
            });
        }
    }

    async handleLogin(formData) {
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            showLoading();
            
            // First establish Django session
            const sessionResponse = await fetch('/auth/session-login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginData)
            });

            const sessionData = await sessionResponse.json();

            if (!sessionResponse.ok) {
                throw new Error(sessionData.detail || 'Login failed');
            }

            // Then get JWT tokens for API calls
            const tokenResponse = await fetch(`${this.baseUrl}/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginData)
            });

            const tokenData = await tokenResponse.json();

            if (tokenResponse.ok) {
                // Store tokens for API calls
                localStorage.setItem('authToken', tokenData.access);
                localStorage.setItem('refreshToken', tokenData.refresh);

                // Get user info
                const userResponse = await fetch('/api/user/profile/', {
                    headers: {
                        'Authorization': `Bearer ${tokenData.access}`
                    }
                });

                if (userResponse.ok) {
                    const userInfo = await userResponse.json();
                    localStorage.setItem('userInfo', JSON.stringify(userInfo));
                }
            }

            showToast('Login successful!', 'success');

            // Redirect based on role from session login
            if (sessionData.role === 'admin') {
                window.location.href = '/admin/dashboard/';
            } else {
                window.location.href = '/citizen/dashboard/';
            }

        } catch (error) {
            console.error('Login error:', error);
            showToast(error.message, 'error');
        } finally {
            hideLoading();
        }
    }

    async handleRegister(formData) {
        const registerData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            phone_number: formData.get('phone_number'),
            role: 'citizen' // Default to citizen role
        };

        // Validate passwords match
        const confirmPassword = formData.get('confirm_password');
        if (registerData.password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            return;
        }

        try {
            showLoading();
            const response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(registerData)
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = Object.values(data).flat().join(', ') || 'Registration failed';
                throw new Error(errorMessage);
            }

            showToast('Registration successful! Please log in.', 'success');
            setTimeout(() => {
                window.location.href = '/login/';
            }, 2000);

        } catch (error) {
            console.error('Registration error:', error);
            showToast(error.message, 'error');
        } finally {
            hideLoading();
        }
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            this.logout();
            return null;
        }

        try {
            const response = await fetch(`${this.baseUrl}/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            localStorage.setItem('authToken', data.access);
            return data.access;

        } catch (error) {
            console.error('Token refresh error:', error);
            // Don't force logout on JWT failure - session might still be valid
            return null;
        }
    }

    logout() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userInfo');
        window.location.href = '/login/';
    }

    isAuthenticated() {
        return !!localStorage.getItem('authToken');
    }

    getUserInfo() {
        const userInfo = localStorage.getItem('userInfo');
        return userInfo ? JSON.parse(userInfo) : null;
    }

    async makeAuthenticatedRequest(url, options = {}) {
        let token = localStorage.getItem('authToken');
        
        if (!token) {
            this.logout();
            return null;
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        let response = await fetch(url, { ...options, headers });

        // If token expired, try to refresh
        if (response.status === 401) {
            token = await this.refreshToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
                response = await fetch(url, { ...options, headers });
            } else {
                return null;
            }
        }

        return response;
    }
}

// Global auth manager instance
const authManager = new AuthManager();

// Global logout function
function logout() {
    authManager.logout();
}

// Export for global use
window.authManager = authManager;