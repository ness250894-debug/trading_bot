import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Save, RefreshCw, AlertTriangle, CheckCircle, TrendingUp, Zap, BarChart2, Activity, Globe } from 'lucide-react';
import { useModal } from '../components/Modal';

const STRATEGY_OPTIONS = [
    { value: 'mean_reversion', label: 'Mean Reversion', desc: 'Buy low, sell high using Bollinger Bands & RSI.', icon: Activity },
    { value: 'sma_crossover', label: 'SMA Crossover', desc: 'Trend following with moving average crosses.', icon: TrendingUp },
    { value: 'macd', label: 'MACD', desc: 'Momentum strategy using MACD histogram.', icon: BarChart2 },
    { value: 'rsi', label: 'RSI', desc: 'Simple overbought/oversold oscillator.', icon: Zap },
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
        { name: 'Aggressive', params: { rsi_period: 7, rsi_overbought: 65, rsi_oversold: 35, bb_period: 14, bb_std: 1.5 } }
    ],
    sma_crossover: [
        { name: 'Scalping', params: { fast_period: 5, slow_period: 20 } },
        { name: 'Swing', params: { fast_period: 20, slow_period: 50 } },
        { name: 'Trend', params: { fast_period: 50, slow_period: 200 } }
    ],
    macd: [
        { name: 'Standard', params: { fast_period: 12, slow_period: 26, signal_period: 9 } },
        { name: 'Quick', params: { fast_period: 5, slow_period: 35, signal_period: 5 } }
    ],
    rsi: [
        { name: 'Standard', params: { period: 14, overbought: 70, oversold: 30 } },
        { name: 'Sensitive', params: { period: 7, overbought: 80, oversold: 20 } }
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
    const modal = useModal();
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [restarting, setRestarting] = useState(false);
    const [message, setMessage] = useState(null);
    const [suggestion, setSuggestion] = useState(null);
    const [exchanges, setExchanges] = useState([]);
    const [exchangesLoading, setExchangesLoading] = useState(true);

    const fetchExchanges = async () => {
        setExchangesLoading(true);
        try {
            const response = await api.get('/exchanges');
            setExchanges(response.data.exchanges || []);
        } catch (err) {
            console.error('Failed to load exchanges:', err);
            // Default to bybit if API fails
            setExchanges([{ name: 'bybit', display_name: 'Bybit' }]);
        } finally {
            setExchangesLoading(false);
        }
    };

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const response = await api.get('/status');
            setConfig(response.data.config);
            setMessage(null);

            const savedSuggestion = localStorage.getItem('suggested_strategy_params');
            if (savedSuggestion) {
                setSuggestion(JSON.parse(savedSuggestion));
            }
        } catch (err) {
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
        setConfig(prev => ({ ...prev, strategy: suggestion.strategy, parameters: { ...suggestion.params } }));
        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
        setMessage({ type: 'success', text: 'Applied suggested parameters! Click Update to save.' });
    };

    const dismissSuggestion = () => {
        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
    };

    const handleSave = async () => {
        modal.confirm({
            title: 'Restart Bot',
            message: 'Saving will restart the bot to apply changes. Continue?',
            confirmText: 'Save & Restart',
            cancelText: 'Cancel',
            type: 'warning',
            onConfirm: async () => {
                setSaving(true);
                setMessage(null);
                try {
                    await api.post('/config', config);
                    setMessage({ type: 'success', text: 'Configuration saved. Restarting bot...' });
                    await api.post('/restart');
                    setRestarting(true);
                    let retries = 0;
                    const interval = setInterval(async () => {
                        try {
                            await api.get('/status');
                            clearInterval(interval);
                            setRestarting(false);
                            setSaving(false);
                            setMessage({ type: 'success', text: 'Bot restarted successfully!' });
                            fetchConfig();
                        } catch (e) {
                            retries++;
                            if (retries > 20) {
                                clearInterval(interval);
                                setRestarting(false);
                                setSaving(false);
                                setMessage({ type: 'error', text: 'Restart timed out.' });
                            }
                        }
                    }, 1000);
                } catch (err) {
                    setMessage({ type: 'error', text: 'Failed to save configuration.' });
                    setSaving(false);
                }
            }
        });
    };

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    const currentParams = STRATEGY_PARAMS[config.strategy] || {};
    const currentPresets = STRATEGY_PRESETS[config.strategy] || [];

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Strategy Manager</h2>
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
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <Globe size={18} className="text-primary" />
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Trading Exchange</label>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                            {exchangesLoading ? (
                                <div className="col-span-full text-center text-muted-foreground py-4">
                                    Loading exchanges...
                                </div>
                            ) : (
                                exchanges.map((exchange) => {
                                    const isActive = (config.exchange || 'bybit') === exchange.name;
                                    return (
                                        <div
                                            key={exchange.name}
                                            onClick={() => handleChange('exchange', exchange.name)}
                                            className={`
                                                cursor-pointer p-4 rounded-xl border transition-all duration-300
                                                ${isActive
                                                    ? 'bg-primary/10 border-primary/50 shadow-lg shadow-primary/10'
                                                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                                                }
                                            `}
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className={`font-bold text-sm ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                                                    {exchange.display_name}
                                                </h4>
                                                {isActive && <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(139,92,246,0.6)]" />}
                                            </div>
                                            <div className="flex gap-1 flex-wrap">
                                                {exchange.supports_futures && (
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">Futures</span>
                                                )}
                                                {exchange.supports_spot && (
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">Spot</span>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Selected: <span className="font-medium text-foreground">{exchanges.find(e => e.name === (config.exchange || 'bybit'))?.display_name || 'ByBit'}</span>
                            {exchanges.find(e => e.name === (config.exchange || 'bybit'))?.supports_demo && (
                                <span className="ml-2 text-primary">• Testnet Available</span>
                            )}
                        </p>
                    </div>

                    {/* Strategy Selection Cards */}
                    <div className="space-y-4">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Active Strategy</label>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {STRATEGY_OPTIONS.map((opt) => {
                                const Icon = opt.icon;
                                const isActive = config.strategy === opt.value;
                                return (
                                    <div
                                        key={opt.value}
                                        onClick={() => handleChange('strategy', opt.value)}
                                        className={`
                                            cursor-pointer p-5 rounded-xl border transition-all duration-300 relative overflow-hidden group
                                            ${isActive
                                                ? 'bg-primary/10 border-primary/50 shadow-lg shadow-primary/10'
                                                : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10'
                                            }
                                        `}
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <Icon size={24} className={isActive ? 'text-primary' : 'text-muted-foreground'} />
                                            {isActive && <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(139,92,246,0.5)]" />}
                                        </div>
                                        <h4 className={`font-bold mb-1 ${isActive ? 'text-foreground' : 'text-muted-foreground group-hover:text-foreground'}`}>
                                            {opt.label}
                                        </h4>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            {opt.desc}
                                        </p>
                                    </div>
                                );
                            })}
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-4">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Timeframe</label>
                            <div className="grid grid-cols-3 gap-2">
                                {TIMEFRAME_OPTIONS.map(opt => (
                                    <button
                                        key={opt}
                                        onClick={() => handleChange('timeframe', opt)}
                                        className={`
                                            py-2 rounded-lg text-sm font-medium transition-all
                                            ${config.timeframe === opt
                                                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                                                : 'bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-foreground'
                                            }
                                        `}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Trade Amount (USDT)</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-4 pl-12 text-lg font-mono focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                    value={config.amount_usdt}
                                    onChange={(e) => handleChange('amount_usdt', parseFloat(e.target.value))}
                                />
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                            </div>
                        </div>
                    </div>

                    <div className="pt-8 border-t border-white/5 flex items-center justify-between">
                        <label
                            className="flex items-center gap-4 cursor-pointer group"
                            onClick={(e) => {
                                e.preventDefault();
                                handleChange('dry_run', !config.dry_run);
                            }}
                        >
                            <div className={`
                                w-14 h-8 rounded-full p-1 transition-colors duration-300
                                ${config.dry_run ? 'bg-primary' : 'bg-white/10'}
                            `}>
                                <div className={`
                                    w-6 h-6 rounded-full bg-white shadow-lg transform transition-transform duration-300
                                    ${config.dry_run ? 'translate-x-6' : 'translate-x-0'}
                                `} />
                            </div>
                            <div>
                                <span className="block font-medium text-foreground">Dry Run Mode</span>
                                <span className="text-xs text-muted-foreground">Simulate trades without real money</span>
                            </div>
                        </label>

                        <button
                            onClick={handleSave}
                            disabled={saving || restarting}
                            className="bg-primary hover:bg-primary/90 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {saving ? <RefreshCw className="animate-spin" size={20} /> : <Save size={20} />}
                            Update Configuration
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
