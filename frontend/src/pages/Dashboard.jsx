import React, { useState, useEffect, useRef } from 'react';
import SentimentWidget from '../components/SentimentWidget';


import api from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Play, Square, Activity, DollarSign, TrendingUp, Terminal, Clock, AlertCircle } from 'lucide-react';
import TradeHistory from '../components/TradeHistory';
import BotInstancesTable from '../components/BotInstancesTable';
import Disclaimer from '../components/Disclaimer';

const StatCard = ({ title, value, subtext, icon: Icon, trend }) => (
    <div className="glass p-6 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Icon size={64} />
        </div>
        <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Icon size={20} />
            </div>
            <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        </div>
        <div className="text-2xl font-bold text-foreground tracking-tight">{value}</div>
        {subtext && (
            <p className={`text-xs mt-1 font-medium ${trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-muted-foreground'}`}>
                {subtext}
            </p>
        )}
    </div>
);

export default function Dashboard() {
    const [status, setStatus] = useState(null);
    const [trades, setTrades] = useState([]);
    const [logs, setLogs] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [wsConnected, setWsConnected] = useState(false);
    const logsEndRef = useRef(null);

    // Initial Data Fetch
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statusRes, tradesRes] = await Promise.all([
                    api.get('/status'),
                    api.get('/trades')
                ]);
                setStatus(statusRes.data);
                setIsRunning(statusRes.data.is_running);
                setTrades(tradesRes.data);
            } catch (err) {
                const errorMsg = err.response?.data?.detail || 'Failed to connect to bot';
                setError(errorMsg);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const handleStartStop = async (symbol = null) => {
        try {
            if (isRunning) {
                await api.post('/stop', {}, { params: { symbol } });
            } else {
                await api.post('/start', {}, { params: { symbol } });
            }
            // Refresh status immediately
            const res = await api.get('/status');
            setStatus(res.data);
            setIsRunning(res.data.is_running);
        } catch (err) {
            const errorMsg = err.response?.data?.detail || `Failed to ${isRunning ? 'stop' : 'start'} bot`;
            setError(errorMsg);
        }
    };

    // WebSocket for Logs
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setWsConnected(true);
        };

        ws.onmessage = (event) => {
            setLogs(prev => [...prev.slice(-99), event.data]); // Keep last 100 logs
        };

        ws.onclose = () => {
            setWsConnected(false);
        };

        return () => ws.close();
    }, []);

    // Auto-scroll logs (only within container, not entire page)
    useEffect(() => {
        if (logsEndRef.current) {
            const container = logsEndRef.current.parentElement;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }, [logs]);

    // Calculate PnL for Chart
    const pnlData = React.useMemo(() => {
        let cumulative = 0;
        return trades.map((t, i) => {
            // Backend returns 'pnl', frontend was using 'profit_loss'
            const value = t.pnl !== undefined ? t.pnl : (t.profit_loss || 0);
            cumulative += value;
            return {
                name: `Trade ${i + 1}`,
                pnl: value,
                cumulative: cumulative
            };
        });
    }, [trades]);

    const refreshTrades = async () => {
        try {
            const tradesRes = await api.get('/trades');
            setTrades(tradesRes.data);
            // Also refresh status to update total PnL
            const statusRes = await api.get('/status');
            setStatus(statusRes.data);
        } catch (err) {
            // Failed to refresh trades
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-muted-foreground animate-pulse">Initializing Dashboard...</p>
            </div>
        </div>
    );

    if (error) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="glass p-8 rounded-2xl text-center max-w-md border-red-500/20">
                <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
                <h2 className="text-xl font-bold text-red-500 mb-2">Connection Error</h2>
                <p className="text-muted-foreground">{error}</p>
                <button onClick={() => window.location.reload()} className="mt-6 px-6 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors">
                    Retry Connection
                </button>
            </div>
        </div>
    );

    return (
        <div className="space-y-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Dashboard
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Real-time market analysis and bot performance.
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${wsConnected ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                        {wsConnected ? 'Live Feed' : 'Disconnected'}
                    </div>

                    <button
                        onClick={handleStartStop}
                        className={`
                            flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all duration-300 shadow-lg
                            ${isRunning
                                ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20 shadow-red-500/10'
                                : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-primary/25 hover:shadow-primary/40'
                            }
                        `}
                    >
                        {isRunning ? <><Square size={18} fill="currentColor" /> Stop Bot</> : <><Play size={18} fill="currentColor" /> Start Bot</>}
                    </button>
                </div>

                {/* Disclaimer */}
                <Disclaimer compact />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Account Balance"
                    value={`${status?.balance?.total?.toFixed(2) || '0.00'} USDT`}
                    icon={DollarSign}
                    subtext={`Free: ${status?.balance?.free?.toFixed(2) || '0.00'} USDT`}
                />
                <StatCard
                    title="Total PnL"
                    value={`${status?.total_pnl?.toFixed(2) || '0.00'} USDT`}
                    icon={TrendingUp}
                    trend={status?.total_pnl >= 0 ? 'up' : 'down'}
                    subtext={status?.total_pnl >= 0 ? 'Profitable' : 'Loss'}
                />
                <StatCard
                    title="Active Trades"
                    value={status?.active_trades || 0}
                    icon={Activity}
                    subtext="Currently open positions"
                />
                <StatCard
                    title="Active Strategy"
                    value={status?.config?.strategy?.replace('_', ' ').toUpperCase() || 'N/A'}
                    icon={Activity}
                    subtext={
                        <span className="flex flex-col gap-1">
                            <span className={status?.config?.dry_run ? 'text-yellow-400' : 'text-green-400'}>
                                {status?.config?.dry_run ? '⚠️ Dry Run Mode' : '🚀 Live Trading'}
                            </span>
                            <span className="text-[10px] opacity-70">
                                {status?.config?.parameters ? Object.entries(status.config.parameters).map(([k, v]) => `${k}: ${v}`).join(', ') : ''}
                            </span>
                        </span>
                    }
                />
                <StatCard
                    title="Win Rate"
                    value={`${((trades.filter(t => (t.pnl !== undefined ? t.pnl : t.profit_loss) > 0).length / trades.length || 0) * 100).toFixed(1)}%`}
                    icon={Clock}
                    trend="up"
                    subtext={`${trades.length} total trades`}
                />
            </div>

            {/* AI Insights Section */}
            <div className="mb-8">
                <SentimentWidget />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">
                {/* Chart Section */}
                <div className="lg:col-span-2 glass rounded-2xl p-6 flex flex-col">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <TrendingUp size={20} className="text-primary" />
                        Performance History
                    </h3>
                    <div className="flex-1 w-full min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={pnlData}>
                                <defs>
                                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                <XAxis
                                    dataKey="name"
                                    stroke="#ffffff40"
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#ffffff40"
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `$${value}`}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="cumulative"
                                    stroke="#8b5cf6"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorPnl)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Logs Section */}
                <div className="glass rounded-2xl p-6 flex flex-col overflow-hidden border-l-4 border-l-primary/50">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Terminal size={20} className="text-primary" />
                        System Logs
                    </h3>
                    <div className="flex-1 overflow-y-auto font-mono text-xs space-y-2 pr-2 scrollbar-thin scrollbar-thumb-white/10">
                        {logs.length === 0 ? (
                            <div className="text-muted-foreground text-center mt-20 italic">
                                Waiting for logs...
                            </div>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="break-words p-2 rounded hover:bg-white/5 transition-colors border-l-2 border-transparent hover:border-primary/50">
                                    <span className="text-primary/60">[{new Date().toLocaleTimeString()}]</span>{' '}
                                    <span className={log.toLowerCase().includes('error') ? 'text-red-400' : 'text-gray-300'}>
                                        {log}
                                    </span>
                                </div>
                            ))
                        )}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>

            {/* Bot Instances Table */}
            <BotInstancesTable
                instances={status?.instances || status || {}}
                onStart={(symbol) => handleStartStop(symbol)}
                onStop={(symbol) => handleStartStop(symbol)}
                onStopAll={() => handleStartStop()}
                loading={loading}
            />

            {/* Trade History Section */}
            <div className="h-[500px] mt-8">
                <TradeHistory trades={trades} onRefresh={refreshTrades} />
            </div>
        </div>
    );
}
