import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, RefreshCw, AlertTriangle, CheckCircle, TrendingUp, Zap, BarChart2, Activity } from 'lucide-react';

const STRATEGY_OPTIONS = [
    { value: 'mean_reversion', label: 'Mean Reversion', desc: 'Buy low, sell high using Bollinger Bands & RSI.', icon: Activity },
    { value: 'sma_crossover', label: 'SMA Crossover', desc: 'Trend following with moving average crosses.', icon: TrendingUp },
    { value: 'macd', label: 'MACD', desc: 'Momentum strategy using MACD histogram.', icon: BarChart2 },
    { value: 'rsi', label: 'RSI', desc: 'Simple overbought/oversold oscillator.', icon: Zap },
    { value: 'combined', label: 'Combined Strategy', desc: 'Multi-indicator confirmation setup.', icon: Activity }
];

const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function Strategies() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [restarting, setRestarting] = useState(false);
    const [message, setMessage] = useState(null);
    const [suggestion, setSuggestion] = useState(null);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/status');
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
        fetchConfig();
    }, []);

    const handleChange = (key, value) => {
        setConfig(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const applySuggestion = () => {
        if (!suggestion || !config) return;
        setConfig(prev => ({ ...prev, strategy: suggestion.strategy, ...suggestion.params }));
        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
        setMessage({ type: 'success', text: 'Applied suggested parameters! Click Update to save.' });
    };

    const dismissSuggestion = () => {
        localStorage.removeItem('suggested_strategy_params');
        setSuggestion(null);
    };

    const handleSave = async () => {
        if (!confirm("Saving will restart the bot to apply changes. Continue?")) return;
        setSaving(true);
        setMessage(null);
        try {
            await axios.post('/api/config', config);
            setMessage({ type: 'success', text: 'Configuration saved. Restarting bot...' });
            await axios.post('/api/restart');
            setRestarting(true);
            let retries = 0;
            const interval = setInterval(async () => {
                try {
                    await axios.get('/api/status');
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
    };

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

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
                        <label className="flex items-center gap-4 cursor-pointer group">
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
