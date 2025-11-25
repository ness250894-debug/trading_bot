import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, TrendingUp, Activity, Settings, Info, CheckCircle, AlertCircle, Sliders } from 'lucide-react';

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
    'MACD': "Moving Average Convergence Divergence. A momentum indicator that follows trends. Good for identifying the strength and direction of a trend."
};

const parameterInfo = {
    short_window: "The period for the faster moving average. A smaller number makes it more sensitive to recent price changes.",
    long_window: "The period for the slower moving average. A larger number smooths out noise but reacts slower to trends.",
    bb_length: "The number of periods used for the Bollinger Bands moving average.",
    bb_std: "Standard Deviations for the bands. Higher values make the bands wider, requiring more extreme price moves to trigger signals.",
    rsi_length: "The lookback period for RSI calculation. Standard is 14.",
    rsi_buy: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    rsi_sell: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    period: "The lookback period for the indicator.",
    buy_threshold: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    sell_threshold: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    fast_period: "The short-term EMA period for MACD.",
    slow_period: "The long-term EMA period for MACD.",
    signal_period: "The EMA period for the signal line."
};

const paramLimits = {
    short_window: { min: 2, max: 50, step: 1 },
    long_window: { min: 10, max: 200, step: 5 },
    bb_length: { min: 5, max: 50, step: 1 },
    bb_std: { min: 0.5, max: 4.0, step: 0.1 },
    rsi_length: { min: 2, max: 30, step: 1 },
    rsi_buy: { min: 5, max: 45, step: 1 },
    rsi_sell: { min: 55, max: 95, step: 1 },
    period: { min: 2, max: 50, step: 1 },
    buy_threshold: { min: 5, max: 45, step: 1 },
    sell_threshold: { min: 55, max: 95, step: 1 },
    fast_period: { min: 2, max: 50, step: 1 },
    slow_period: { min: 10, max: 100, step: 1 },
    signal_period: { min: 2, max: 30, step: 1 }
};

const presets = {
    'SMA Crossover': [
        { name: 'Conservative', ranges: { short_window: { start: 10, end: 20, step: 2 }, long_window: { start: 50, end: 100, step: 10 } } },
        { name: 'Aggressive', ranges: { short_window: { start: 3, end: 10, step: 1 }, long_window: { start: 15, end: 40, step: 5 } } },
        { name: 'Wide Search', ranges: { short_window: { start: 2, end: 30, step: 2 }, long_window: { start: 20, end: 150, step: 10 } } }
    ],
    'Mean Reversion': [
        { name: 'Standard', ranges: { bb_length: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, rsi_length: { start: 14, end: 14, step: 1 }, rsi_buy: { start: 30, end: 30, step: 1 }, rsi_sell: { start: 70, end: 70, step: 1 } } },
        { name: 'Volatile Market', ranges: { bb_length: { start: 10, end: 30, step: 5 }, bb_std: { start: 2.0, end: 3.0, step: 0.2 }, rsi_length: { start: 10, end: 20, step: 2 }, rsi_buy: { start: 20, end: 40, step: 5 }, rsi_sell: { start: 60, end: 80, step: 5 } } }
    ],
    'RSI': [
        { name: 'Scalping', ranges: { period: { start: 5, end: 10, step: 1 }, buy_threshold: { start: 20, end: 30, step: 2 }, sell_threshold: { start: 70, end: 80, step: 2 } } },
        { name: 'Swing', ranges: { period: { start: 14, end: 28, step: 2 }, buy_threshold: { start: 30, end: 40, step: 2 }, sell_threshold: { start: 60, end: 70, step: 2 } } }
    ],
    'MACD': [
        { name: 'Standard', ranges: { fast_period: { start: 12, end: 12, step: 1 }, slow_period: { start: 26, end: 26, step: 1 }, signal_period: { start: 9, end: 9, step: 1 } } },
        { name: 'Fast', ranges: { fast_period: { start: 5, end: 15, step: 1 }, slow_period: { start: 15, end: 30, step: 2 }, signal_period: { start: 5, end: 10, step: 1 } } }
    ]
};

export default function Optimization() {
    const [strategy, setStrategy] = useState(() => localStorage.getItem('optimization_strategy') || 'SMA Crossover');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(() => {
        const saved = localStorage.getItem('optimization_results');
        return saved ? JSON.parse(saved) : [];
    });

    const [ranges, setRanges] = useState(() => {
        const saved = localStorage.getItem('optimization_ranges');
        return saved ? JSON.parse(saved) : {
            short_window: { start: 5, end: 20, step: 5 },
            long_window: { start: 30, end: 60, step: 10 }
        };
    });

    const [progress, setProgress] = useState({ current: 0, total: 0 });
    const [isOptimizing, setIsOptimizing] = useState(false);

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

    useEffect(() => {
        localStorage.setItem('optimization_strategy', strategy);
    }, [strategy]);

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

    const runOptimization = async () => {
        setLoading(true);
        setIsOptimizing(true);
        setProgress({ current: 0, total: 0 });
        setResults([]);

        const param_ranges = {};
        for (const [key, range] of Object.entries(ranges)) {
            const values = [];
            let current = range.start;
            const step = Math.max(range.step, 0.1);
            while (current <= range.end) {
                values.push(Number(current.toFixed(2)));
                current += step;
            }
            param_ranges[key] = values;
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/api/ws/optimize`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            ws.send(JSON.stringify({
                symbol: 'BTC/USDT',
                timeframe: '1m',
                days: 3,
                strategy: strategy,
                param_ranges: param_ranges
            }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                setProgress({ current: data.current, total: data.total });
            } else if (data.type === 'complete') {
                setResults(data.results);
                setLoading(false);
                setIsOptimizing(false);
                ws.close();
            } else if (data.error) {
                console.error(data.error);
                alert('Optimization failed: ' + data.error);
                setLoading(false);
                setIsOptimizing(false);
                ws.close();
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            alert('WebSocket connection failed.');
            setLoading(false);
            setIsOptimizing(false);
        };
    };

    const applyToStrategy = (params) => {
        const suggestion = {
            strategy: strategy,
            params: params
        };
        localStorage.setItem('suggested_strategy_params', JSON.stringify(suggestion));
        window.location.href = '/strategies';
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8">
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
                            <label className="text-sm font-medium text-foreground">Strategy:</label>
                            <select
                                className="bg-black/20 border border-white/10 rounded-lg p-2 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm"
                                value={strategy}
                                onChange={handleStrategyChange}
                            >
                                {strategies.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        {presets[strategy] && (
                            <div className="flex gap-2">
                                {presets[strategy].map((preset, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => applyPreset(preset)}
                                        className="px-3 py-1.5 text-xs font-medium bg-white/5 hover:bg-white/10 text-foreground rounded-lg transition-colors border border-white/5"
                                    >
                                        {preset.name}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(ranges).map(([param, range]) => {
                        const limits = paramLimits[param] || { min: 0, max: 100, step: 1 };
                        return (
                            <div key={param} className="p-3 bg-white/5 rounded-xl border border-white/5">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-bold text-foreground capitalize">
                                        {param.replace(/_/g, ' ')}
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

            {/* Results Panel - Below Configuration */}
            <div className="glass rounded-2xl overflow-hidden flex flex-col">
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
                                    <th className="px-6 py-4 text-right">Return</th>
                                    <th className="px-6 py-4 text-right">Win Rate</th>
                                    <th className="px-6 py-4 text-right">Trades</th>
                                    <th className="px-6 py-4 text-center">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {results.length === 0 ? (
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
                                    results.map((res, i) => (
                                        <tr key={i} className="hover:bg-white/5 transition-colors group">
                                            <td className="px-6 py-4 font-mono text-muted-foreground">
                                                {i === 0 ? (
                                                    <span className="flex items-center gap-1 text-yellow-400 font-bold">
                                                        <CheckCircle size={14} /> #1
                                                    </span>
                                                ) : `#${i + 1}`}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-wrap gap-2">
                                                    {Object.entries(res.params).map(([k, v]) => (
                                                        <span key={k} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-white/10 text-foreground border border-white/5">
                                                            {k}: {v}
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
                                                <button
                                                    onClick={() => applyToStrategy(res.params)}
                                                    className="text-xs bg-primary/10 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-md font-medium transition-colors border border-primary/20"
                                                >
                                                    Apply
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
