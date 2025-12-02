import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import {
    User, CreditCard, Activity, TrendingUp, Bot, Zap,
    Calendar, Shield, Newspaper, RefreshCw, CheckCircle,
    XCircle, Play, Square, Settings
} from 'lucide-react';
import SentimentWidget from '../components/SentimentWidget';
import BotInstancesTable from '../components/BotInstancesTable';
import Disclaimer from '../components/Disclaimer';
import PlanGate from '../components/PlanGate';
import { formatPlanName, formatStrategyName, formatLabel } from '../lib/utils';

const InfoCard = ({ title, value, icon: Icon, subtext, trend }) => (
    <div className="glass p-6 rounded-2xl relative overflow-hidden group hover:border-primary/20 transition-all">
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

const NewsItem = ({ title, summary, source, time, url }) => (
    <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="block p-4 glass rounded-xl hover:bg-white/5 transition-all group border border-transparent hover:border-primary/20"
    >
        <div className="flex justify-between items-start mb-2">
            <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors flex-1">
                {title}
            </h4>
            <span className="text-xs text-muted-foreground ml-2">{time}</span>
        </div>
        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{summary}</p>
        <span className="text-xs text-primary/60">{source}</span>
    </a>
);

export default function Main() {
    const [user, setUser] = useState(null);
    const [subscription, setSubscription] = useState(null);
    const [botStatus, setBotStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try {
            const [userRes, subRes, statusRes] = await Promise.all([
                api.get('/auth/me'),
                api.get('/billing/status'),
                api.get('/status')
            ]);

            setUser(userRes.data);
            setSubscription(subRes.data);
            setBotStatus(statusRes.data);
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchData();
    };

    const handleStartStop = async () => {
        try {
            if (botStatus?.is_running) {
                await api.post('/stop');
            } else {
                await api.post('/start');
            }
            // Refresh status immediately
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            console.error('Error toggling bot:', err);
        }
    };

    // Count bot instances
    const botCount = React.useMemo(() => {
        if (!botStatus?.instances) return 0;
        if (typeof botStatus.instances === 'object') {
            return Object.keys(botStatus.instances).length;
        }
        return botStatus.is_running ? 1 : 0;
    }, [botStatus]);

    // Mock news data (you can replace with real API later)
    const newsItems = [
        {
            title: "Bitcoin Hits New All-Time High",
            summary: "BTC surpasses previous records as institutional adoption grows...",
            source: "CryptoNews",
            time: "2h ago",
            url: "https://cryptonews.com"
        },
        {
            title: "Ethereum 2.0 Upgrade Complete",
            summary: "Major network upgrade brings improved scalability and security...",
            source: "CoinDesk",
            time: "5h ago",
            url: "https://coindesk.com"
        },
        {
            title: "New Trading Regulations Announced",
            summary: "SEC releases new guidelines for cryptocurrency exchanges...",
            source: "Bloomberg Crypto",
            time: "1d ago",
            url: "https://bloomberg.com"
        }
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-muted-foreground animate-pulse">Loading your profile...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Welcome back, {user?.nickname || user?.email?.split('@')[0] || 'Trader'}!
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Your trading overview and account information.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="p-2 hover:bg-white/10 rounded-lg transition-all"
                        title="Refresh data"
                    >
                        <RefreshCw size={20} className={`text-muted-foreground ${refreshing ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                        onClick={handleStartStop}
                        className={`
                            flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all duration-300 shadow-lg
                            ${botStatus?.is_running
                                ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20 shadow-red-500/10'
                                : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-primary/25 hover:shadow-primary/40'
                            }
                        `}
                    >
                        {botStatus?.is_running ? <><Square size={18} fill="currentColor" /> Stop Bot</> : <><Play size={18} fill="currentColor" /> Start Bot</>}
                    </button>
                </div>

                {/* Disclaimer */}
                <Disclaimer compact />
            </div>

            {/* Subscription & Bot Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                <InfoCard
                    title="Subscription Plan"
                    value={formatPlanName(subscription?.plan) || 'Free'}
                    icon={CreditCard}
                    subtext={subscription?.status === 'active' ? '✓ Active' : subscription?.status === 'expired' ? '✗ Expired' : 'No subscription'}
                    trend={subscription?.status === 'active' ? 'up' : 'down'}
                />
                <InfoCard
                    title="Bot Status"
                    value={botStatus?.is_running ? 'Running' : 'Stopped'}
                    icon={Bot}
                    subtext={`${botCount} instance(s)`}
                    trend={botStatus?.is_running ? 'up' : 'down'}
                />
                <InfoCard
                    title="Active Positions"
                    value={botStatus?.active_trades || 0}
                    icon={Activity}
                    subtext="Currently open"
                />
            </div>

            {/* Subscription Details Card */}
            <div className="glass p-6 rounded-2xl">
                <div className="flex items-center gap-2 mb-4">
                    <Shield size={20} className="text-primary" />
                    <h2 className="text-xl font-bold">Subscription Details</h2>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Current Plan</p>
                        <p className="text-lg font-semibold text-foreground">
                            {formatPlanName(subscription?.plan) || 'Free Plan'}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Status</p>
                        <div className="flex items-center gap-2">
                            {subscription?.status === 'active' ? (
                                <>
                                    <CheckCircle size={16} className="text-green-400" />
                                    <p className="text-lg font-semibold text-green-400">Active</p>
                                </>
                            ) : (
                                <>
                                    <XCircle size={16} className="text-red-400" />
                                    <p className="text-lg font-semibold text-red-400">
                                        {subscription?.status?.toUpperCase() || 'Inactive'}
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                    {subscription?.expires_at && (
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Expires</p>
                            <div className="flex items-center gap-2">
                                <Calendar size={16} className="text-primary" />
                                <p className="text-lg font-semibold text-foreground">
                                    {new Date(subscription.expires_at).toLocaleDateString()}
                                </p>
                            </div>
                        </div>
                    )}
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Actions</p>
                        <a
                            href="/pricing"
                            className="text-primary hover:text-primary/80 font-medium inline-flex items-center gap-1"
                        >
                            Upgrade Plan <TrendingUp size={14} />
                        </a>
                    </div>
                </div>
            </div>

            {/* Active Strategy Card */}
            <div className="glass p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Zap size={20} className="text-primary" />
                        <h2 className="text-xl font-bold">Active Strategy</h2>
                    </div>
                    <a
                        href="/strategies"
                        className="text-sm text-primary hover:text-primary/80 inline-flex items-center gap-1"
                    >
                        <Settings size={14} /> Configure
                    </a>
                </div>
                <div className="grid md:grid-cols-3 gap-4">
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Strategy Type</p>
                        <p className="text-lg font-semibold text-foreground">
                            {formatStrategyName(botStatus?.config?.strategy) || 'None'}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Trading Mode</p>
                        <div className="flex items-center gap-2">
                            {botStatus?.config?.dry_run ? (
                                <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded text-xs font-medium">
                                    ⚠️ Practice Mode
                                </span>
                            ) : (
                                <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs font-medium">
                                    🚀 Live Trading
                                </span>
                            )}
                        </div>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Symbol</p>
                        <p className="text-lg font-semibold text-foreground">
                            {botStatus?.config?.symbol || 'N/A'}
                        </p>
                    </div>
                </div>
                {botStatus?.config?.parameters && Object.keys(botStatus.config.parameters).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/5">
                        <p className="text-sm text-muted-foreground mb-2">Strategy Parameters</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {Object.entries(botStatus.config.parameters).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                    <span className="text-muted-foreground capitalize">{formatLabel(key)}: </span>
                                    <span className="text-foreground font-medium">{value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* AI Sentiment */}
            <div>
                <PlanGate feature="AI Sentiment Analysis">
                    <SentimentWidget />
                </PlanGate>
            </div>

            {/* News Feed */}
            <div className="glass p-6 rounded-2xl">
                <div className="flex items-center gap-2 mb-4">
                    <Newspaper size={20} className="text-primary" />
                    <h2 className="text-xl font-bold">Market News</h2>
                </div>
                <div className="space-y-3">
                    {newsItems.map((item, idx) => (
                        <NewsItem key={idx} {...item} />
                    ))}
                </div>
                <div className="mt-4 text-center">
                    <a
                        href="https://cryptonews.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:text-primary/80 inline-flex items-center gap-1"
                    >
                        View More News <TrendingUp size={14} />
                    </a>
                </div>
            </div>

            {/* Bot Instances Table */}
            <BotInstancesTable
                instances={botStatus?.instances || botStatus || {}}
                onStart={() => handleStartStop()}
                onStop={() => handleStartStop()}
                onStopAll={() => handleStartStop()}
                loading={loading}
            />
        </div>
    );
}
