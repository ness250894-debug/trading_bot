import React, { useState } from 'react';
import api from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Loader2, Save, FolderOpen, Trash2, X } from 'lucide-react';
import { useToast } from '../components/ToastContext';
import Disclaimer from '../components/Disclaimer';
import PlanGate from '../components/PlanGate';
import { formatLabel } from '../lib/utils';
import EditableText from '../components/constructor/EditableText';

const STRATEGIES = [
    { name: 'Mean Reversion', params: { bb_period: 20, bb_std: 2.0, rsi_period: 14, rsi_oversold: 30, rsi_overbought: 70 } },
    { name: 'SMA Crossover', params: { fast_period: 10, slow_period: 30 } },
    { name: 'MACD', params: { fast_period: 12, slow_period: 26, signal_period: 9 } },
    { name: 'RSI', params: { period: 14, overbought: 70, oversold: 30 } },
    { name: 'Bollinger Breakout', params: { bb_period: 20, bb_std: 2.0, volume_factor: 1.5 } },
    { name: 'Momentum', params: { roc_period: 10, rsi_period: 14, rsi_min: 50, rsi_max: 70 } },
    { name: 'DCA Dip', params: { ema_long: 200, ema_short: 20 } }
];

const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function Backtest() {
    const toast = useToast();
    const [selectedStrategy, setSelectedStrategy] = useState(STRATEGIES[0]);
    const [params, setParams] = useState(STRATEGIES[0].params);
    const [timeframe, setTimeframe] = useState('1m');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);

    // Template state
    const [templates, setTemplates] = useState([]);
    const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
    const [isLoadModalOpen, setIsLoadModalOpen] = useState(false);
    const [newTemplateName, setNewTemplateName] = useState('');
    const [templateLoading, setTemplateLoading] = useState(false);

    // Fetch templates
    const fetchTemplates = async () => {
        try {
            const response = await api.get('/backtest-templates');
            setTemplates(response.data.templates || []);
        } catch (error) {
            console.error('Failed to fetch templates:', error);
        }
    };

    const handleSaveTemplate = async (e) => {
        e.preventDefault();
        if (!newTemplateName) return;

        setTemplateLoading(true);
        try {
            await api.post('/backtest-templates', {
                name: newTemplateName,
                symbol: 'BTC/USDT', // TODO: Make symbol dynamic in backtest
                timeframe,
                strategy: selectedStrategy.name,
                parameters: JSON.stringify(params)
            });
            toast.success('Template saved successfully');
            setIsSaveModalOpen(false);
            setNewTemplateName('');
            fetchTemplates();
        } catch (error) {
            toast.error('Failed to save template');
        } finally {
            setTemplateLoading(false);
        }
    };

    const handleLoadTemplate = (template) => {
        try {
            const strategy = STRATEGIES.find(s => s.name === template.strategy);
            if (strategy) {
                setSelectedStrategy(strategy);
                setParams(JSON.parse(template.parameters));
                setTimeframe(template.timeframe);
                setIsLoadModalOpen(false);
                toast.success(`Loaded template: ${template.name}`);
            }
        } catch (error) {
            console.error('Error loading template:', error);
            toast.error('Failed to load template parameters');
        }
    };

    const handleDeleteTemplate = async (id) => {
        try {
            await api.delete(`/backtest-templates/${id}`);
            setTemplates(prev => prev.filter(t => t.id !== id));
            toast.success('Template deleted');
        } catch (error) {
            toast.error('Failed to delete template');
        }
    };

    const handleStrategyChange = (e) => {
        const strategy = STRATEGIES.find(s => s.name === e.target.value);
        setSelectedStrategy(strategy);
        setParams(strategy.params);
    };

    const handleParamChange = (key, value) => {
        setParams(prev => ({ ...prev, [key]: parseFloat(value) }));
    };

    const runBacktest = async () => {
        setLoading(true);
        try {
            const response = await api.post('/backtest', {
                symbol: 'BTC/USDT',
                timeframe: timeframe,
                days: 5,
                strategy: selectedStrategy.name,
                params: params
            });
            setResults(response.data);
            toast.success('Backtest completed successfully!');
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to run backtest');
        } finally {
            setLoading(false);
        }
    };

    return (
        <PlanGate feature="Backtesting" explanation="Test your strategies against historical data to verify performance before trading with real money.">
            <div className="p-8 max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-3xl font-bold">
                        <EditableText
                            configPath="pages.backtest.pageTitle"
                            defaultValue="Backtest Lab"
                        />
                    </h2>
                </div>

                <Disclaimer compact />

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Configuration Panel */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-card p-6 rounded-xl border border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold">Configuration</h3>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => { fetchTemplates(); setIsLoadModalOpen(true); }}
                                        className="p-1.5 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-primary transition-colors"
                                        title="Load Template"
                                    >
                                        <FolderOpen size={18} />
                                    </button>
                                    <button
                                        onClick={() => setIsSaveModalOpen(true)}
                                        className="p-1.5 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-primary transition-colors"
                                        title="Save Template"
                                    >
                                        <Save size={18} />
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Strategy</label>
                                    <div className="relative">
                                        <select
                                            className="w-full bg-black/20 border border-white/10 rounded-xl p-3 pr-10 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                            value={selectedStrategy.name}
                                            onChange={handleStrategyChange}
                                        >
                                            {STRATEGIES.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                                        </select>
                                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Timeframe</label>
                                    <div className="relative">
                                        <select
                                            className="w-full bg-black/20 border border-white/10 rounded-xl p-3 pr-10 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all appearance-none cursor-pointer hover:bg-black/30"
                                            value={timeframe}
                                            onChange={(e) => setTimeframe(e.target.value)}
                                        >
                                            {TIMEFRAME_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}
                                        </select>
                                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </div>
                                </div>

                                {Object.entries(params).map(([key, value]) => (
                                    <div key={key}>
                                        <label className="block text-sm text-muted-foreground mb-1 capitalize">{formatLabel(key)}</label>
                                        <input
                                            type="number"
                                            className="w-full bg-background border border-border rounded-md p-2 text-sm"
                                            value={value}
                                            onChange={(e) => handleParamChange(key, e.target.value)}
                                        />
                                    </div>
                                ))}

                                <button
                                    onClick={runBacktest}
                                    disabled={loading}
                                    className="w-full bg-primary text-primary-foreground py-2 rounded-md font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                                >
                                    {loading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
                                    Run Backtest
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Results Panel */}
                    <div className="lg:col-span-3 space-y-6">
                        {results && (
                            <>
                                {/* Metrics Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-card p-4 rounded-xl border border-border">
                                        <p className="text-sm text-muted-foreground">Total Return</p>
                                        <p className={`text-xl font-bold ${results.metrics.total_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                            {results.metrics.total_return.toFixed(2)}%
                                        </p>
                                    </div>
                                    <div className="bg-card p-4 rounded-xl border border-border">
                                        <p className="text-sm text-muted-foreground">Win Rate</p>
                                        <p className="text-xl font-bold">{results.metrics.win_rate.toFixed(2)}%</p>
                                    </div>
                                    <div className="bg-card p-4 rounded-xl border border-border">
                                        <p className="text-sm text-muted-foreground">Trades</p>
                                        <p className="text-xl font-bold">{results.metrics.total_trades}</p>
                                    </div>
                                    <div className="bg-card p-4 rounded-xl border border-border">
                                        <p className="text-sm text-muted-foreground">Final Balance</p>
                                        <p className="text-xl font-bold">${results.metrics.final_balance.toFixed(2)}</p>
                                    </div>
                                </div>

                                {/* Chart */}
                                <div className="bg-card p-6 rounded-xl border border-border h-[400px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={results.chart_data}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                            <XAxis dataKey="timestamp" hide />
                                            <YAxis domain={['auto', 'auto']} stroke="#888" />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                                                itemStyle={{ color: '#e2e8f0' }}
                                            />
                                            <Line type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={2} />
                                            {/* Add more lines for indicators if available */}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Trade History */}
                                <div className="bg-card rounded-xl border border-border overflow-hidden">
                                    <div className="p-4 border-b border-border">
                                        <h3 className="font-semibold">Trade History</h3>
                                    </div>
                                    <div className="max-h-[300px] overflow-auto">
                                        <table className="w-full text-sm text-left">
                                            <thead className="bg-muted/50 text-muted-foreground">
                                                <tr>
                                                    <th className="p-3">Time</th>
                                                    <th className="p-3">PnL</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {results.trades.map((trade, i) => (
                                                    <tr key={i} className="border-b border-border hover:bg-muted/20">
                                                        <td className="p-3">{new Date(trade.time).toLocaleString()}</td>
                                                        <td className={`p-3 font-medium ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                            {trade.pnl > 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </>
                        )}

                        {!results && !loading && (
                            <div className="h-[400px] flex items-center justify-center text-muted-foreground border-2 border-dashed border-border rounded-xl">
                                Select a strategy and run backtest to see results
                            </div>
                        )}
                    </div>
                </div>
            </div>
            {/* Save Template Modal */}
            {isSaveModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-card border border-border p-6 rounded-xl w-full max-w-md m-4">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Save Configuration</h3>
                            <button onClick={() => setIsSaveModalOpen(false)} className="text-muted-foreground hover:text-foreground">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSaveTemplate}>
                            <input
                                type="text"
                                value={newTemplateName}
                                onChange={(e) => setNewTemplateName(e.target.value)}
                                placeholder="Template Name (e.g. Scalping Setup)"
                                className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 mb-4 focus:border-primary/50 outline-none"
                                autoFocus
                            />
                            <div className="flex justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={() => setIsSaveModalOpen(false)}
                                    className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={!newTemplateName || templateLoading}
                                    className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                                >
                                    {templateLoading ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Load Template Modal */}
            {isLoadModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-card border border-border p-6 rounded-xl w-full max-w-md m-4 max-h-[80vh] flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Load Configuration</h3>
                            <button onClick={() => setIsLoadModalOpen(false)} className="text-muted-foreground hover:text-foreground">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-2">
                            {templates.length === 0 ? (
                                <div className="text-center text-muted-foreground py-8">
                                    No saved templates
                                </div>
                            ) : (
                                templates.map(template => (
                                    <div key={template.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg group hover:bg-white/10 transition-all">
                                        <button
                                            onClick={() => handleLoadTemplate(template)}
                                            className="flex-1 text-left"
                                        >
                                            <div className="font-medium">{template.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {template.strategy} • {template.timeframe}
                                            </div>
                                        </button>
                                        <button
                                            onClick={() => handleDeleteTemplate(template.id)}
                                            className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </PlanGate>
    );
}
