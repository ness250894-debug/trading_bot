/**
 * Secure storage service for authentication tokens.
 * Migrates from localStorage to more secure storage mechanisms.
 */

class SecureStorage {
    constructor() {
        // Use sessionStorage for tokens (better than localStorage)
        // In production, should use httpOnly cookies set by backend
        this.storage = sessionStorage;
    }

    // Authentication tokens
    setToken(token) {
        if (!token) {
            console.warn('Attempting to set empty token');
            return;
        }
        this.storage.setItem('auth_token', token);
    }

    getToken() {
        return this.storage.getItem('auth_token');
    }

    clearToken() {
        this.storage.removeItem('auth_token');
    }

    // Application state (can stay in localStorage)
    setAppState(key, value) {
        try {
            localStorage.setItem(`app_${key}`, JSON.stringify(value));
        } catch (error) {
            console.error('Failed to save app state:', error);
        }
    }

    getAppState(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`app_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to load app state:', error);
            return defaultValue;
        }
    }

    clearAppState(key) {
        localStorage.removeItem(`app_${key}`);
    }

    // Clear all
    clearAll() {
        this.clearToken();
        // Clear all app state
        Object.keys(localStorage)
            .filter(key => key.startsWith('app_'))
            .forEach(key => localStorage.removeItem(key));
    }
}

export default new SecureStorage();
