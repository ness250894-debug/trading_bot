import React, { useState, useEffect, useContext } from 'react';
import api from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, DollarSign, TrendingUp, Clock, AlertCircle, PieChart as PieChartIcon, BarChart2 } from 'lucide-react';
import TradeHistory from '../components/TradeHistory';
import TradingGoalsWidget from '../components/TradingGoalsWidget';

import { formatStrategyName } from '../lib/utils';
import { ToastContext } from '../components/ToastContext';
import EditableText from '../components/constructor/EditableText';

const BalanceCard = ({ status, onRefreshBalance, refreshing, trades, exchangeBalances, exchangeBalancesLoading }) => {
    const isPracticeMode = status?.config?.dry_run;
    const hasApiConnected = exchangeBalances?.has_keys || (status?.balance?.total !== undefined && status?.balance?.total !== null);

    // Exchange display names
    const exchangeNames = {
        'bybit': 'Bybit',
        'binance': 'Binance',
        'okx': 'OKX',
        'kraken': 'Kraken',
        'coinbase': 'Coinbase'
    };

    return (
        <div className="glass p-8 rounded-2xl relative overflow-hidden group col-span-1">

            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                        <DollarSign size={24} />
                    </div>
                    <h3 className="text-base font-medium text-muted-foreground">Exchange Balances</h3>
                </div>
                {isPracticeMode && hasApiConnected && (
                    <button
                        onClick={onRefreshBalance}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors text-sm disabled:opacity-50 relative z-20"
                        title="Reset practice balance to $1,000"
                    >
                        {refreshing ? (
                            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
                            </svg>
                        )}
                        Reset
                    </button>
                )}
            </div>

            {!hasApiConnected ? (
                <div className="py-8 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted-foreground/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                    </div>
                    <h4 className="text-lg font-semibold mb-2">Connect Your API Keys</h4>
                    <p className="text-muted-foreground text-sm max-w-md mx-auto">
                        To view your account balance and start trading, please connect your exchange API keys in Settings.
                    </p>
                </div>
            ) : exchangeBalancesLoading ? (
                <div className="py-8 text-center">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-muted-foreground text-sm">Fetching balances from exchanges...</p>
                </div>
            ) : (
                <>
                    {/* Total Balance */}
                    <div className="relative z-10 mb-6">
                        <div className="text-sm text-muted-foreground mb-2">Total Balance (All Exchanges)</div>
                        <div className="text-4xl font-bold text-foreground tracking-tight mb-1">
                            ${exchangeBalances?.total_usdt?.toFixed(2) || '0.00'}
                        </div>
                        <div className="text-xs text-muted-foreground">USDT across {exchangeBalances?.exchanges?.length || 0} exchange(s)</div>
                    </div>

                    {/* Per-Exchange Breakdown */}
                    {exchangeBalances?.exchanges?.length > 0 && (
                        <div className="space-y-3 mb-4">
                            <div className="text-sm text-muted-foreground font-medium">Balance by Exchange</div>
                            {exchangeBalances.exchanges.map((ex, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${ex.status === 'connected' ? 'bg-green-400' : 'bg-red-400'}`} />
                                        <span className="font-medium capitalize">{exchangeNames[ex.exchange] || ex.exchange}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold">${ex.usdt_total?.toFixed(2) || '0.00'}</div>
                                        {ex.usdt_free !== undefined && ex.usdt_free !== ex.usdt_total && (
                                            <div className="text-xs text-muted-foreground">
                                                Available: ${ex.usdt_free?.toFixed(2)}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="pt-4 border-t border-white/10 flex items-center justify-between relative z-10">
                        <div className="flex items-center gap-4 text-sm">
                            {isPracticeMode && (
                                <div className="px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                    <p className="text-xs text-yellow-400 flex items-center gap-1">
                                        <span>⚠️</span>
                                        <span>Practice Mode Active</span>
                                    </p>
                                </div>
                            )}
                        </div>
                        {!isPracticeMode && (
                            <div className="px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                                <p className="text-xs text-green-400 flex items-center gap-1">
                                    <span>🚀</span>
                                    <span>Live Trading Active</span>
                                </p>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

const PnLCard = ({ trades, totalPnl }) => {
    const winningTrades = trades.filter(t => (t.pnl !== undefined ? t.pnl : t.profit_loss) > 0);
    const losingTrades = trades.filter(t => (t.pnl !== undefined ? t.pnl : t.profit_loss) < 0);
    const winRate = trades.length > 0 ? (winningTrades.length / trades.length * 100) : 0;

    return (
        <div className="glass p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <TrendingUp size={64} />
            </div>
            <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <TrendingUp size={20} />
                </div>
                <h3 className="text-sm font-medium text-muted-foreground">Total PnL</h3>
            </div>
            <div className="text-3xl font-bold text-foreground tracking-tight mb-3">
                ${totalPnl?.toFixed(2) || '0.00'} USDT
            </div>
            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Win Rate:</span>
                    <span className="font-semibold text-green-400">{winRate.toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Winning Trades:</span>
                    <span className="font-semibold text-green-400">{winningTrades.length}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Losing Trades:</span>
                    <span className="font-semibold text-red-400">{losingTrades.length}</span>
                </div>
                <div className={`px-3 py-1.5 rounded-lg ${totalPnl >= 0 ? 'bg-green-500/10 border border-green-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
                    <p className={`text-xs flex items-center gap-1 ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        <span>{totalPnl >= 0 ? '📈' : '📉'}</span>
                        <span>{totalPnl >= 0 ? 'Profitable' : 'Loss'}</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

const COLORS = ['#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#6366f1'];

export default function Dashboard() {
    const toast = useContext(ToastContext);
    const [status, setStatus] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pollingInterval] = useState(30000); // 30 seconds polling interval
    const [refreshingBalance, setRefreshingBalance] = useState(false);
    const [exchangeBalances, setExchangeBalances] = useState(null);
    const [exchangeBalancesLoading, setExchangeBalancesLoading] = useState(true);

    // Fetch Exchange Balances
    useEffect(() => {
        const fetchExchangeBalances = async () => {
            try {
                const response = await api.get('/exchange-balances');
                setExchangeBalances(response.data);
            } catch (err) {
                console.error('Failed to fetch exchange balances:', err);
            } finally {
                setExchangeBalancesLoading(false);
            }
        };

        fetchExchangeBalances();
        // Refresh exchange balances every 60 seconds
        const balanceInterval = setInterval(fetchExchangeBalances, 60000);
        return () => clearInterval(balanceInterval);
    }, []);

    // Initial Data Fetch
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statusRes, tradesRes] = await Promise.all([
                    api.get('/status'),
                    api.get('/trades')
                ]);
                setStatus(statusRes.data);
                setTrades(tradesRes.data.trades || []);
            } catch (err) {
                const errorMsg = err.response?.data?.detail || 'Failed to connect to bot';
                setError(errorMsg);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, pollingInterval);
        return () => clearInterval(interval);
    }, [pollingInterval]);

    // Calculate PnL for Chart
    const pnlData = React.useMemo(() => {
        if (!trades || !Array.isArray(trades) || trades.length === 0) return [];

        let cumulative = 0;
        return trades.map((t, i) => {
            const value = t.pnl !== undefined ? t.pnl : (t.profit_loss || 0);
            cumulative += value;
            return {
                name: `Trade ${i + 1}`,
                pnl: value,
                cumulative: cumulative
            };
        });
    }, [JSON.stringify(trades)]);

    // Calculate Win Rate Over Time
    const winRateData = React.useMemo(() => {
        if (!trades || trades.length === 0) return [];

        const data = [];
        let wins = 0;
        let total = 0;

        trades.forEach((t, i) => {
            total++;
            if ((t.pnl !== undefined ? t.pnl : t.profit_loss) > 0) wins++;

            if ((i + 1) % 5 === 0 || i === trades.length - 1) {
                data.push({
                    name: `Trade ${i + 1}`,
                    winRate: (wins / total) * 100
                });
            }
        });

        return data;
    }, [JSON.stringify(trades)]);

    // Calculate Symbol Performance
    const symbolPerformance = React.useMemo(() => {
        if (!trades || trades.length === 0) return [];

        const symbolMap = {};
        trades.forEach(t => {
            const symbol = t.symbol || 'Unknown';
            const pnl = t.pnl !== undefined ? t.pnl : t.profit_loss || 0;

            if (!symbolMap[symbol]) {
                symbolMap[symbol] = { symbol, pnl: 0, count: 0 };
            }
            symbolMap[symbol].pnl += pnl;
            symbolMap[symbol].count++;
        });

        return Object.values(symbolMap).sort((a, b) => b.pnl - a.pnl);
    }, [JSON.stringify(trades)]);

    // Calculate Daily PnL (group by date)
    const dailyPnlData = React.useMemo(() => {
        if (!trades || trades.length === 0) return [];

        const dailyMap = {};
        trades.forEach(t => {
            const date = t.timestamp ? new Date(t.timestamp).toLocaleDateString() : 'Unknown';
            const pnl = t.pnl !== undefined ? t.pnl : t.profit_loss || 0;

            if (!dailyMap[date]) {
                dailyMap[date] = { date, pnl: 0 };
            }
            dailyMap[date].pnl += pnl;
        });

        return Object.values(dailyMap).slice(-10); // Last 10 days
    }, [JSON.stringify(trades)]);

    const refreshTrades = async () => {
        try {
            const tradesRes = await api.get('/trades');
            setTrades(tradesRes.data.trades || []);
            const statusRes = await api.get('/status');
            setStatus(statusRes.data);
        } catch (err) {
            // Failed to refresh trades
        }
    };

    const handleRefreshBalance = async () => {
        if (!status?.config?.dry_run || refreshingBalance) return;

        setRefreshingBalance(true);
        try {
            // In practice mode, we can reset the balance via API
            // This would need a backend endpoint to reset practice balance
            // For now, we'll just refresh the status
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
            const statusRes = await api.get('/status');
            setStatus(statusRes.data);
            toast.success('Practice balance has been reset to $1,000!');
        } catch (err) {
            toast.error('Failed to refresh balance. Please try again.');
        } finally {
            setRefreshingBalance(false);
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
                        <EditableText
                            configPath="pages.dashboard.pageTitle"
                            defaultValue="Analytics Dashboard"
                        />
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        <EditableText
                            configPath="pages.dashboard.subtitle"
                            defaultValue="Comprehensive performance insights and trading analytics."
                        />
                    </p>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 gap-6">
                <BalanceCard
                    status={status}
                    onRefreshBalance={handleRefreshBalance}
                    refreshing={refreshingBalance}
                    trades={trades}
                    exchangeBalances={exchangeBalances}
                    exchangeBalancesLoading={exchangeBalancesLoading}
                />
            </div>

            {/* Main Chart - Performance History */}
            <div className="glass rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                    <TrendingUp size={20} className="text-primary" />
                    Cumulative Performance
                </h3>
                <div className="w-full h-[400px]">
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

            {/* Analytics Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Win Rate Over Time */}
                <div className="glass rounded-2xl p-6">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <BarChart2 size={20} className="text-primary" />
                        Win Rate Progress
                    </h3>
                    <div className="w-full h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={winRateData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="name" stroke="#ffffff40" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#ffffff40" tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                                    formatter={(value) => `${value.toFixed(1)}%`}
                                />
                                <Line type="monotone" dataKey="winRate" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Symbol Performance */}
                <div className="glass rounded-2xl p-6">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <PieChartIcon size={20} className="text-primary" />
                        Symbol Performance
                    </h3>
                    <div className="w-full h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={symbolPerformance}
                                    dataKey="pnl"
                                    nameKey="symbol"
                                    cx="50%"
                                    cy="50%"
                                    outerRadius={80}
                                    label={(entry) => entry.symbol}
                                >
                                    {symbolPerformance.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                                    formatter={(value) => `$${value.toFixed(2)}`}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Daily PnL */}
                <div className="glass rounded-2xl p-6">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <BarChart2 size={20} className="text-primary" />
                        Daily PnL
                    </h3>
                    <div className="w-full h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={dailyPnlData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="date" stroke="#ffffff40" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#ffffff40" tick={{ fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                                    formatter={(value) => `$${value.toFixed(2)}`}
                                />
                                <Bar dataKey="pnl" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Trading Goals Widget */}
            <TradingGoalsWidget />

            {/* Trade History Section */}
            <div className="h-[500px] mt-8">
                <TradeHistory trades={trades} onRefresh={refreshTrades} />
            </div>
        </div>
    );
}
