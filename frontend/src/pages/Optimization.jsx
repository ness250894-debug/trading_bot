import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Play, TrendingUp, Activity, Settings, Info, CheckCircle, AlertCircle, Sliders, ArrowUp, ArrowDown, ArrowUpDown, Crown, Lock } from 'lucide-react';
import { useToast } from '../components/ToastContext';
import { useModal } from '../components/Modal';

import PlanGate from '../components/PlanGate';
import { formatLabel } from '../lib/utils';

// --- Helper Components ---

const Tooltip = ({ content }) => (
    <div className="group relative inline-block ml-2">
        <Info size={14} className="text-muted-foreground hover:text-primary cursor-help transition-colors" />
        <div className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity absolute z-50 w-64 p-3 mt-2 text-xs text-popover-foreground bg-popover/90 backdrop-blur-md rounded-xl shadow-xl -left-28 border border-white/10 pointer-events-none">
            {content}
        </div>
    </div>
);

const SliderInput = ({ label, value, min, max, step, onChange, description }) => {
    return (
        <div className="mb-3 group">
            <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                    {label}
                    {description && <Tooltip content={description} />}
                </label>
                <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
                    {value}
                </span>
            </div>
            <div className="flex items-center gap-2">
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary hover:accent-primary/80 transition-all"
                />
                <input
                    type="number"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-16 bg-black/20 border border-white/10 rounded-md px-2 py-1 text-xs text-right focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                />
            </div>
        </div>
    );
};

// --- Configuration Data ---

const strategyInfo = {
    'SMA Crossover': "A classic trend-following strategy. It buys when a short-term moving average crosses above a long-term one (bullish signal) and sells when it crosses below (bearish signal). Best for trending markets.",
    'Mean Reversion': "Assumes prices will revert to their average. Uses Bollinger Bands and RSI to identify overbought (sell) or oversold (buy) conditions. Best for ranging/sideways markets.",
    'RSI': "Uses the Relative Strength Index to find momentum. Buys when RSI is low (oversold) and sells when RSI is high (overbought). Simple and effective for catching reversals.",
    'MACD': "Moving Average Convergence Divergence. A momentum indicator that follows trends. Good for identifying the strength and direction of a trend.",
    'Bollinger Breakout': "Buys when price breaks above the upper Bollinger Band with volume confirmation. Sells when price drops below the middle band.",
    'Momentum': "Uses Rate of Change (ROC) and RSI to identify strong momentum. Buys when momentum is high and RSI is not overbought.",
    'DCA Dip': "Dollar Cost Averaging on dips. Buys when price drops below a short-term EMA while above a long-term EMA (uptrend)."
};

const parameterInfo = {
    fast_period: "The period for the faster moving average. A smaller number makes it more sensitive to recent price changes.",
    slow_period: "The period for the slower moving average. A larger number smooths out noise but reacts slower to trends.",
    bb_period: "The number of periods used for the Bollinger Bands moving average.",
    bb_std: "Standard Deviations for the bands. Higher values make the bands wider, requiring more extreme price moves to trigger signals.",
    rsi_period: "The lookback period for RSI calculation. Standard is 14.",
    rsi_oversold: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    rsi_overbought: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    period: "The lookback period for the indicator.",
    oversold: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    overbought: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    signal_period: "The EMA period for the signal line.",
    volume_factor: "Multiplier for volume to confirm a breakout. Volume must be > average volume * factor.",
    roc_period: "The period for Rate of Change calculation.",
    rsi_min: "Minimum RSI required to enter a momentum trade.",
    rsi_max: "Maximum RSI allowed to enter (to avoid buying tops).",
    ema_long: "Long-term EMA period to define the major trend.",
    ema_short: "Short-term EMA period to define the dip."
};

const paramLimits = {
    fast_period: { min: 2, max: 50, step: 1 },
    slow_period: { min: 10, max: 200, step: 5 },
    bb_period: { min: 5, max: 50, step: 1 },
    bb_std: { min: 0.5, max: 4.0, step: 0.1 },
    rsi_period: { min: 2, max: 30, step: 1 },
    rsi_oversold: { min: 5, max: 45, step: 1 },
    rsi_overbought: { min: 55, max: 95, step: 1 },
    period: { min: 2, max: 50, step: 1 },
    oversold: { min: 5, max: 45, step: 1 },
    overbought: { min: 55, max: 95, step: 1 },
    signal_period: { min: 2, max: 30, step: 1 },
    volume_factor: { min: 1.0, max: 5.0, step: 0.1 },
    roc_period: { min: 2, max: 50, step: 1 },
    rsi_min: { min: 30, max: 60, step: 1 },
    rsi_max: { min: 60, max: 90, step: 1 },
    ema_long: { min: 50, max: 300, step: 10 },
    ema_short: { min: 5, max: 50, step: 1 }
};

const presets = {
    'SMA Crossover': [
        { name: 'Conservative', timeframe: '1h', ranges: { fast_period: { start: 10, end: 20, step: 2 }, slow_period: { start: 50, end: 100, step: 10 } } },
        { name: 'Aggressive', timeframe: '5m', ranges: { fast_period: { start: 3, end: 10, step: 1 }, slow_period: { start: 15, end: 40, step: 5 } } },
        { name: 'Wide Search', timeframe: '15m', ranges: { fast_period: { start: 2, end: 30, step: 2 }, slow_period: { start: 20, end: 150, step: 10 } } }
    ],
    'Mean Reversion': [
        { name: 'Standard', timeframe: '1h', ranges: { bb_period: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, rsi_period: { start: 14, end: 14, step: 1 }, rsi_oversold: { start: 30, end: 30, step: 1 }, rsi_overbought: { start: 70, end: 70, step: 1 } } },
        { name: 'Volatile Market', timeframe: '15m', ranges: { bb_period: { start: 10, end: 30, step: 5 }, bb_std: { start: 2.0, end: 3.0, step: 0.2 }, rsi_period: { start: 10, end: 20, step: 2 }, rsi_oversold: { start: 20, end: 40, step: 5 }, rsi_overbought: { start: 60, end: 80, step: 5 } } }
    ],
    'RSI': [
        { name: 'Scalping', timeframe: '1m', ranges: { period: { start: 5, end: 10, step: 1 }, oversold: { start: 20, end: 30, step: 2 }, overbought: { start: 70, end: 80, step: 2 } } },
        { name: 'Swing', timeframe: '4h', ranges: { period: { start: 14, end: 28, step: 2 }, oversold: { start: 30, end: 40, step: 2 }, overbought: { start: 60, end: 70, step: 2 } } }
    ],
    'MACD': [
        { name: 'Standard', timeframe: '1h', ranges: { fast_period: { start: 12, end: 12, step: 1 }, slow_period: { start: 26, end: 26, step: 1 }, signal_period: { start: 9, end: 9, step: 1 } } },
        { name: 'Fast', timeframe: '15m', ranges: { fast_period: { start: 5, end: 15, step: 1 }, slow_period: { start: 15, end: 30, step: 2 }, signal_period: { start: 5, end: 10, step: 1 } } }
    ],
    'Bollinger Breakout': [
        { name: 'Standard', timeframe: '1h', ranges: { bb_period: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, volume_factor: { start: 1.5, end: 1.5, step: 0.1 } } },
        { name: 'Volatile', timeframe: '15m', ranges: { bb_period: { start: 10, end: 30, step: 2 }, bb_std: { start: 1.5, end: 2.5, step: 0.1 }, volume_factor: { start: 1.2, end: 2.0, step: 0.1 } } }
    ],
    'Momentum': [
        { name: 'Standard', timeframe: '1h', ranges: { roc_period: { start: 10, end: 10, step: 1 }, rsi_period: { start: 14, end: 14, step: 1 }, rsi_min: { start: 50, end: 50, step: 1 }, rsi_max: { start: 70, end: 70, step: 1 } } },
        { name: 'Scalp', timeframe: '5m', ranges: { roc_period: { start: 5, end: 15, step: 1 }, rsi_period: { start: 7, end: 14, step: 1 }, rsi_min: { start: 40, end: 55, step: 5 }, rsi_max: { start: 65, end: 80, step: 5 } } }
    ],
    'DCA Dip': [
        { name: 'Standard', timeframe: '4h', ranges: { ema_long: { start: 200, end: 200, step: 10 }, ema_short: { start: 20, end: 20, step: 1 } } },
        { name: 'Aggressive', timeframe: '1h', ranges: { ema_long: { start: 100, end: 200, step: 20 }, ema_short: { start: 10, end: 30, step: 2 } } }
    ]
};

const STRATEGY_NAME_MAP = {
    'SMA Crossover': 'sma_crossover',
    'Mean Reversion': 'mean_reversion',
    'RSI': 'rsi',
    'MACD': 'macd',
    'Bollinger Breakout': 'bollinger_breakout',
    'Momentum': 'momentum',
    'DCA Dip': 'dca_dip'
};

const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function Optimization() {
    const toast = useToast();
    const modal = useModal();
    const [strategy, setStrategy] = useState(() => localStorage.getItem('optimization_strategy') || 'SMA Crossover');
    const [timeframe, setTimeframe] = useState(() => localStorage.getItem('optimization_timeframe') || '1m');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(() => {
        const saved = localStorage.getItem('optimization_results');
        return saved ? JSON.parse(saved) : [];
    });

    const [ranges, setRanges] = useState(() => {
        const saved = localStorage.getItem('optimization_ranges');
        if (saved) {
            const parsed = JSON.parse(saved);
            // Check for legacy keys and discard if found
            if (parsed.short_window || parsed.rsi_length || parsed.bb_length) {
                return {
                    fast_period: { start: 5, end: 20, step: 5 },
                    slow_period: { start: 30, end: 60, step: 10 }
                };
            }
            return parsed;
        }
        return {
            fast_period: { start: 5, end: 20, step: 5 },
            slow_period: { start: 30, end: 60, step: 10 }
        };
    });

    const [progress, setProgress] = useState({ current: 0, total: 0 });
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: 'return', direction: 'desc' });
    const [subscription, setSubscription] = useState(null);

    // Ultimate Optimization State
    const [isUltimateOptimizing, setIsUltimateOptimizing] = useState(false);
    const [ultimateResults, setUltimateResults] = useState([]);
    const globalQueueRef = React.useRef([]);
    const ultimateOptimizingRef = React.useRef(false);

    // Fetch subscription status
    useEffect(() => {
        api.get('/billing/status')
            .then(res => setSubscription(res.data))
            .catch(err => console.error("Failed to fetch subscription:", err));
    }, []);

    const strategies = Object.keys(strategyInfo);

    const handleStrategyChange = (e) => {
        const newStrategy = e.target.value;
        setStrategy(newStrategy);
        setResults([]);
        if (presets[newStrategy] && presets[newStrategy].length > 0) {
            setRanges(presets[newStrategy][0].ranges);
        }
    };

    const applyPreset = (preset) => {
        setRanges(preset.ranges);
        if (preset.timeframe) {
            setTimeframe(preset.timeframe);
        }
    };

    const handleRangeChange = (param, field, value) => {
        setRanges(prev => {
            const currentRange = prev[param];
            let newValue = parseFloat(value);
            let newRange = { ...currentRange, [field]: newValue };

            if (field === 'start') {
                if (newValue > currentRange.end) {
                    newValue = Math.min(newValue, currentRange.end);
                    newRange.start = newValue;
                }
            } else if (field === 'end') {
                if (newValue < currentRange.start) {
                    newValue = Math.max(newValue, currentRange.start);
                    newRange.end = newValue;
                }
            }

            return { ...prev, [param]: newRange };
        });
    };

    const handleSort = (key) => {
        setSortConfig((current) => {
            if (current.key === key) {
                return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
            }
            return { key, direction: 'desc' };
        });
    };

    const sortedResults = [...results].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    useEffect(() => {
        localStorage.setItem('optimization_strategy', strategy);
    }, [strategy]);

    useEffect(() => {
        localStorage.setItem('optimization_timeframe', timeframe);
    }, [timeframe]);

    useEffect(() => {
        localStorage.setItem('optimization_results', JSON.stringify(results));
    }, [results]);

    useEffect(() => {
        localStorage.setItem('optimization_ranges', JSON.stringify(ranges));
    }, [ranges]);

    const clearResults = () => {
        setResults([]);
        localStorage.removeItem('optimization_results');
    };

    const [ws, setWs] = useState(null);

    // Self-healing: Validate ranges against strategy
    useEffect(() => {
        const expectedKeys = {
            'SMA Crossover': ['fast_period', 'slow_period'],
            'Mean Reversion': ['bb_period', 'bb_std', 'rsi_period', 'rsi_oversold', 'rsi_overbought'],
            'RSI': ['period', 'oversold', 'overbought'],
            'MACD': ['fast_period', 'slow_period', 'signal_period'],
            'Bollinger Breakout': ['bb_period', 'bb_std', 'volume_factor'],
            'Momentum': ['roc_period', 'rsi_period', 'rsi_min', 'rsi_max'],
            'DCA Dip': ['ema_long', 'ema_short']
        };

        const currentKeys = Object.keys(ranges);
        const expected = expectedKeys[strategy];

        if (!expected) return;

        const hasAllKeys = expected.every(key => currentKeys.includes(key));
        const hasExtraKeys = currentKeys.some(key => !expected.includes(key));

        if (!hasAllKeys || hasExtraKeys) {
            if (presets[strategy] && presets[strategy].length > 0) {
                setRanges(presets[strategy][0].ranges);
            }
        }
    }, [strategy, ranges]);

    // Persistent WebSocket Connection
    useEffect(() => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/optimize`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            // WebSocket connected
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                setIsOptimizing(true);
                setLoading(true);
                setProgress({ current: data.current, total: data.total });
            } else if (data.type === 'complete') {
                // Deduplicate results based on parameters
                const uniqueResults = [];
                const seenParams = new Set();

                for (const result of data.results) {
                    // Create a stable string representation of params for comparison
                    const paramKey = JSON.stringify(Object.keys(result.params).sort().reduce((obj, key) => {
                        obj[key] = result.params[key];
                        return obj;
                    }, {}));

                    if (!seenParams.has(paramKey)) {
                        seenParams.add(paramKey);
                        uniqueResults.push(result);
                    }
                }

                if (ultimateOptimizingRef.current) {
                    // Ultimate Optimization Flow
                    // Add strategy name to results if not present (backend might not send it in params, but it's in the task)
                    // Actually, the result params don't have strategy name. We need to know which strategy produced these.
                    // The current strategy is set in state `strategy`.
                    const strategiesResults = uniqueResults.map(r => ({
                        ...r,
                        strategy: strategy // Use current strategy from state
                    }));

                    setUltimateResults(prev => [...prev, ...strategiesResults]);

                    const nextTask = globalQueueRef.current.shift();
                    if (nextTask) {
                        setStrategy(nextTask.strategy);
                        sendOptimizationRequest(nextTask, event.target);
                    } else {
                        // All done
                        ultimateOptimizingRef.current = false;
                        setIsUltimateOptimizing(false);
                        setLoading(false);
                        setIsOptimizing(false);
                        toast.success("Ultimate Optimization Complete!");
                    }

                } else {
                    // Standard Optimization Flow
                    setResults(uniqueResults);
                    setLoading(false);
                    setIsOptimizing(false);
                    toast.success("Optimization Complete!");
                }
            } else if (data.type === 'error') {
                toast.error('Optimization error: ' + data.error);
                setLoading(false);
                setIsOptimizing(false);
                if (ultimateOptimizingRef.current) {
                    ultimateOptimizingRef.current = false;
                    setIsUltimateOptimizing(false);
                }
            } else if (data.error) {
                toast.error(data.error);
                setLoading(false);
                setIsOptimizing(false);
                if (ultimateOptimizingRef.current) {
                    ultimateOptimizingRef.current = false;
                    setIsUltimateOptimizing(false);
                }
            }
        };

        socket.onclose = () => {
            // WebSocket closed
        };

        setWs(socket);

        return () => {
            socket.close();
        };
    }, []);

    const [nTrials, setNTrials] = useState(50);

    const STRATEGY_PARAM_KEYS = {
        'SMA Crossover': ['fast_period', 'slow_period'],
        'Mean Reversion': ['bb_period', 'bb_std', 'rsi_period', 'rsi_oversold', 'rsi_overbought'],
        'RSI': ['period', 'oversold', 'overbought'],
        'MACD': ['fast_period', 'slow_period', 'signal_period'],
        'Bollinger Breakout': ['bb_period', 'bb_std', 'volume_factor'],
        'Momentum': ['roc_period', 'rsi_period', 'rsi_min', 'rsi_max'],
        'DCA Dip': ['ema_long', 'ema_short']
    };

    const runUltimateOptimization = () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            toast.error("WebSocket not connected. Please refresh the page.");
            return;
        }

        // Check Subscription
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

        setLoading(true);
        setIsOptimizing(true);
        setIsUltimateOptimizing(true);
        ultimateOptimizingRef.current = true;
        setUltimateResults([]); // Clear previous ultimate results only

        // Build Queue
        const queue = [];
        for (const stratName of Object.keys(strategyInfo)) {
            const stratPresets = presets[stratName];
            if (stratPresets && stratPresets.length > 0) {
                // Use last preset (usually widest ranges)
                const preset = stratPresets[stratPresets.length - 1];
                queue.push({
                    strategy: stratName,
                    timeframe: preset.timeframe || '1h',
                    ranges: preset.ranges
                });
            }
        }
        globalQueueRef.current = queue;

        // Start First Task
        const firstTask = globalQueueRef.current.shift();
        if (firstTask) {
            setStrategy(firstTask.strategy);
            sendOptimizationRequest(firstTask, ws);
        }
    };

    const sendOptimizationRequest = (task, socket) => {
        const { strategy, timeframe, ranges } = task;
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

        socket.send(JSON.stringify({
            symbol: 'BTC/USDT',
            timeframe: timeframe,
            days: 3,
            strategy: strategy,
            param_ranges: param_ranges,
            n_trials: nTrials,
            token: localStorage.getItem('token')
        }));
    };

    const runOptimization = () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            toast.error("WebSocket not connected. Please refresh the page.");
            return;
        }
        setLoading(true);
        setIsOptimizing(true);
        setProgress({ current: 0, total: nTrials });
        setResults([]);

        sendOptimizationRequest({
            strategy,
            timeframe,
            ranges
        }, ws);
    };


    const applyToBacktest = (params) => {
        const suggestion = {
            strategy: strategy,
            timeframe: timeframe,
            params: params
        };
        localStorage.setItem('backtest_params_suggestion', JSON.stringify(suggestion));
        window.location.href = '/backtest';
    };




    return (
        <PlanGate feature="Strategy Optimization" explanation="Fine-tune your strategy parameters to maximize profitability using historical data.">
            <div className="max-w-7xl mx-auto space-y-8">
                <style>{`
                /* Hide number input spinners */
                input[type=number]::-webkit-inner-spin-button, 
                input[type=number]::-webkit-outer-spin-button { 
                    -webkit-appearance: none; 
                    margin: 0; 
                }
                input[type=number] {
                    -moz-appearance: textfield;
                }
                /* Dark scrollbar for table */
                ::-webkit-scrollbar {
                    width: 8px;
                    height: 8px;
                }
                ::-webkit-scrollbar-track {
                    background: rgba(0, 0, 0, 0.1); 
                }
                ::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.2); 
                    border-radius: 4px;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.3); 
                }
            `}</style>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Strategy Optimization
                        </h2>
                        <p className="text-muted-foreground mt-1">
                            Fine-tune your trading strategy parameters to maximize profits.
                        </p>
                    </div>
                </div>

                {/* Configuration Panel - Horizontal Layout */}
                <div className="glass p-4 rounded-2xl">
                    <div className="flex justify-between items-center mb-4 border-b border-white/10 pb-3">
                        <h3 className="font-semibold flex items-center gap-2 text-base text-foreground">
                            <Settings size={18} className="text-primary" />
                            Configuration
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-foreground">Timeframe:</label>
                                <div className="relative">
                                    <select
                                        className="bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white"
                                        value={timeframe}
                                        onChange={(e) => setTimeframe(e.target.value)}
                                    >
                                        {TIMEFRAME_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}
                                    </select>
                                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                        <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-foreground">Strategy:</label>
                                <div className="relative">
                                    <select
                                        className="bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white"
                                        value={strategy}
                                        onChange={handleStrategyChange}
                                    >
                                        {strategies.map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Presets */}
                    {presets[strategy] && presets[strategy].length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-6 p-3 bg-white/5 rounded-xl border border-white/10">
                            <span className="text-xs font-bold text-muted-foreground uppercase flex items-center mr-2">
                                <Sliders size={12} className="mr-1" /> Presets:
                            </span>
                            {presets[strategy].map((preset, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => applyPreset(preset)}
                                    className="px-3 py-1 bg-black/20 hover:bg-primary/20 hover:text-primary text-xs font-medium rounded-full border border-white/5 transition-all"
                                >
                                    {preset.name}
                                </button>
                            ))}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {Object.entries(ranges).map(([param, range]) => {
                            const limits = paramLimits[param] || { min: 0, max: 100, step: 1 };
                            return (
                                <div key={param} className="p-3 bg-white/5 rounded-xl border border-white/5">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-xs font-bold text-foreground capitalize">
                                            {formatLabel(param)}
                                        </span>
                                        <Tooltip content={parameterInfo[param]} />
                                    </div>

                                    <SliderInput
                                        label="Start"
                                        value={range.start}
                                        min={limits.min}
                                        max={limits.max}
                                        step={limits.step}
                                        onChange={(val) => handleRangeChange(param, 'start', val)}
                                    />

                                    <SliderInput
                                        label="End"
                                        value={range.end}
                                        min={limits.min}
                                        max={limits.max}
                                        step={limits.step}
                                        onChange={(val) => handleRangeChange(param, 'end', val)}
                                    />

                                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
                                        <label className="text-[10px] text-muted-foreground">Step</label>
                                        <input
                                            type="number"
                                            className="w-12 bg-black/20 border border-white/10 rounded px-1.5 py-0.5 text-[10px] text-right"
                                            value={range.step}
                                            min={limits.step}
                                            step={limits.step}
                                            onChange={(e) => handleRangeChange(param, 'step', e.target.value)}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="mt-6 flex items-center gap-4">
                        <div className="w-48">
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">Trials: {nTrials}</label>
                            <input
                                type="range"
                                min="10"
                                max="200"
                                step="10"
                                value={nTrials}
                                onChange={(e) => setNTrials(Number(e.target.value))}
                                className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary hover:accent-primary/80 transition-all"
                            />
                        </div>
                        <button
                            onClick={runOptimization}
                            disabled={loading}
                            className="flex-1 bg-primary hover:bg-primary/90 text-white py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 disabled:opacity-70 disabled:cursor-not-allowed text-sm"
                        >
                            {loading ? (
                                <span className="animate-pulse flex items-center gap-2">
                                    <Activity className="animate-spin" size={16} /> Optimizing...
                                </span>
                            ) : (
                                <>
                                    <Play size={16} fill="currentColor" /> Run Optimization
                                </>
                            )}
                        </button>
                        {isOptimizing && (
                            <div className="flex-1 flex flex-col gap-1">
                                <div className="flex justify-between text-xs text-muted-foreground">
                                    <span>Progress</span>
                                    <span>{progress.current} / {progress.total}</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-300"
                                        style={{ width: `${(progress.current / Math.max(progress.total, 1)) * 100}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Ultimate Optimization Section */}
                <div className="glass rounded-2xl overflow-hidden flex flex-col border border-purple-500/20 shadow-lg shadow-purple-900/10 mb-8">
                    <div className="p-6 border-b border-white/10 flex justify-between items-center bg-gradient-to-r from-purple-900/20 to-transparent">
                        <div className="flex items-center gap-3">
                            <h3 className="font-semibold flex items-center gap-2 text-lg text-purple-100">
                                <Crown size={20} className="text-purple-400" />
                                Ultimate Optimization Results
                            </h3>
                            {isUltimateOptimizing && (
                                <span className="text-xs text-purple-300 animate-pulse bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                                    Running... {progress.current} / {progress.total}
                                </span>
                            )}
                        </div>

                        <button
                            onClick={runUltimateOptimization}
                            disabled={loading}
                            className={`px-4 py-2 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg text-sm ${subscription?.plan === 'free'
                                ? 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 cursor-pointer'
                                : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/25'
                                }`}
                        >
                            {loading && isUltimateOptimizing ? (
                                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white/20 border-t-white"></span>
                            ) : (
                                subscription?.plan === 'free' ? <Lock size={16} /> : <Play size={16} fill="currentColor" />
                            )}
                            Run Ultimate Optimization
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <div className="max-h-[500px] overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-white/5 text-muted-foreground uppercase text-xs font-medium sticky top-0 backdrop-blur-md z-10">
                                    <tr>
                                        <th className="px-6 py-4">Strategy</th>
                                        <th className="px-6 py-4">Rank</th>
                                        <th className="px-6 py-4">Parameters</th>
                                        <th className="px-6 py-4 text-right">Return</th>
                                        <th className="px-6 py-4 text-right">Win Rate</th>
                                        <th className="px-6 py-4 text-right">Trades</th>
                                        <th className="px-6 py-4 text-center">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {ultimateResults.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="px-6 py-16 text-center text-muted-foreground">
                                                <div className="flex flex-col items-center justify-center gap-2 opacity-50">
                                                    <Crown size={32} />
                                                    <p>Run Ultimate Optimization to compare all strategies</p>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        ultimateResults.sort((a, b) => b.return - a.return).map((res, i) => (
                                            <tr key={i} className="hover:bg-white/5 transition-colors group">
                                                <td className="px-6 py-4 font-medium text-purple-200">
                                                    {res.strategy}
                                                </td>
                                                <td className="px-6 py-4 font-mono text-muted-foreground">
                                                    #{i + 1}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-wrap gap-2">
                                                        {Object.entries(res.params).map(([k, v]) => (
                                                            <span key={k} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-white/10 text-foreground border border-white/5">
                                                                <span className="opacity-70 mr-1">{formatLabel(k)}:</span> <span className="font-bold">{v}</span>
                                                            </span>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td className={`px-6 py-4 text-right font-bold ${res.return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {res.return > 0 ? '+' : ''}{res.return.toFixed(2)}%
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    {res.win_rate.toFixed(1)}%
                                                </td>
                                                <td className="px-6 py-4 text-right text-muted-foreground font-mono">
                                                    {res.trades}
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <div className="flex justify-center gap-2">
                                                        <button
                                                            onClick={() => {
                                                                setStrategy(res.strategy);
                                                                applyToBacktest(res.params);
                                                            }}
                                                            className="text-xs bg-white/10 text-white hover:bg-white/20 px-3 py-1.5 rounded-md font-medium transition-colors border border-white/20"
                                                        >
                                                            Backtest
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Results Panel - Below Configuration */}
                < div className="glass rounded-2xl overflow-hidden flex flex-col" >
                    <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                        <h3 className="font-semibold flex items-center gap-2 text-lg">
                            <TrendingUp size={20} className="text-green-400" />
                            Optimization Results
                        </h3>
                        <div className="flex items-center gap-4">
                            <span className="text-sm text-muted-foreground bg-black/20 px-3 py-1 rounded-full border border-white/5">
                                {results.length} combinations
                            </span>
                            {results.length > 0 && (
                                <button
                                    onClick={clearResults}
                                    className="text-xs text-red-400 hover:text-red-300 font-medium px-3 py-1 hover:bg-red-500/10 rounded transition-colors"
                                >
                                    Clear
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <div className="max-h-[500px] overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-white/5 text-muted-foreground uppercase text-xs font-medium sticky top-0 backdrop-blur-md z-10">
                                    <tr>
                                        <th className="px-6 py-4">Rank</th>
                                        <th className="px-6 py-4">Parameters</th>
                                        <th
                                            className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                            onClick={() => handleSort('return')}
                                        >
                                            <div className="flex items-center justify-end gap-1">
                                                Return
                                                {sortConfig.key === 'return' ? (
                                                    sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                                ) : (
                                                    <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                                )}
                                            </div>
                                        </th>
                                        <th
                                            className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                            onClick={() => handleSort('win_rate')}
                                        >
                                            <div className="flex items-center justify-end gap-1">
                                                Win Rate
                                                {sortConfig.key === 'win_rate' ? (
                                                    sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                                ) : (
                                                    <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                                )}
                                            </div>
                                        </th>
                                        <th
                                            className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                            onClick={() => handleSort('trades')}
                                        >
                                            <div className="flex items-center justify-end gap-1">
                                                Trades
                                                {sortConfig.key === 'trades' ? (
                                                    sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                                ) : (
                                                    <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                                )}
                                            </div>
                                        </th>
                                        <th className="px-6 py-4 text-center">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {sortedResults.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" className="px-6 py-24 text-center">
                                                <div className="flex flex-col items-center justify-center text-muted-foreground">
                                                    <Activity size={48} className="mb-4 opacity-20" />
                                                    <p className="text-lg font-medium">No results yet</p>
                                                    <p className="text-sm opacity-70 max-w-xs mt-2">
                                                        Configure your parameters above and click "Run Optimization" to find the best strategy settings.
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        sortedResults.map((res, i) => (
                                            <tr key={i} className="hover:bg-white/5 transition-colors group">
                                                <td className="px-6 py-4 font-mono text-muted-foreground">
                                                    {i === 0 && sortConfig.key === 'return' && sortConfig.direction === 'desc' ? (
                                                        <span className="flex items-center gap-1 text-yellow-400 font-bold">
                                                            <CheckCircle size={14} /> #1
                                                        </span>
                                                    ) : `#${i + 1}`}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-wrap gap-2">
                                                        {Object.entries(res.params).map(([k, v]) => (
                                                            <span key={k} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-white/10 text-foreground border border-white/5">
                                                                <span className="opacity-70 mr-1">{formatLabel(k)}:</span> <span className="font-bold">{v}</span>
                                                            </span>
                                                        ))}
                                                    </div>

                                                </td>
                                                <td className={`px-6 py-4 text-right font-bold ${res.return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {res.return > 0 ? '+' : ''}{res.return.toFixed(2)}%
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="flex items-center justify-end gap-2">
                                                        <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-primary"
                                                                style={{ width: `${res.win_rate}%` }}
                                                            />
                                                        </div>
                                                        {res.win_rate.toFixed(1)}%
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right text-muted-foreground font-mono">
                                                    {res.trades}
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <div className="flex justify-center gap-2">
                                                        <button
                                                            onClick={() => applyToBacktest(res.params)}
                                                            className="text-xs bg-white/10 text-white hover:bg-white/20 px-3 py-1.5 rounded-md font-medium transition-colors border border-white/20"
                                                        >
                                                            Backtest
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div >
            </div >
        </PlanGate >
    );
}
