import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { DEFAULT_EXCHANGES } from '../constants/exchanges';
import { Save, RefreshCw, AlertTriangle, CheckCircle, TrendingUp, Zap, BarChart2, Activity, Globe, Plus } from 'lucide-react';
import { useModal } from '../components/Modal';

import { useToast } from '../components/ToastContext';


const STRATEGY_OPTIONS = [
    { value: 'mean_reversion', label: 'Mean Reversion', desc: 'Buy low, sell high using Bollinger Bands & RSI.', icon: Activity },
    { value: 'sma_crossover', label: 'SMA Crossover', desc: 'Trend following with moving average crosses.', icon: TrendingUp },
    { value: 'macd', label: 'MACD', desc: 'Momentum strategy using MACD histogram.', icon: BarChart2 },
    { value: 'rsi', label: 'RSI', desc: 'Simple overbought/oversold oscillator.', icon: Zap },
    { value: 'bollinger_breakout', label: 'Bollinger Breakout', desc: 'Buy on upper band breakout with volume.', icon: TrendingUp },
    { value: 'momentum', label: 'Momentum', desc: 'Trade based on Rate of Change and RSI.', icon: Zap },
    { value: 'dca_dip', label: 'DCA Dip', desc: 'Accumulate on dips during uptrends.', icon: BarChart2 },
    { value: 'combined', label: 'Combined Strategy', desc: 'Multi-indicator confirmation setup.', icon: Activity }
];

const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];

const STRATEGY_PARAMS = {
    mean_reversion: {
        rsi_period: { label: 'RSI Period', type: 'number', min: 2, max: 50, default: 14 },
        rsi_overbought: { label: 'RSI Overbought', type: 'number', min: 50, max: 100, default: 70 },
        rsi_oversold: { label: 'RSI Oversold', type: 'number', min: 0, max: 50, default: 30 },
        bb_period: { label: 'Bollinger Period', type: 'number', min: 5, max: 50, default: 20 },
        bb_std: { label: 'Bollinger Std Dev', type: 'number', min: 1, max: 5, step: 0.1, default: 2.0 }
    },
    sma_crossover: {
        fast_period: { label: 'Fast SMA', type: 'number', min: 2, max: 100, default: 10 },
        slow_period: { label: 'Slow SMA', type: 'number', min: 5, max: 200, default: 50 }
    },
    macd: {
        fast_period: { label: 'Fast Period', type: 'number', min: 2, max: 50, default: 12 },
        slow_period: { label: 'Slow Period', type: 'number', min: 10, max: 100, default: 26 },
        signal_period: { label: 'Signal Period', type: 'number', min: 2, max: 50, default: 9 }
    },
    rsi: {
        period: { label: 'RSI Period', type: 'number', min: 2, max: 50, default: 14 },
        overbought: { label: 'Overbought', type: 'number', min: 50, max: 100, default: 70 },
        oversold: { label: 'Oversold', type: 'number', min: 0, max: 50, default: 30 }
    },
    bollinger_breakout: {
        bb_period: { label: 'Bollinger Period', type: 'number', min: 5, max: 50, default: 20 },
        bb_std: { label: 'Bollinger Std Dev', type: 'number', min: 1, max: 5, step: 0.1, default: 2.0 },
        volume_factor: { label: 'Volume Factor', type: 'number', min: 1, max: 5, step: 0.1, default: 1.5 }
    },
    momentum: {
        roc_period: { label: 'ROC Period', type: 'number', min: 2, max: 50, default: 10 },
        rsi_period: { label: 'RSI Period', type: 'number', min: 2, max: 50, default: 14 },
        rsi_min: { label: 'RSI Min', type: 'number', min: 0, max: 50, default: 50 },
        rsi_max: { label: 'RSI Max', type: 'number', min: 50, max: 100, default: 70 }
    },
    dca_dip: {
        ema_long: { label: 'Long EMA', type: 'number', min: 50, max: 300, default: 200 },
        ema_short: { label: 'Short EMA', type: 'number', min: 5, max: 50, default: 20 }
    },
    combined: {
        rsi_period: { label: 'RSI Period', type: 'number', min: 2, max: 50, default: 14 },
        fast_sma: { label: 'Fast SMA', type: 'number', min: 2, max: 100, default: 10 },
        slow_sma: { label: 'Slow SMA', type: 'number', min: 5, max: 200, default: 50 }
    }
};

// Map display names to internal values (for suggestions from Backtest/Optimization)
const STRATEGY_NAME_TO_VALUE = {
    'Mean Reversion': 'mean_reversion',
    'SMA Crossover': 'sma_crossover',
    'MACD': 'macd',
    'RSI': 'rsi',
    'Bollinger Breakout': 'bollinger_breakout',
    'Momentum': 'momentum',
    'DCA Dip': 'dca_dip',
    'Combined Strategy': 'combined',
    // Also support already-converted values
    'mean_reversion': 'mean_reversion',
    'sma_crossover': 'sma_crossover',
    'macd': 'macd',
    'rsi': 'rsi',
    'bollinger_breakout': 'bollinger_breakout',
    'momentum': 'momentum',
    'dca_dip': 'dca_dip',
    'combined': 'combined'
};

export default function Strategies() {
    const navigate = useNavigate();
    const toast = useToast();
    const modal = useModal();

    // Initialize new strategy with global practice mode preference
    // Default to 'true' if not set, or preserve 'false' if explicitly set
    const savedPracticeMode = localStorage.getItem('globalPracticeMode');
    const isPracticeMode = savedPracticeMode === null ? true : savedPracticeMode === 'true';

    const initialConfig = {
        name: 'New Strategy',
        symbol: 'BTC/USDT',
        timeframe: '1h',
        strategy: 'macd',
        parameters: { ...Object.fromEntries(Object.entries(STRATEGY_PARAMS.macd).map(([k, v]) => [k, v.default])) },
        amount_usdt: 100,
        take_profit_pct: 0.04,
        stop_loss_pct: 0.02,
        leverage: 10,
        dry_run: isPracticeMode // Use the global setting here!
    };

    const [config, setConfig] = useState(initialConfig);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [suggestion, setSuggestion] = useState(null);
    const [exchanges, setExchanges] = useState([]);
    const [exchangesLoading, setExchangesLoading] = useState(true);
    const [customSymbol, setCustomSymbol] = useState(false);
    const [subscription, setSubscription] = useState(null);

    // New state for dynamic data
    const [strategyPresets, setStrategyPresets] = useState({});
    const [riskPresets, setRiskPresets] = useState([]);
    const [popularSymbols, setPopularSymbols] = useState([]);


    const fetchData = async () => {
        setLoading(true);
        setExchangesLoading(true);
        try {
            const [subRes, exchangesRes, strategiesRes, risksRes, symbolsRes] = await Promise.all([
                api.get('/billing/status'),
                api.get('/exchanges'),
                api.get('/strategy-presets'),
                api.get('/risk-presets'),
                api.get('/popular-symbols')
            ]);

            // Process Subscription
            setSubscription(subRes.data);
            setMessage(null);

            // Re-apply free plan limit to config if necessary, though global mode should handle first init
            if (subRes.data?.plan === 'free') {
                // Force true for free plan if not already
                setConfig(prev => ({ ...prev, dry_run: true }));
            }

            const savedSuggestion = localStorage.getItem('suggested_strategy_params');
            if (savedSuggestion) {
                setSuggestion(JSON.parse(savedSuggestion));
            }

            // Process Exchanges
            setExchanges(exchangesRes.data.exchanges || []);

            // Process Strategy Presets
            const presetsByStrategy = {};
            if (strategiesRes.data.presets) {
                strategiesRes.data.presets.forEach(p => {
                    if (!presetsByStrategy[p.strategy_type]) {
                        presetsByStrategy[p.strategy_type] = [];
                    }
                    presetsByStrategy[p.strategy_type].push({
                        name: p.preset_name,
                        params: p.parameters,
                        desc: p.description
                    });
                });
            }
            setStrategyPresets(presetsByStrategy);

            // Process Risk Presets
            setRiskPresets(risksRes.data.presets || []);

            // Process Symbols
            const symbols = (symbolsRes.data.symbols || []).map(s => s.symbol);
            setPopularSymbols([...symbols, 'CUSTOM']);

        } catch (err) {
            console.error("Error fetching data:", err);
            setMessage({ type: 'error', text: 'Failed to load configuration.' });
            // Fallback for exchanges if API fails
            setExchanges([DEFAULT_EXCHANGES[0]]);
        } finally {
            setLoading(false);
            setExchangesLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Listen for storage events in case practice mode changes in another tab? 
        // Not strictly required but good practice. For now just init logic is fine.
    }, []);

    const handleChange = (key, value) => {
        setConfig(prev => {
            const newConfig = { ...prev, [key]: value };

            // If strategy changes, reset parameters to defaults for the new strategy
            if (key === 'strategy') {
                const defaultParams = {};
                const strategyParams = STRATEGY_PARAMS[value] || {};
                Object.entries(strategyParams).forEach(([pKey, pDef]) => {
                    defaultParams[pKey] = pDef.default;
                });
                newConfig.parameters = defaultParams;
            }

            return newConfig;
        });
    };

    const handleParamChange = (param, value) => {
        setConfig(prev => ({
            ...prev,
            parameters: {
                ...prev.parameters,
                [param]: value
            }
        }));
    };

    const applyPreset = (presetParams) => {
        setConfig(prev => ({
            ...prev,
            parameters: { ...presetParams }
        }));
    };

    const applyRiskPreset = (preset) => {
        setConfig(prev => ({
            ...prev,
            take_profit_pct: preset.take_profit_pct,
            stop_loss_pct: preset.stop_loss_pct
        }));
    };

    const applySuggestion = () => {
        if (!suggestion || !config) return;

        const params = { ...suggestion.params };
        let newTimeframe = config.timeframe;
        let newSymbol = config.symbol;

        // Extract timeframe if present in params
        if (params.timeframe) {
            newTimeframe = params.timeframe;
            delete params.timeframe;
        }

        // Extract symbol from top-level suggestion
        if (suggestion.symbol) {
            newSymbol = suggestion.symbol;
        }

        // Convert strategy name to internal value (e.g., "Mean Reversion" -> "mean_reversion")
        const strategyValue = STRATEGY_NAME_TO_VALUE[suggestion.strategy] || suggestion.strategy;

        // Get valid parameter keys for this strategy and filter params
        const validParamKeys = Object.keys(STRATEGY_PARAMS[strategyValue] || {});
        const filteredParams = {};
        validParamKeys.forEach(key => {
            if (params[key] !== undefined) {
                filteredParams[key] = params[key];
            }
        });

        setConfig(prev => ({
            ...prev,
            strategy: strategyValue,
            symbol: newSymbol,
            timeframe: newTimeframe,
            parameters: filteredParams
        }));

        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
        setMessage({ type: 'success', text: 'Applied suggested parameters, symbol, and timeframe! Click Add Bot to save.' });
    };

    const dismissSuggestion = () => {
        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
    };

    const handleAddBot = async () => {
        setSaving(true);
        setMessage(null);
        try {
            // 1. Prepare config for backend (only fields expected by ConfigUpdate model)
            const configForBackend = {
                symbol: config.symbol,
                timeframe: config.timeframe,
                amount_usdt: config.amount_usdt,
                strategy: config.strategy,
                dry_run: config.dry_run,
                take_profit_pct: config.take_profit_pct,
                stop_loss_pct: config.stop_loss_pct,
                leverage: config.leverage,
                parameters: config.parameters || {}
            };

            // Save to API
            await api.post('/bot-configs', configForBackend);

            toast.success('Bot configuration added successfully');

            // Redirect to Main page
            navigate('/main');
        } catch (err) {
            // API returns: {error: {code: 403, message: "..."}}
            const errorData = err.response?.data;
            const errorMsg = errorData?.error?.message || errorData?.detail || 'Failed to add bot configuration.';
            const statusCode = err.response?.status;

            // Show upgrade modal for plan limits (403 errors with free plan)
            if (statusCode === 403) {
                modal.show({
                    title: '🚀 Upgrade Your Plan',
                    content: (
                        <div className="space-y-4">
                            <p className="text-muted-foreground">
                                Your free plan is limited to <span className="text-foreground font-semibold">1 bot</span>.
                            </p>
                            <p className="text-muted-foreground">
                                Upgrade to unlock:
                            </p>
                            <ul className="space-y-2 text-sm">
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                    <span className="text-foreground">Multiple trading bots</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                    <span className="text-foreground">All trading strategies</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                    <span className="text-foreground">Real money trading</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                    <span className="text-foreground">Priority support</span>
                                </li>
                            </ul>
                            <button
                                onClick={() => {
                                    modal.hide();
                                    navigate('/pricing');
                                }}
                                className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-xl font-semibold transition-all shadow-lg shadow-purple-500/25"
                            >
                                View Upgrade Options
                            </button>
                        </div>
                    )
                });
            } else {
                setMessage({ type: 'error', text: errorMsg });
            }
            setSaving(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!config) return null;

    const currentParams = STRATEGY_PARAMS[config.strategy] || {};
    const currentPresets = strategyPresets[config.strategy] || [];

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Bot Management
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        Configure your bot's trading logic and risk parameters.
                    </p>
                </div>
                <button
                    onClick={fetchData}
                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-foreground transition-all"
                    title="Refresh Config"
                >
                    <RefreshCw size={20} />
                </button>
            </div>

            {suggestion && (
                <div className="glass p-6 rounded-xl border-l-4 border-l-blue-500 animate-in slide-in-from-top-4 duration-500">
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-blue-500/20 rounded-full text-blue-400">
                                <TrendingUp size={24} />
                            </div>
                            <div>
                                <h4 className="font-bold text-blue-400">Optimization Result Found</h4>
                                <p className="text-sm text-muted-foreground">
                                    Ready to apply optimized configuration
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3 w-full md:w-auto">
                            <button onClick={dismissSuggestion} className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">Dismiss</button>
                            <button onClick={applySuggestion} className="flex-1 md:flex-none px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all shadow-lg shadow-blue-500/20">Apply</button>
                        </div>
                    </div>
                    {/* Show suggestion details */}
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="bg-white/5 rounded-lg p-3">
                            <span className="text-muted-foreground text-xs uppercase tracking-wider">Strategy</span>
                            <p className="font-medium text-foreground mt-1">{suggestion.strategy}</p>
                        </div>
                        {suggestion.symbol && (
                            <div className="bg-white/5 rounded-lg p-3">
                                <span className="text-muted-foreground text-xs uppercase tracking-wider">Symbol</span>
                                <p className="font-medium text-foreground mt-1 font-mono">{suggestion.symbol}</p>
                            </div>
                        )}
                        {suggestion.params?.timeframe && (
                            <div className="bg-white/5 rounded-lg p-3">
                                <span className="text-muted-foreground text-xs uppercase tracking-wider">Timeframe</span>
                                <p className="font-medium text-foreground mt-1 font-mono">{suggestion.params.timeframe}</p>
                            </div>
                        )}
                        <div className="bg-white/5 rounded-lg p-3">
                            <span className="text-muted-foreground text-xs uppercase tracking-wider">Parameters</span>
                            <p className="font-medium text-foreground mt-1">{Object.keys(suggestion.params || {}).filter(k => k !== 'timeframe').length} customized</p>
                        </div>
                    </div>
                </div>
            )}

            {message && (
                <div className={`p-4 rounded-xl flex items-center gap-3 border ${message.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                    {message.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                    {message.text}
                </div>
            )}

            <div className="glass rounded-2xl overflow-hidden">
                <div className="p-4 md:p-8 border-b border-white/5">
                    <h3 className="font-semibold text-lg text-foreground">Global Configuration</h3>
                    <p className="text-sm text-muted-foreground mt-1">These settings apply to the live trading bot.</p>
                </div>

                <div className="p-4 md:p-8 space-y-8">
                    {/* Exchange Selection */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Globe size={18} className="text-primary" />
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Trading Exchange</label>
                        </div>
                        {exchangesLoading ? (
                            <div className="text-center text-muted-foreground py-4">
                                Loading exchanges...
                            </div>
                        ) : (
                            <div className="relative">
                                <select
                                    value={config.exchange || 'bybit'}
                                    onChange={(e) => handleChange('exchange', e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pr-10 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                >
                                    {exchanges.map((exchange) => (
                                        <option key={exchange.name} value={exchange.name}>
                                            {exchange.display_name}
                                            {exchange.supports_futures && exchange.supports_spot ? ' (Futures & Spot)' :
                                                exchange.supports_futures ? ' (Futures)' : ' (Spot)'}
                                        </option>
                                    ))}
                                </select>
                                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Strategy Selection */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Active Strategy</label>
                        <div className="relative">
                            <select
                                value={config.strategy}
                                onChange={(e) => handleChange('strategy', e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pr-10 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                            >
                                {STRATEGY_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {opt.label} - {opt.desc}
                                    </option>
                                ))}
                            </select>
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                                <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Risk Management Section */}
                    <div className="space-y-4 p-6 bg-white/5 rounded-xl border border-white/5">
                        <div className="flex justify-between items-center mb-4">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Risk Management</label>
                            <div className="flex flex-wrap gap-2">
                                {riskPresets.map(preset => (
                                    <button
                                        key={preset.name}
                                        onClick={() => applyRiskPreset(preset)}
                                        className="px-3 py-1 text-xs rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                                        title={preset.description}
                                    >
                                        {preset.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-xs text-muted-foreground">Take Profit (%)</label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="0.1"
                                        max="100"
                                        step="0.1"
                                        value={config.take_profit_pct ? (config.take_profit_pct * 100).toFixed(2) : ''}
                                        onChange={(e) => handleChange('take_profit_pct', parseFloat(e.target.value) / 100)}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm font-mono focus:border-primary/50 outline-none transition-all"
                                    />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">%</span>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs text-muted-foreground">Stop Loss (%)</label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="0.1"
                                        max="50"
                                        step="0.1"
                                        value={config.stop_loss_pct ? (config.stop_loss_pct * 100).toFixed(2) : ''}
                                        onChange={(e) => handleChange('stop_loss_pct', parseFloat(e.target.value) / 100)}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm font-mono focus:border-primary/50 outline-none transition-all"
                                    />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Strategy Parameters Section */}
                    {Object.keys(currentParams).length > 0 && (
                        <div className="space-y-4 p-6 bg-white/5 rounded-xl border border-white/5">
                            <div className="flex justify-between items-center mb-4">
                                <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Strategy Parameters</label>
                                {currentPresets.length > 0 && (
                                    <div className="flex flex-wrap gap-2">
                                        {currentPresets.map(preset => (
                                            <button
                                                key={preset.name}
                                                onClick={() => applyPreset(preset.params)}
                                                className="px-3 py-1 text-xs rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                                            >
                                                {preset.name}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {Object.entries(currentParams).map(([key, def]) => (
                                    <div key={key} className="space-y-2">
                                        <label className="text-xs text-muted-foreground">{def.label}</label>
                                        <input
                                            type={def.type}
                                            min={def.min}
                                            max={def.max}
                                            step={def.step}
                                            value={config.parameters?.[key] ?? def.default}
                                            onChange={(e) => handleParamChange(key, parseFloat(e.target.value))}
                                            className="w-full bg-black/20 border border-white/10 rounded-lg p-2 text-sm font-mono focus:border-primary/50 outline-none transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Trading Symbol</label>
                            {customSymbol ? (
                                <div className="space-y-2">
                                    <div className="relative">
                                        <input
                                            type="text"
                                            placeholder="Enter symbol (e.g., BTC/USDT)"
                                            className="w-full bg-black/20 border border-white/10 rounded-xl p-4 text-sm font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all uppercase"
                                            value={config.symbol}
                                            onChange={(e) => handleChange('symbol', e.target.value.toUpperCase())}
                                        />
                                    </div>
                                    <button
                                        onClick={() => setCustomSymbol(false)}
                                        className="text-xs text-primary hover:text-primary/80 transition-colors"
                                    >
                                        ← Back to popular symbols
                                    </button>
                                </div>
                            ) : (
                                <div className="relative">
                                    <select
                                        value={popularSymbols.includes(config.symbol) ? config.symbol : 'CUSTOM'}
                                        onChange={(e) => {
                                            if (e.target.value === 'CUSTOM') {
                                                setCustomSymbol(true);
                                            } else {
                                                handleChange('symbol', e.target.value);
                                            }
                                        }}
                                        className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pr-10 text-sm font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                    >
                                        {popularSymbols.map((symbol) => (
                                            <option key={symbol} value={symbol}>
                                                {symbol === 'CUSTOM' ? '+ Custom Symbol' : symbol}
                                            </option>
                                        ))}
                                    </select>
                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                                        <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="space-y-3">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Timeframe</label>
                            <div className="relative">
                                <select
                                    value={config.timeframe}
                                    onChange={(e) => handleChange('timeframe', e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pr-10 text-sm font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                >
                                    {TIMEFRAME_OPTIONS.map(opt => (
                                        <option key={opt} value={opt}>{opt}</option>
                                    ))}
                                </select>
                                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Trade Amount (USDT)</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pl-12 text-sm font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                    value={config.amount_usdt}
                                    onChange={(e) => handleChange('amount_usdt', parseFloat(e.target.value))}
                                />
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                            </div>
                        </div>
                    </div>

                    <div className="pt-8 border-t border-white/5 flex items-center justify-end">
                        <button
                            onClick={handleAddBot}
                            disabled={saving}
                            className="bg-primary hover:bg-primary/90 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {saving ? <RefreshCw className="animate-spin" size={20} /> : <Plus size={20} />}
                            Add Bot
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

