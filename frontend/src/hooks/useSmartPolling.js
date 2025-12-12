import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Smart Polling Hook
 * Pauses polling when browser tab is hidden to save resources
 */
export const useSmartPolling = (
    fetchFn,
    intervalMs = 30000,
    options = {}
) => {
    const {
        enabled = true,
        pauseWhenHidden = true,
        immediateOnVisible = true,
        onError = null
    } = options;

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isVisible, setIsVisible] = useState(!document.hidden);
    const [lastFetch, setLastFetch] = useState(null);

    const intervalRef = useRef(null);
    const fetchRef = useRef(fetchFn);
    fetchRef.current = fetchFn;

    // Track document visibility
    useEffect(() => {
        if (!pauseWhenHidden) return;

        const handleVisibilityChange = () => {
            setIsVisible(!document.hidden);
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [pauseWhenHidden]);

    // Fetch function
    const doFetch = useCallback(async () => {
        if (!enabled) return;

        try {
            setLoading(true);
            const result = await fetchRef.current();
            setData(result);
            setError(null);
            setLastFetch(Date.now());
        } catch (err) {
            setError(err);
            if (onError) onError(err);
        } finally {
            setLoading(false);
        }
    }, [enabled, onError]);

    // Initial fetch and polling setup
    useEffect(() => {
        if (!enabled) return;

        // Initial fetch
        doFetch();

        // Clear any existing interval
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        // Only poll if visible (or pauseWhenHidden is false)
        if (!pauseWhenHidden || isVisible) {
            intervalRef.current = setInterval(doFetch, intervalMs);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [enabled, intervalMs, isVisible, pauseWhenHidden, doFetch]);

    // Fetch immediately when becoming visible
    useEffect(() => {
        if (immediateOnVisible && isVisible && lastFetch) {
            const timeSinceLastFetch = Date.now() - lastFetch;
            // Only fetch if more than half the interval has passed
            if (timeSinceLastFetch > intervalMs / 2) {
                doFetch();
            }
        }
    }, [isVisible, immediateOnVisible, intervalMs, lastFetch, doFetch]);

    return {
        data,
        loading,
        error,
        isVisible,
        refetch: doFetch,
        lastFetch
    };
};

/**
 * Page Visibility Hook
 * Simple hook to track if the page is visible
 */
export const usePageVisibility = () => {
    const [isVisible, setIsVisible] = useState(!document.hidden);

    useEffect(() => {
        const handleVisibilityChange = () => {
            setIsVisible(!document.hidden);
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []);

    return isVisible;
};

/**
 * Smart Interval Hook
 * setInterval that pauses when tab is hidden
 */
export const useSmartInterval = (callback, delay, pauseWhenHidden = true) => {
    const savedCallback = useRef(callback);
    const [isVisible, setIsVisible] = useState(!document.hidden);

    // Remember the latest callback
    useEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    // Track visibility
    useEffect(() => {
        if (!pauseWhenHidden) return;

        const handleVisibilityChange = () => {
            setIsVisible(!document.hidden);
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [pauseWhenHidden]);

    // Set up the interval
    useEffect(() => {
        if (delay === null) return;
        if (pauseWhenHidden && !isVisible) return;

        const tick = () => savedCallback.current();
        const id = setInterval(tick, delay);

        return () => clearInterval(id);
    }, [delay, isVisible, pauseWhenHidden]);
};

export default useSmartPolling;
