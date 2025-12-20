import { useState, useEffect } from 'react';
import { useToast } from '../components/ToastContext';

export default function useOptimization(strategy, symbol, timeframe, ranges, nTrials, leverage) {
    const toast = useToast();
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(() => {
        const saved = localStorage.getItem('optimization_results');
        return saved ? JSON.parse(saved) : [];
    });
    const [progress, setProgress] = useState({ current: 0, total: 0 });
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [ws, setWs] = useState(null);

    // Reset results when core params change
    useEffect(() => {
        setResults([]);
        setProgress({ current: 0, total: 0 });
    }, [strategy, symbol, timeframe, leverage]);

    // Save results to local storage
    useEffect(() => {
        localStorage.setItem('optimization_results', JSON.stringify(results));
    }, [results]);

    // WebSocket Connection
    useEffect(() => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/optimize`;
        const socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'progress' && data.job_type !== 'ultimate') {
                setIsOptimizing(true);
                setLoading(true);
                setProgress({ current: data.current, total: data.total });
            } else if (data.type === 'complete' && data.job_type !== 'ultimate') {
                // Deduplicate results based on parameters
                const uniqueResults = [];
                const seenParams = new Set();
                for (const result of data.results) {
                    const paramKey = JSON.stringify(Object.keys(result.params).sort().reduce((obj, key) => {
                        obj[key] = result.params[key];
                        return obj;
                    }, {}));
                    if (!seenParams.has(paramKey)) {
                        seenParams.add(paramKey);
                        uniqueResults.push(result);
                    }
                }
                setResults(uniqueResults);
                toast.success("Optimization Complete!");
                setLoading(false);
                setIsOptimizing(false);
            } else if (data.type === 'error' && data.job_type !== 'ultimate') {
                toast.error('Optimization error: ' + data.error);
                setLoading(false);
                setIsOptimizing(false);
            }
        };

        setWs(socket);

        return () => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.close();
            }
        };
    }, [toast]);

    const runOptimization = (STRATEGY_PARAM_KEYS) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            toast.error("WebSocket not connected. Please refresh the page.");
            return;
        }
        setLoading(true);
        setIsOptimizing(true);
        setProgress({ current: 0, total: nTrials });
        setResults([]);

        const validKeys = STRATEGY_PARAM_KEYS[strategy] || [];
        const param_ranges = {};

        for (const [key, range] of Object.entries(ranges)) {
            if (['bb_length', 'short_window', 'long_window', 'rsi_length', 'rsi_buy', 'rsi_sell', 'buy_threshold', 'sell_threshold'].includes(key)) {
                continue;
            }
            if (validKeys.includes(key)) {
                param_ranges[key] = [range.start, range.end, range.step];
            }
        }

        ws.send(JSON.stringify({
            symbol: symbol,
            timeframe: timeframe,
            days: 3,
            strategy: strategy,
            leverage: leverage,
            param_ranges: param_ranges,
            n_trials: nTrials,
            token: localStorage.getItem('token')
        }));
    };

    const clearResults = () => {
        setResults([]);
        localStorage.removeItem('optimization_results');
    };

    return {
        results,
        clearResults,
        loading,
        isOptimizing,
        progress,
        runOptimization
    };
}
