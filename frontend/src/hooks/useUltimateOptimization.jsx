import { useState, useEffect, useRef } from 'react';
import { useToast } from '../components/ToastContext';
import { useModal } from '../components/Modal';
import { Crown } from 'lucide-react';

export default function useUltimateOptimization(ultimateSymbol, presets, strategyInfo, STRATEGY_PARAM_KEYS, subscription, leverage = 10) {
    const toast = useToast();
    const modal = useModal();
    const [isUltimateOptimizing, setIsUltimateOptimizing] = useState(false);
    const [ultimateResults, setUltimateResults] = useState(() => {
        const saved = localStorage.getItem('ultimate_optimization_results');
        return saved ? JSON.parse(saved) : [];
    });
    const [progress, setProgress] = useState({ current: 0, total: 0 });
    const [ws, setWs] = useState(null);

    useEffect(() => {
        localStorage.setItem('ultimate_optimization_results', JSON.stringify(ultimateResults));
    }, [ultimateResults]);

    useEffect(() => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/optimize`;
        const socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const isUltimate = data.job_type === 'ultimate';

            if (isUltimate) {
                if (data.type === 'progress') {
                    setIsUltimateOptimizing(true);
                    // If it's the start of a task or sub-progress
                    if (data.total) setProgress({ current: data.current, total: data.total });

                    if (data.details && data.details.type === 'strategy_complete') {
                        const newResults = data.details.results;
                        setUltimateResults(prev => {
                            const existing = new Set(prev.map(p => JSON.stringify(p.params) + p.strategy));
                            const uniqueNew = newResults.filter(r => !existing.has(JSON.stringify(r.params) + r.strategy));
                            return [...prev, ...uniqueNew];
                        });
                    }
                } else if (data.type === 'complete') {
                    toast.success("Ultimate Optimization Complete!");
                    setIsUltimateOptimizing(false);
                } else if (data.type === 'error') {
                    toast.error('Ultimate Optimization error: ' + data.error);
                    setIsUltimateOptimizing(false);
                }
            }
        };

        setWs(socket);

        return () => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.close();
            }
        };
    }, [toast]);

    const runUltimateOptimization = () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            toast.error("WebSocket not connected. Please refresh the page.");
            return;
        }

        if (!subscription || subscription.plan === 'free') {
            modal.show({
                title: '🚀 Unlock Ultimate Optimization',
                content: (
                    <div className="space-y-4">
                        <p className="text-muted-foreground">
                            The <span className="text-foreground font-semibold">Ultimate Optimization</span> tool runs ALL strategies automatically to find the absolute best market fit.
                        </p>
                        <p className="text-muted-foreground">
                            Upgrade to <span className="text-amber-400 font-bold">Pro</span> or <span className="text-purple-400 font-bold">Admin</span> to access this powerful feature.
                        </p>
                        <button
                            onClick={() => {
                                modal.hide();
                                window.location.href = '/pricing';
                            }}
                            className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white rounded-xl font-semibold transition-all shadow-lg shadow-amber-500/25 flex items-center justify-center gap-2"
                        >
                            <Crown size={18} />
                            Upgrade Now
                        </button>
                    </div>
                )
            });
            return;
        }

        setIsUltimateOptimizing(true);
        setUltimateResults([]);

        const prepareParamRanges = (strategyName, ranges) => {
            const validKeys = STRATEGY_PARAM_KEYS[strategyName] || [];
            const param_ranges = {};
            for (const [key, range] of Object.entries(ranges)) {
                if (validKeys.includes(key)) {
                    param_ranges[key] = [range.start, range.end, range.step];
                }
            }
            return param_ranges;
        };

        const tasks = [];
        for (const stratName of Object.keys(strategyInfo)) {
            const stratPresets = presets[stratName];
            if (stratPresets && stratPresets.length > 0) {
                const preset = stratPresets[stratPresets.length - 1];
                const taskRange = prepareParamRanges(stratName, preset.ranges);

                tasks.push({
                    strategy: stratName,
                    symbol: ultimateSymbol,
                    timeframe: preset.timeframe || '1h',
                    days: 3,
                    param_ranges: taskRange,
                    leverage: leverage,
                    n_trials: 30
                });
            }
        }

        ws.send(JSON.stringify({
            type: "ultimate",
            tasks: tasks,
            token: localStorage.getItem('token')
        }));
    };

    const clearUltimateResults = () => {
        setUltimateResults([]);
        localStorage.removeItem('ultimate_optimization_results');
    };

    return {
        ultimateResults,
        clearUltimateResults,
        isUltimateOptimizing,
        runUltimateOptimization,
        progress
    };
}
