import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, TrendingUp, Activity, Settings, Info, CheckCircle, AlertCircle } from 'lucide-react';

// --- Helper Components ---

const Tooltip = ({ content }) => (
    <div className="group relative inline-block ml-2">
        <Info size={14} className="text-muted-foreground hover:text-primary cursor-help" />
        <div className="invisible group-hover:visible absolute z-10 w-64 p-2 mt-2 text-xs text-popover-foreground bg-popover rounded-md shadow-lg -left-28 border border-border">
            {content}
        </div>
    </div>
);

const SliderInput = ({ label, value, min, max, step, onChange, description }) => {
    return (
        <div className="mb-4">
            <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-medium text-foreground flex items-center">
                    {label}
                    {description && <Tooltip content={description} />}
                </label>
                <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                    {value}
                </span>
            </div>
            <div className="flex items-center gap-3">
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <input
                    type="number"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-16 bg-background border border-input rounded px-2 py-1 text-sm text-right focus:ring-1 focus:ring-primary outline-none"
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
        { name: 'Standard', ranges: { bb_length: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, rsi_length: { start: 14, end: 14, step: 1 } } },
        { name: 'Volatile Market', ranges: { bb_length: { start: 10, end: 30, step: 5 }, bb_std: { start: 2.0, end: 3.0, step: 0.2 }, rsi_length: { start: 10, end: 20, step: 2 } } }
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

    // Ranges state now holds { start, end, step }
    const [ranges, setRanges] = useState(() => {
        const saved = localStorage.getItem('optimization_ranges');
        return saved ? JSON.parse(saved) : {
            short_window: { start: 5, end: 20, step: 5 },
            long_window: { start: 30, end: 60, step: 10 }
        };
    });

    const strategies = Object.keys(strategyInfo);

    const handleStrategyChange = (e) => {
        const newStrategy = e.target.value;
        setStrategy(newStrategy);
        setResults([]);

        // Reset ranges based on strategy with sensible defaults
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

            // Clamp values to prevent start > end
            if (field === 'start') {
                if (newValue > currentRange.end) {
                    // If start is dragged past end, push end or clamp start?
                    // User requested "not moving other slider", so we clamp start to end.
                    newValue = Math.min(newValue, currentRange.end);
                    newRange.start = newValue;
                }
            } else if (field === 'end') {
                if (newValue < currentRange.start) {
                    // If end is dragged below start, clamp end to start.
                    newValue = Math.max(newValue, currentRange.start);
                    newRange.end = newValue;
                }
            }

            return {
                ...prev,
                [param]: newRange
            };
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
        try {
            // Convert ranges to lists
            const param_ranges = {};
            for (const [key, range] of Object.entries(ranges)) {
                const values = [];
                let current = range.start;
                // Safety check to prevent infinite loops if step is 0 or negative
                const step = Math.max(range.step, 0.1);

                while (current <= range.end) {
                    values.push(Number(current.toFixed(2)));
                    current += step;
                }
                param_ranges[key] = values;
            }

            const response = await axios.post('/api/optimize', {
                symbol: 'BTC/USDT',
                timeframe: '1m',
                days: 3,
                strategy: strategy,
                param_ranges: param_ranges
            });

            setResults(response.data.results);
        } catch (err) {
            console.error(err);
            alert('Optimization failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h2 className="text-3xl font-bold flex items-center gap-3 text-foreground">
                        <Activity className="text-primary" />
                        Strategy Optimization
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        Fine-tune your trading strategy parameters to maximize profits.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Configuration Panel */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-card p-6 rounded-xl border border-border shadow-sm">
                        <h3 className="font-semibold mb-6 flex items-center gap-2 text-lg">
                            <Settings size={20} className="text-primary" />
                            Configuration
                        </h3>

                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium mb-2 text-foreground">
                                    Select Strategy
                                    <Tooltip content={strategyInfo[strategy]} />
                                </label>
                                <select
                                    className="w-full bg-background border border-input rounded-lg p-2.5 text-foreground focus:ring-2 focus:ring-primary outline-none transition-all"
                                    value={strategy}
                                    onChange={handleStrategyChange}
                                >
                                    {strategies.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                                    {strategyInfo[strategy]}
                                </p>
                            </div>

                            {/* Presets */}
                            {presets[strategy] && (
                                <div>
                                    <label className="block text-xs font-medium mb-2 text-muted-foreground uppercase tracking-wider">
                                        Quick Presets
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {presets[strategy].map((preset, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => applyPreset(preset)}
                                                className="px-3 py-1.5 text-xs font-medium bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-md transition-colors border border-border/50"
                                            >
                                                {preset.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="border-t border-border pt-6">
                                <h4 className="text-sm font-semibold mb-4 text-primary uppercase tracking-wider">Parameter Ranges</h4>
                                {Object.entries(ranges).map(([param, range]) => {
                                    const limits = paramLimits[param] || { min: 0, max: 100, step: 1 };
                                    return (
                                        <div key={param} className="mb-6 p-4 bg-muted/30 rounded-lg border border-border/50">
                                            <div className="flex items-center gap-2 mb-3">
                                                <span className="text-sm font-bold text-foreground capitalize">
                                                    {param.replace(/_/g, ' ')}
                                                </span>
                                                <Tooltip content={parameterInfo[param]} />
                                            </div>

                                            <SliderInput
                                                label="Start Value"
                                                value={range.start}
                                                min={limits.min}
                                                max={limits.max}
                                                step={limits.step}
                                                onChange={(val) => handleRangeChange(param, 'start', val)}
                                            />

                                            <SliderInput
                                                label="End Value"
                                                value={range.end}
                                                min={limits.min} // Fixed min to prevent jumping
                                                max={limits.max}
                                                step={limits.step}
                                                onChange={(val) => handleRangeChange(param, 'end', val)}
                                            />

                                            <div className="flex justify-between items-center mt-2 pt-2 border-t border-border/50">
                                                <label className="text-xs text-muted-foreground">Step Size</label>
                                                <input
                                                    type="number"
                                                    className="w-16 bg-background border border-input rounded px-2 py-1 text-xs text-right"
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

                            <button
                                onClick={runOptimization}
                                disabled={loading}
                                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <span className="animate-pulse flex items-center gap-2">
                                        <Activity className="animate-spin" size={18} /> Optimizing...
                                    </span>
                                ) : (
                                    <>
                                        <Play size={18} fill="currentColor" /> Run Optimization
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Results Panel */}
                <div className="lg:col-span-8">
                    <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden h-full flex flex-col">
                        <div className="p-6 border-b border-border flex justify-between items-center bg-muted/10">
                            <h3 className="font-semibold flex items-center gap-2 text-lg">
                                <TrendingUp size={20} className="text-green-500" />
                                Optimization Results
                            </h3>
                            <div className="flex items-center gap-4">
                                <span className="text-sm text-muted-foreground bg-background px-3 py-1 rounded-full border border-border">
                                    {results.length} combinations
                                </span>
                                {results.length > 0 && (
                                    <button
                                        onClick={clearResults}
                                        className="text-xs text-destructive hover:text-destructive/80 font-medium px-3 py-1 hover:bg-destructive/10 rounded transition-colors"
                                    >
                                        Clear
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="overflow-x-auto flex-1">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-muted/50 text-muted-foreground uppercase text-xs font-medium">
                                    <tr>
                                        <th className="px-6 py-4">Rank</th>
                                        <th className="px-6 py-4">Parameters</th>
                                        <th className="px-6 py-4 text-right">Return</th>
                                        <th className="px-6 py-4 text-right">Win Rate</th>
                                        <th className="px-6 py-4 text-right">Trades</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {results.length === 0 ? (
                                        <tr>
                                            <td colSpan="5" className="px-6 py-24 text-center">
                                                <div className="flex flex-col items-center justify-center text-muted-foreground">
                                                    <Activity size={48} className="mb-4 opacity-20" />
                                                    <p className="text-lg font-medium">No results yet</p>
                                                    <p className="text-sm opacity-70 max-w-xs mt-2">
                                                        Configure your parameters on the left and click "Run Optimization" to find the best strategy settings.
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        results.map((res, i) => (
                                            <tr key={i} className="hover:bg-muted/30 transition-colors group">
                                                <td className="px-6 py-4 font-mono text-muted-foreground">
                                                    {i === 0 ? (
                                                        <span className="flex items-center gap-1 text-yellow-500 font-bold">
                                                            <CheckCircle size={14} /> #1
                                                        </span>
                                                    ) : `#${i + 1}`}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-wrap gap-2">
                                                        {Object.entries(res.params).map(([k, v]) => (
                                                            <span key={k} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-secondary text-secondary-foreground border border-border/50">
                                                                {k}: {v}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td className={`px-6 py-4 text-right font-bold ${res.return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                    {res.return > 0 ? '+' : ''}{res.return.toFixed(2)}%
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="flex items-center justify-end gap-2">
                                                        <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
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
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
