/**
 * ConfigContext - React Context for UI Configuration
 * Provides centralized access to UI config and constructor mode state.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from './api';

// Create contexts
const ConfigContext = createContext(null);
const ConstructorContext = createContext(null);

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
    const [constructorMode, setConstructorMode] = useState(false);
    const [pendingChanges, setPendingChanges] = useState({});
    const [isAdmin, setIsAdmin] = useState(false);

    // Load config on mount
    useEffect(() => {
        loadConfig();
        checkAdminStatus();
    }, []);

    // Check if current user is admin
    const checkAdminStatus = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setIsAdmin(false);
                return;
            }
            const response = await api.get('/auth/me');
            setIsAdmin(response.data?.is_admin || false);
        } catch {
            setIsAdmin(false);
        }
    };

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
        // Check pending changes first
        if (pendingChanges[path] !== undefined) {
            return pendingChanges[path];
        }

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
    }, [config, pendingChanges]);

    // Set a value locally (pending changes)
    const setValue = useCallback((path, value) => {
        setPendingChanges(prev => ({
            ...prev,
            [path]: value
        }));
    }, []);

    // Save all pending changes to backend
    const saveChanges = async () => {
        if (Object.keys(pendingChanges).length === 0) return true;

        try {
            // Apply pending changes to config
            let newConfig = JSON.parse(JSON.stringify(config));

            for (const [path, value] of Object.entries(pendingChanges)) {
                const keys = path.split('.');
                let current = newConfig;

                for (let i = 0; i < keys.length - 1; i++) {
                    if (!(keys[i] in current)) {
                        current[keys[i]] = {};
                    }
                    current = current[keys[i]];
                }
                current[keys[keys.length - 1]] = value;
            }

            await api.put('/constructor/config', { config: newConfig });
            setConfig(newConfig);
            setPendingChanges({});
            return true;
        } catch (err) {
            console.error('Failed to save config:', err);
            return false;
        }
    };

    // Discard pending changes
    const discardChanges = useCallback(() => {
        setPendingChanges({});
    }, []);

    // Toggle constructor mode (admin only)
    const toggleConstructorMode = useCallback(() => {
        if (!isAdmin) return;
        setConstructorMode(prev => !prev);
        if (constructorMode) {
            // Exiting constructor mode - discard unsaved changes
            discardChanges();
        }
    }, [isAdmin, constructorMode, discardChanges]);

    // Check if there are unsaved changes
    const hasChanges = Object.keys(pendingChanges).length > 0;

    const configValue = {
        config,
        loading,
        error,
        getValue,
        reload: loadConfig
    };

    const constructorValue = {
        constructorMode,
        toggleConstructorMode,
        isAdmin,
        setValue,
        saveChanges,
        discardChanges,
        hasChanges,
        pendingChanges
    };

    return (
        <ConfigContext.Provider value={configValue}>
            <ConstructorContext.Provider value={constructorValue}>
                {children}
            </ConstructorContext.Provider>
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
 * Hook to access constructor mode state
 */
export function useConstructorMode() {
    const context = useContext(ConstructorContext);
    if (!context) {
        throw new Error('useConstructorMode must be used within a ConfigProvider');
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
