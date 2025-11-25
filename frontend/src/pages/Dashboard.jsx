import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Activity, Wallet, TrendingUp, AlertCircle, Terminal, Wifi, WifiOff } from 'lucide-react';

export default function Dashboard() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [logs, setLogs] = useState([]);
    const [wsConnected, setWsConnected] = useState(false);
    const [trades, setTrades] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const logsEndRef = useRef(null);

    // Fetch Status and Trades
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statusRes, tradesRes] = await Promise.all([
                    axios.get('/api/status'),
                    axios.get('/api/trades')
                ]);
                setStatus(statusRes.data);
                setIsRunning(statusRes.data.is_running);
                setTrades(tradesRes.data);
            } catch (err) {
                setError('Failed to connect to bot');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const handleStartStop = async () => {
        try {
            if (isRunning) {
                await axios.post('/api/stop');
            } else {
                await axios.post('/api/start');
            }
            // Refresh status immediately
            const res = await axios.get('/api/status');
            setStatus(res.data);
            setIsRunning(res.data.is_running);
        } catch (err) {
            console.error("Failed to toggle bot:", err);
            alert("Failed to toggle bot status");
        }
    };

    // WebSocket for Logs
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setWsConnected(true);
            setLogs(prev => [...prev, '[SYSTEM] Connected to Log Stream']);
        };

        ws.onmessage = (event) => {
            setLogs(prev => {
                const newLogs = [...prev, event.data];
                if (newLogs.length > 500) return newLogs.slice(-500); // Keep last 500 logs
                return newLogs;
            });
        };

        ws.onerror = (event) => {
            console.error("WebSocket Error:", event);
            setLogs(prev => [...prev, `[SYSTEM] WebSocket Error: ${JSON.stringify(event)}`]);
        };

        ws.onclose = (event) => {
            setWsConnected(false);
            setLogs(prev => [...prev, `[SYSTEM] Disconnected. Code: ${event.code}, Reason: ${event.reason || 'None'}, Clean: ${event.wasClean}`]);
        };

        return () => {
            ws.close();
        };
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    if (loading) return <div className="p-8">Loading...</div>;
    if (error) return (
        <div className="p-8">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg flex items-center gap-2">
                <AlertCircle size={20} />
                {error}. Is the backend running?
            </div>
        </div>
    );

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold">Dashboard</h2>
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleStartStop}
                        className={`px-6 py-2 rounded-lg font-bold transition-all shadow-md ${isRunning
                                ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                                : 'bg-green-600 text-white hover:bg-green-700'
                            }`}
                    >
                        {isRunning ? 'Stop Trading' : 'Start Trading'}
                    </button>
                    <div className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 ${status.status === 'Active' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'}`}>
                        <div className={`w-2 h-2 rounded-full ${status.status === 'Active' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                        {status.status}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="p-6 bg-card rounded-xl border border-border">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-primary/10 rounded-lg text-primary">
                            <Wallet size={24} />
                        </div>
                        <div>
                            <h3 className="text-muted-foreground text-sm font-medium">Configuration</h3>
                            <p className="text-xl font-bold">{status.config.symbol}</p>
                        </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        Strategy: <span className="text-foreground font-medium">{status.config.strategy}</span>
                    </div>
                </div>

                <div className="p-6 bg-card rounded-xl border border-border">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-accent/10 rounded-lg text-accent-foreground">
                            <Activity size={24} />
                        </div>
                        <div>
                            <h3 className="text-muted-foreground text-sm font-medium">Mode</h3>
                            <p className="text-xl font-bold">{status.config.dry_run ? 'Dry Run' : 'Live Trading'}</p>
                        </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        Timeframe: <span className="text-foreground font-medium">{status.config.timeframe}</span>
                    </div>
                </div>

                <div className="p-6 bg-card rounded-xl border border-border">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-green-500/10 rounded-lg text-green-500">
                            <TrendingUp size={24} />
                        </div>
                        <div>
                            <h3 className="text-muted-foreground text-sm font-medium">Trade Amount</h3>
                            <p className="text-xl font-bold">${status.config.amount_usdt}</p>
                        </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        Fixed amount per trade
                    </div>
                </div>
            </div>

            {/* Recent Trades Section */}
            <div className="mb-8 bg-card rounded-xl border border-border overflow-hidden">
                <div className="p-4 border-b border-border flex justify-between items-center bg-muted/30">
                    <div className="flex items-center gap-2">
                        <TrendingUp size={18} className="text-muted-foreground" />
                        <h3 className="font-semibold">Recent Trades</h3>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-muted/50 text-muted-foreground font-medium">
                            <tr>
                                <th className="px-4 py-3">Time</th>
                                <th className="px-4 py-3">Symbol</th>
                                <th className="px-4 py-3">Side</th>
                                <th className="px-4 py-3">Type</th>
                                <th className="px-4 py-3">Price</th>
                                <th className="px-4 py-3">Amount</th>
                                <th className="px-4 py-3">PnL</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {trades.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="px-4 py-8 text-center text-muted-foreground">
                                        No trades recorded yet.
                                    </td>
                                </tr>
                            ) : (
                                trades.map((trade, i) => (
                                    <tr key={i} className="hover:bg-muted/30 transition-colors">
                                        <td className="px-4 py-3 text-muted-foreground">
                                            {new Date(trade.timestamp).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3 font-medium">{trade.symbol}</td>
                                        <td className={`px-4 py-3 font-bold ${trade.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                                            {trade.side}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${trade.type === 'OPEN' ? 'bg-blue-500/10 text-blue-500' : 'bg-purple-500/10 text-purple-500'}`}>
                                                {trade.type}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3">${trade.price.toFixed(2)}</td>
                                        <td className="px-4 py-3">{trade.amount}</td>
                                        <td className={`px-4 py-3 font-bold ${trade.pnl > 0 ? 'text-green-500' :
                                            trade.pnl < 0 ? 'text-red-500' :
                                                'text-muted-foreground'
                                            }`}>
                                            {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Logs Section */}
            <div className="bg-card rounded-xl border border-border overflow-hidden flex flex-col h-[500px]">
                <div className="p-4 border-b border-border flex justify-between items-center bg-muted/30">
                    <div className="flex items-center gap-2">
                        <Terminal size={18} className="text-muted-foreground" />
                        <h3 className="font-semibold">Live Logs</h3>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                        {wsConnected ? (
                            <span className="text-green-500 flex items-center gap-1"><Wifi size={14} /> Connected</span>
                        ) : (
                            <span className="text-destructive flex items-center gap-1"><WifiOff size={14} /> Disconnected</span>
                        )}
                    </div>
                </div>
                <div className="flex-1 p-4 bg-black/90 font-mono text-xs text-green-400 overflow-auto">
                    {logs.length === 0 && <div className="text-muted-foreground italic">Waiting for logs...</div>}
                    {logs.map((log, i) => (
                        <div key={i} className="mb-1 break-all whitespace-pre-wrap border-b border-white/5 pb-1">
                            {log}
                        </div>
                    ))}
                    <div ref={logsEndRef} />
                </div>
            </div>
        </div>
    );
}
