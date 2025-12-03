import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { DEFAULT_EXCHANGES } from '../constants/exchanges';
import { Save, RefreshCw, AlertTriangle, CheckCircle, TrendingUp, Zap, BarChart2, Activity, Globe, Plus } from 'lucide-react';
import { useModal } from '../components/Modal';
import Disclaimer from '../components/Disclaimer';
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

const POPULAR_SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'DOGE/USDT',
    'MATIC/USDT',
    'CUSTOM' // Special option to enable custom input
];


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

const STRATEGY_PRESETS = {
    mean_reversion: [
        { name: 'Conservative', params: { rsi_period: 14, rsi_overbought: 75, rsi_oversold: 25, bb_period: 20, bb_std: 2.5 } },
        { name: 'Moderate', params: { rsi_period: 14, rsi_overbought: 70, rsi_oversold: 30, bb_period: 20, bb_std: 2.0 } },
        { name: 'Aggressive', params: { rsi_period: 7, rsi_overbought: 65, rsi_oversold: 35, bb_period: 14, bb_std: 1.5 } },
        { name: 'Range Trading', params: { rsi_period: 14, rsi_overbought: 65, rsi_oversold: 35, bb_period: 20, bb_std: 2.0 } }
    ],
    sma_crossover: [
        { name: 'Scalping', params: { fast_period: 5, slow_period: 20 } },
        { name: 'Swing', params: { fast_period: 20, slow_period: 50 } },
        { name: 'Trend', params: { fast_period: 50, slow_period: 200 } },
        { name: 'Trend Following', params: { fast_period: 20, slow_period: 100 } },
        { name: 'Automated Execution', params: { fast_period: 10, slow_period: 50 } }
    ],
    macd: [
        { name: 'Standard', params: { fast_period: 12, slow_period: 26, signal_period: 9 } },
        { name: 'Quick', params: { fast_period: 5, slow_period: 35, signal_period: 5 } },
        { name: 'Trend Analysis', params: { fast_period: 19, slow_period: 39, signal_period: 9 } }
    ],
    rsi: [
        { name: 'Standard', params: { period: 14, overbought: 70, oversold: 30 } },
        { name: 'Sensitive', params: { period: 7, overbought: 80, oversold: 20 } },
        { name: 'RSI Reversal', params: { period: 14, overbought: 80, oversold: 20 } }
    ],
    bollinger_breakout: [
        { name: 'Standard', params: { bb_period: 20, bb_std: 2.0, volume_factor: 1.5 } },
        { name: 'Aggressive', params: { bb_period: 20, bb_std: 1.5, volume_factor: 1.2 } },
        { name: 'Volume Breakout', params: { bb_period: 20, bb_std: 2.0, volume_factor: 2.0 } },
        { name: 'Volatility Scalping', params: { bb_period: 10, bb_std: 1.5, volume_factor: 1.2 } }
    ],
    momentum: [
        { name: 'Standard', params: { roc_period: 10, rsi_period: 14, rsi_min: 50, rsi_max: 70 } },
        { name: 'Quick', params: { roc_period: 5, rsi_period: 7, rsi_min: 45, rsi_max: 75 } },
        { name: 'Rapid Scalping', params: { roc_period: 3, rsi_period: 5, rsi_min: 40, rsi_max: 80 } }
    ],
    dca_dip: [
        { name: 'Standard', params: { ema_long: 200, ema_short: 20 } },
        { name: 'Aggressive', params: { ema_long: 100, ema_short: 10 } },
        { name: 'Smart DCA', params: { ema_long: 200, ema_short: 20 } },
        { name: 'Compound Growth', params: { ema_long: 150, ema_short: 25 } },
        { name: 'Secure HODL', params: { ema_long: 300, ema_short: 50 } }
    ],
    combined: [
        { name: 'Standard', params: { rsi_period: 14, fast_sma: 10, slow_sma: 50 } },
        { name: 'Market Neutral', params: { rsi_period: 14, fast_sma: 20, slow_sma: 50 } },
        { name: 'Technical Analysis', params: { rsi_period: 14, fast_sma: 10, slow_sma: 100 } },
        { name: 'Multi-Strategy', params: { rsi_period: 14, fast_sma: 20, slow_sma: 200 } },
        { name: 'Dynamic Allocation', params: { rsi_period: 21, fast_sma: 50, slow_sma: 200 } }
    ]
};

const RISK_PRESETS = [
    { name: 'Scalp', tp: 1.0, sl: 0.5 },
    { name: 'Day', tp: 2.0, sl: 1.0 },
    { name: 'Swing', tp: 5.0, sl: 2.0 },
    { name: 'Conservative', tp: 0.5, sl: 0.5 },
    { name: 'Aggressive', tp: 3.0, sl: 1.5 }
];

export default function Strategies() {
    const navigate = useNavigate();
    const toast = useToast();
    const modal = useModal();
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [suggestion, setSuggestion] = useState(null);
    const [exchanges, setExchanges] = useState([]);
    const [exchangesLoading, setExchangesLoading] = useState(true);
    const [customSymbol, setCustomSymbol] = useState(false);
    const [subscription, setSubscription] = useState(null);


    const fetchExchanges = async () => {
        setExchangesLoading(true);
        try {
            const response = await api.get('/exchanges');
            setExchanges(response.data.exchanges || []);
        } catch (err) {
            // Silent fail - use fallback list
            // Default to bybit if API fails
            setExchanges([DEFAULT_EXCHANGES[0]]); // Just bybit as fallback
        } finally {
            setExchangesLoading(false);
        }
    };

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const [statusRes, subRes] = await Promise.all([
                api.get('/status'),
                api.get('/billing/status')
            ]);

            setConfig(statusRes.data.config);
            setSubscription(subRes.data);
            setMessage(null);

            // Force dry_run to true for free plan
            if (subRes.data?.plan === 'free' && !statusRes.data.config.dry_run) {
                setConfig(prev => ({ ...prev, dry_run: true }));
            }

            const savedSuggestion = localStorage.getItem('suggested_strategy_params');
            if (savedSuggestion) {
                setSuggestion(JSON.parse(savedSuggestion));
            }
        } catch {
            setMessage({ type: 'error', text: 'Failed to load configuration.' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchExchanges();
        fetchConfig();
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
            take_profit_pct: preset.tp / 100,
            stop_loss_pct: preset.sl / 100
        }));
    };

    const applySuggestion = () => {
        if (!suggestion || !config) return;

        const params = { ...suggestion.params };
        let newTimeframe = config.timeframe;

        // Extract timeframe if present
        if (params.timeframe) {
            newTimeframe = params.timeframe;
            delete params.timeframe;
        }

        setConfig(prev => ({
            ...prev,
            strategy: suggestion.strategy,
            timeframe: newTimeframe,
            parameters: params
        }));

        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
        setMessage({ type: 'success', text: 'Applied suggested parameters and timeframe! Click Update to save.' });
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
                parameters: config.parameters || {}
            };

            // Save to API
            await api.post('/bot-configs', configForBackend);

            toast.success('Bot configuration added successfully');

            // Redirect to Main page
            navigate('/main');
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Failed to add bot configuration.';
            setMessage({ type: 'error', text: errorMsg });
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
    const currentPresets = STRATEGY_PRESETS[config.strategy] || {};

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Bot Management</h2>
                    <p className="text-muted-foreground mt-1">Configure your bot's trading logic and risk parameters.</p>
                </div>
                <button
                    onClick={fetchConfig}
                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-foreground transition-all"
                    title="Refresh Config"
                >
                    <RefreshCw size={20} />
                </button>
            </div>

            <Disclaimer compact />

            {suggestion && (
                <div className="glass p-6 rounded-xl border-l-4 border-l-blue-500 flex items-center justify-between animate-in slide-in-from-top-4 duration-500">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-500/20 rounded-full text-blue-400">
                            <TrendingUp size={24} />
                        </div>
                        <div>
                            <h4 className="font-bold text-blue-400">Optimization Result Found</h4>
                            <p className="text-sm text-muted-foreground">
                                Apply best parameters for <span className="font-medium text-foreground">{suggestion.strategy}</span>?
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={dismissSuggestion} className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">Dismiss</button>
                        <button onClick={applySuggestion} className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all shadow-lg shadow-blue-500/20">Apply</button>
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
                <div className="p-8 border-b border-white/5">
                    <h3 className="font-semibold text-lg text-foreground">Global Configuration</h3>
                    <p className="text-sm text-muted-foreground mt-1">These settings apply to the live trading bot.</p>
                </div>

                <div className="p-8 space-y-8">
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
                            <div className="flex gap-2">
                                {RISK_PRESETS.map(preset => (
                                    <button
                                        key={preset.name}
                                        onClick={() => applyRiskPreset(preset)}
                                        className="px-3 py-1 text-xs rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
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
                                    <div className="flex gap-2">
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

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
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
                                        value={POPULAR_SYMBOLS.includes(config.symbol) ? config.symbol : 'CUSTOM'}
                                        onChange={(e) => {
                                            if (e.target.value === 'CUSTOM') {
                                                setCustomSymbol(true);
                                            } else {
                                                handleChange('symbol', e.target.value);
                                            }
                                        }}
                                        className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pr-10 text-sm font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                    >
                                        {POPULAR_SYMBOLS.map((symbol) => (
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

                    <div className="pt-8 border-t border-white/5 flex items-center justify-between">
                        <label
                            className={`flex items-center gap-4 group ${subscription?.plan === 'free' ? 'cursor-not-allowed opacity-80' : 'cursor-pointer'}`}
                            onClick={(e) => {
                                e.preventDefault();
                                if (subscription?.plan === 'free') return;
                                handleChange('dry_run', !config.dry_run);
                            }}
                        >
                            <div className={`
                                w-14 h-8 rounded-full p-1 transition-colors duration-300
                                ${config.dry_run ? 'bg-primary' : 'bg-white/10'}
                                ${subscription?.plan === 'free' ? 'opacity-50' : ''}
                            `}>
                                <div className={`
                                    w-6 h-6 rounded-full bg-white shadow-lg transform transition-transform duration-300
                                    ${config.dry_run ? 'translate-x-6' : 'translate-x-0'}
                                `} />
                            </div>
                            <div>
                                <span className="block font-medium text-foreground">Practice Mode</span>
                                <span className="text-xs text-muted-foreground">Simulate trades without real money</span>
                                {subscription?.plan === 'free' && (
                                    <a href="/pricing" className="block text-xs text-primary mt-1 hover:underline">
                                        Upgrade for Real Trading
                                    </a>
                                )}
                            </div>
                        </label>

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
