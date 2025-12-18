/**
 * ConfigContext - React Context for UI Configuration
 * Provides centralized access to UI config.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from './api';

// Create contexts
const ConfigContext = createContext(null);

// Default config fallback
const DEFAULT_CONFIG = {
    branding: { appName: 'TradingBot Pro', tagline: 'Smart Crypto Trading' },
    theme: { primaryColor: '#8b5cf6', accentColor: '#10b981' },
    pages: {},
    widgets: {},
    tables: {},
    labels: { common: {}, auth: {}, subscription: {} }
};

/**
 * Config Provider Component
 * Wraps the app to provide UI configuration to all components.
 */
export function ConfigProvider({ children }) {
    const [config, setConfig] = useState(DEFAULT_CONFIG);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Load config on mount
    useEffect(() => {
        loadConfig();
    }, []);

    // Load config from backend
    const loadConfig = async () => {
        try {
            setLoading(true);
            const response = await api.get('/constructor/config');
            setConfig(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to load UI config:', err);
            setError(err.message);
            // Use default config on error
            setConfig(DEFAULT_CONFIG);
        } finally {
            setLoading(false);
        }
    };

    // Get a nested config value using dot notation
    const getValue = useCallback((path, defaultValue = '') => {
        const keys = path.split('.');
        let result = config;

        for (const key of keys) {
            if (result && typeof result === 'object' && key in result) {
                result = result[key];
            } else {
                return defaultValue;
            }
        }

        return result ?? defaultValue;
    }, [config]);

    const configValue = {
        config,
        loading,
        error,
        getValue,
        reload: loadConfig
    };

    return (
        <ConfigContext.Provider value={configValue}>
            {children}
        </ConfigContext.Provider>
    );
}

/**
 * Hook to access UI configuration
 */
export function useConfig() {
    const context = useContext(ConfigContext);
    if (!context) {
        throw new Error('useConfig must be used within a ConfigProvider');
    }
    return context;
}


/**
 * Convenience hook to get a config value with default
 */
export function useConfigValue(path, defaultValue = '') {
    const { getValue } = useConfig();
    return getValue(path, defaultValue);
}

export default ConfigProvider;
