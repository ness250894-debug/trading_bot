import React, { useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Loader2 } from 'lucide-react';

const STRATEGIES = [
    { name: 'Mean Reversion', params: { bb_length: 20, bb_std: 2.0, rsi_length: 14, rsi_buy: 30, rsi_sell: 70 } },
    { name: 'SMA Crossover', params: { short_window: 10, long_window: 30 } },
    { name: 'MACD', params: { fast: 12, slow: 26, signal: 9 } },
    { name: 'RSI', params: { period: 14, overbought: 70, oversold: 30 } },
];

export default function Backtest() {
    const [selectedStrategy, setSelectedStrategy] = useState(STRATEGIES[0]);
    const [params, setParams] = useState(STRATEGIES[0].params);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

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
        setError(null);
        try {
            const response = await axios.post('/api/backtest', {
                symbol: 'BTC/USDT',
                timeframe: '1m',
                days: 5,
                strategy: selectedStrategy.name,
                params: params
            });
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to run backtest');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold">Backtest Lab</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Configuration Panel */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-card p-6 rounded-xl border border-border">
                        <h3 className="font-semibold mb-4">Configuration</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">Strategy</label>
                                <select
                                    className="w-full bg-background border border-border rounded-md p-2 text-sm"
                                    value={selectedStrategy.name}
                                    onChange={handleStrategyChange}
                                >
                                    {STRATEGIES.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                                </select>
                            </div>

                            {Object.entries(params).map(([key, value]) => (
                                <div key={key}>
                                    <label className="block text-sm text-muted-foreground mb-1 capitalize">{key.replace('_', ' ')}</label>
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
                    {error && (
                        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20">
                            {error}
                        </div>
                    )}

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

                    {!results && !loading && !error && (
                        <div className="h-[400px] flex items-center justify-center text-muted-foreground border-2 border-dashed border-border rounded-xl">
                            Select a strategy and run backtest to see results
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
