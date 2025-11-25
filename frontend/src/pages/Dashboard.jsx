import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Play, Square, Activity, DollarSign, TrendingUp, Terminal, Clock, AlertCircle } from 'lucide-react';
import TradeHistory from '../components/TradeHistory';

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
                    axios.get('/api/status'),
                    axios.get('/api/trades')
                ]);
                setStatus(statusRes.data);
                setIsRunning(statusRes.data.is_running);
                setTrades(tradesRes.data);
            } catch (err) {
                const errorMsg = err.response?.data?.detail || 'Failed to connect to bot';
                setError(errorMsg);
                console.error('Dashboard data fetch error:', err);
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
            const errorMsg = err.response?.data?.detail || `Failed to ${isRunning ? 'stop' : 'start'} bot`;
            setError(errorMsg);
            console.error('Start/Stop error:', err);
        }
    };

    // WebSocket for Logs
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setWsConnected(true);
            console.log("WS Connected");
        };

        ws.onmessage = (event) => {
            setLogs(prev => [...prev.slice(-99), event.data]); // Keep last 100 logs
        };

        ws.onclose = () => {
            setWsConnected(false);
            console.log("WS Disconnected");
        };

        return () => ws.close();
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

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

    // Calculate PnL for Chart
    const pnlData = trades.map((t, i) => ({
        name: `Trade ${i + 1}`,
        pnl: t.profit_loss,
        cumulative: trades.slice(0, i + 1).reduce((acc, curr) => acc + curr.profit_loss, 0)
    }));

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
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total PnL"
                    value={`${status?.total_pnl?.toFixed(2) || '0.00'} USDT`}
                    icon={DollarSign}
                    trend={status?.total_pnl >= 0 ? 'up' : 'down'}
                    subtext={status?.total_pnl >= 0 ? '+12.5% this week' : '-2.3% this week'}
                />
                <StatCard
                    title="Active Trades"
                    value={status?.active_trades || 0}
                    icon={Activity}
                    subtext="Currently open positions"
                />
                <StatCard
                    title="Win Rate"
                    value={`${((trades.filter(t => t.profit_loss > 0).length / trades.length || 0) * 100).toFixed(1)}%`}
                    icon={TrendingUp}
                    trend="up"
                    subtext={`${trades.length} total trades`}
                />
                <StatCard
                    title="Uptime"
                    value="24h 12m"
                    icon={Clock}
                    subtext="Since last restart"
                />
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

            {/* Trade History Section */}
            <div className="h-[500px]">
                <TradeHistory trades={trades} />
            </div>
        </div>
    );
}
