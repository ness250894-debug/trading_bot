import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, RefreshCw, AlertTriangle, CheckCircle, Power } from 'lucide-react';

const STRATEGY_OPTIONS = [
    { value: 'mean_reversion', label: 'Mean Reversion' },
    { value: 'sma_crossover', label: 'SMA Crossover' },
    { value: 'macd', label: 'MACD' },
    { value: 'rsi', label: 'RSI' },
    { value: 'combined', label: 'Combined Strategy' }
];

const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function Strategies() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [restarting, setRestarting] = useState(false);
    const [message, setMessage] = useState(null);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/status');
            setConfig(response.data.config);
            setMessage(null);
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

    const handleSave = async () => {
        if (!confirm("Saving will restart the bot to apply changes. Continue?")) return;

        setSaving(true);
        setMessage(null);
        try {
            // 1. Save Config
            await axios.post('/api/config', config);
            setMessage({ type: 'success', text: 'Configuration saved. Restarting bot...' });

            // 2. Trigger Restart
            await axios.post('/api/restart');
            setRestarting(true);

            // 3. Poll for recovery
            let retries = 0;
            const interval = setInterval(async () => {
                try {
                    await axios.get('/api/status');
                    clearInterval(interval);
                    setRestarting(false);
                    setSaving(false);
                    setMessage({
                        type: 'success',
                        text: 'Bot restarted successfully! Please go to Dashboard and click "Start Trading" to resume.'
                    });
                    fetchConfig();
                } catch (e) {
                    retries++;
                    if (retries > 20) {
                        clearInterval(interval);
                        setRestarting(false);
                        setSaving(false);
                        setMessage({ type: 'error', text: 'Restart timed out. Please check terminal.' });
                    }
                }
            }, 1000);

        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to save configuration.' });
            setSaving(false);
        }
    };

    const handleRestart = async () => {
        if (!confirm("Are you sure you want to restart the bot?")) return;
        setRestarting(true);
        try {
            await axios.post('/api/restart');
            setMessage({ type: 'success', text: 'Bot is restarting...' });
            // Poll for status
            let retries = 0;
            const interval = setInterval(async () => {
                try {
                    await axios.get('/api/status');
                    clearInterval(interval);
                    setRestarting(false);
                    setMessage({ type: 'success', text: 'Bot restarted!' });
                } catch (e) {
                    retries++;
                    if (retries > 20) {
                        clearInterval(interval);
                        setRestarting(false);
                        setMessage({ type: 'error', text: 'Restart timed out.' });
                    }
                }
            }, 1000);
        } catch (err) {
            setRestarting(false);
            setMessage({ type: 'error', text: 'Failed to restart.' });
        }
    };

    if (loading) return <div className="p-8">Loading configuration...</div>;

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold">Strategy Manager</h2>
                <button
                    onClick={fetchConfig}
                    className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                    title="Refresh Config"
                >
                    <RefreshCw size={20} />
                </button>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'}`}>
                    {message.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                    {message.text}
                </div>
            )}

            <div className="bg-card rounded-xl border border-border overflow-hidden">
                <div className="p-6 border-b border-border">
                    <h3 className="font-semibold text-lg">Global Configuration</h3>
                    <p className="text-sm text-muted-foreground">These settings apply to the live trading bot.</p>
                </div>

                <div className="p-6 space-y-6">
                    {/* Strategy Selection */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium mb-2">Active Strategy</label>
                            <select
                                className="w-full bg-background border border-border rounded-md p-2.5"
                                value={config.strategy}
                                onChange={(e) => handleChange('strategy', e.target.value)}
                            >
                                {STRATEGY_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                            <p className="text-xs text-muted-foreground mt-1">
                                Select the primary logic for signal generation.
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">Timeframe</label>
                            <select
                                className="w-full bg-background border border-border rounded-md p-2.5"
                                value={config.timeframe}
                                onChange={(e) => handleChange('timeframe', e.target.value)}
                            >
                                {TIMEFRAME_OPTIONS.map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Trading Parameters */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium mb-2">Trade Amount (USDT)</label>
                            <input
                                type="number"
                                className="w-full bg-background border border-border rounded-md p-2.5"
                                value={config.amount_usdt}
                                onChange={(e) => handleChange('amount_usdt', parseFloat(e.target.value))}
                            />
                        </div>

                        <div className="flex items-center space-x-3 pt-8">
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={config.dry_run}
                                    onChange={(e) => handleChange('dry_run', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                <span className="ml-3 text-sm font-medium">Dry Run Mode</span>
                            </label>
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="pt-6 border-t border-border flex justify-end gap-4">
                        <button
                            onClick={handleSave}
                            disabled={saving || restarting}
                            className="bg-primary text-primary-foreground px-6 py-2.5 rounded-lg font-medium flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
                            Update
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
