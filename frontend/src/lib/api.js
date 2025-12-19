import axios from 'axios';

// Use environment variable or fallback to relative path for production
const baseURL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle 401s
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Retry logic for 5xx errors or network errors
        if (error.response && (error.response.status >= 500 && error.response.status <= 599) || error.message === 'Network Error') {
            originalRequest._retryCount = originalRequest._retryCount || 0;
            const maxRetries = 3;

            if (originalRequest._retryCount < maxRetries) {
                originalRequest._retryCount += 1;

                // Exponential backoff: 1s, 2s, 4s...
                const delay = Math.pow(2, originalRequest._retryCount - 1) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));

                return api(originalRequest);
            }
        }

        if (error.response && error.response.status === 401) {
            // Don't redirect if this is a login or signup request (wrong password is expected)
            const isAuthEndpoint = error.config?.url?.includes('/auth/login') ||
                error.config?.url?.includes('/auth/signup');

            if (!isAuthEndpoint && !originalRequest._retry) {
                // Clear token and redirect to login for protected routes
                localStorage.removeItem('token');
                if (window.location.pathname !== '/signup' &&
                    window.location.pathname !== '/') {
                    window.location.href = '/';
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;
