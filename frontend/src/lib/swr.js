import useSWR from 'swr';
import api from './api';

// Custom fetcher that uses our configured axios instance
export const fetcher = async (url) => {
    const response = await api.get(url);
    return response.data;
};

// SWR configuration with sensible defaults
export const swrConfig = {
    fetcher,
    revalidateOnFocus: false, // Don't refetch when window regains focus
    revalidateOnReconnect: true, // Refetch when reconnecting
    dedupingInterval: 2000, // Deduplicate requests within 2s
    errorRetryCount: 3, // Retry failed requests 3 times
    errorRetryInterval: 5000, // Wait 5s between retries
};

// Custom hook for data that rarely changes (user info, plans, etc.)
export const useStaticData = (url, options = {}) => {
    return useSWR(url, fetcher, {
        ...swrConfig,
        revalidateIfStale: false, // Don't revalidate stale data automatically
        revalidateOnMount: true, // Only fetch on mount
        dedupingInterval: 60000, // Cache for 1 minute
        ...options,
    });
};

// Custom hook for frequently changing data (bot status, trades)
export const useDynamicData = (url, refreshInterval = null, options = {}) => {
    return useSWR(url, fetcher, {
        ...swrConfig,
        refreshInterval, // Auto-refresh at specified interval
        ...options,
    });
};

export default useSWR;
