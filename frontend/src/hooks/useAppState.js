import { useState, useEffect } from 'react';
import secureStorage from '../lib/secureStorage';

/**
 * Hook for managing application state with persistent storage
 * @param {string} key - Storage key
 * @param {*} defaultValue - Default value if no stored value exists
 * @returns {[*, function]} - [state, setState] tuple
 */
export function useAppState(key, defaultValue) {
    const [state, setState] = useState(() => {
        return secureStorage.getAppState(key, defaultValue);
    });

    useEffect(() => {
        secureStorage.setAppState(key, state);
    }, [key, state]);

    return [state, setState];
}
