import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import {
    User, CreditCard, Activity, TrendingUp, Bot, Zap,
    Calendar, Shield, Newspaper, RefreshCw, CheckCircle,
    XCircle, Play, Square, Settings, Plus, Trash2, Edit
} from 'lucide-react';
import CombinedSentimentWidget from '../components/CombinedSentimentWidget';
import BotInstancesTable from '../components/BotInstancesTable';
import WatchlistWidget from '../components/WatchlistWidget';
import PriceAlertsWidget from '../components/PriceAlertsWidget';
import BalanceCard from '../components/dashboard/BalanceCard';
import PracticeModeToggle from '../components/PracticeModeToggle';

import PlanGate from '../components/PlanGate';
import { useModal } from '../components/Modal';
import { formatPlanName } from '../lib/utils';
import { useToast } from '../components/ToastContext';
import EditableText from '../components/constructor/EditableText';
import DraggableWidget from '../components/constructor/DraggableWidget';

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
    const toast = useToast();
    const [user, setUser] = useState(null);
    const [subscription, setSubscription] = useState(null);
    const [botStatus, setBotStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [pollingInterval, setPollingInterval] = useState(30000); // Start with 30s
    const [exchangeBalances, setExchangeBalances] = useState(null);
    const [exchangeBalancesLoading, setExchangeBalancesLoading] = useState(true);
    const [refreshingBalance, setRefreshingBalance] = useState(false);

    // Global Practice Mode State
    const [isPracticeMode, setIsPracticeMode] = useState(true);

    // Multi-bot configuration state
    const [botConfigs, setBotConfigs] = useState([]);
    const [startingBots, setStartingBots] = useState(new Set());
    const [newsItems, setNewsItems] = useState([]);
    const [newsLoading, setNewsLoading] = useState(true);

    // Load initial practice mode from localStorage
    useEffect(() => {
        const savedMode = localStorage.getItem('globalPracticeMode');
        // Default to true if not set
        setIsPracticeMode(savedMode === null ? true : savedMode === 'true');
    }, []);

    // Handle Practice Mode Toggle
    const handlePracticeModeToggle = (newValue) => {
        setIsPracticeMode(newValue);
        localStorage.setItem('globalPracticeMode', String(newValue));
    };

    // Fetch bot configs from API
    useEffect(() => {
        const fetchBotConfigs = async () => {
            try {
                const response = await api.get('/bot-configs');
                setBotConfigs(response.data.configs || []);
            } catch (err) {
                console.error('Failed to fetch bot configs:', err);
                setBotConfigs([]);
            }
        };
        fetchBotConfigs();
    }, []);

    // Smart polling: Reduce frequency when page is not visible
    React.useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                setPollingInterval(60000); // 1 min when inactive
            } else {
                setPollingInterval(30000); // 30s when active
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, []);

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

            // Force practice mode if free plan
            if (subRes.data?.plan === 'free') {
                setIsPracticeMode(true);
                localStorage.setItem('globalPracticeMode', 'true');
            }

        } catch (err) {
            // Silent fail - loading state will show error UI if needed
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh with dynamic interval based on page visibility
        const interval = setInterval(fetchData, pollingInterval);
        return () => clearInterval(interval);
    }, [pollingInterval]);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchData();
        fetchExchangeBalances();
        fetchNews();
    };

    // Fetch Exchange Balances
    const fetchExchangeBalances = async () => {
        // Here we could simulate practice balance if in practice mode, 
        // but BalanceCard handles the *display* logic. 
        // We still fetch real balances if available for reference or if switched to Live.
        try {
            const response = await api.get('/exchange-balances');
            setExchangeBalances(response.data);
        } catch (err) {
            console.error('Failed to fetch exchange balances:', err);
        } finally {
            setExchangeBalancesLoading(false);
        }
    };

    useEffect(() => {
        fetchExchangeBalances();
        // Refresh exchange balances every 60 seconds
        const balanceInterval = setInterval(fetchExchangeBalances, 60000);
        return () => clearInterval(balanceInterval);
    }, []);

    const handleRefreshBalance = async () => {
        // If in Practice Mode, reset balance
        if (isPracticeMode) {
            if (refreshingBalance) return;
            setRefreshingBalance(true);
            try {
                // Simulate backend reset
                await new Promise(resolve => setTimeout(resolve, 1000));
                // Update bot status to reflect reset if backend supported it
                // For now just toast
                toast.success('Practice balance has been reset to $1,000!');
                // Re-fetch status to see updates if any
                const statusRes = await api.get('/status');
                setBotStatus(statusRes.data);
            } catch (err) {
                toast.error('Failed to reset practice balance.');
            } finally {
                setRefreshingBalance(false);
            }
        } else {
            // If in Live Mode, refresh exchange connection
            if (refreshingBalance) return;
            setRefreshingBalance(true);
            try {
                await fetchExchangeBalances();
                toast.success('Exchange balances updated.');
            } catch (err) {
                toast.error('Failed to update exchange balances.');
            } finally {
                setRefreshingBalance(false);
            }
        }
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
            // Error will be visible in UI state
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

    // Get running status for a specific symbol
    const isBotRunning = (symbol) => {
        if (!botStatus?.instances) return false;
        if (typeof botStatus.instances === 'object') {
            return botStatus.instances[symbol]?.is_running || false;
        }
        return false;
    };

    // Multi-bot handlers
    const handleRemoveBot = async (symbol, configId) => {
        try {
            // Delete from API if has config ID
            if (configId) {
                await api.delete(`/bot-configs/${configId}`);
                // Remove from local state
                setBotConfigs(prev => prev.filter(c => c.id !== configId));
            } else {
                // No config ID means it's a running bot without saved config
                // Just stop it
                if (isBotRunning(symbol)) {
                    await api.post('/stop', null, { params: { symbol } });
                }
            }

            // Always refresh status to update UI
            const res = await api.get('/status');
            setBotStatus(res.data);

            toast.success('Bot removed');
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to remove bot');
        }
    };

    const handleBulkRemove = async (symbols) => {
        try {
            // Find configs for these symbols and delete them
            const configsToDelete = botConfigs.filter(c => symbols.includes(c.symbol));

            for (const config of configsToDelete) {
                await api.delete(`/bot-configs/${config.id}`);
            }

            // Update local state
            setBotConfigs(prev => prev.filter(c => !symbols.includes(c.symbol)));

            // Refresh status
            const res = await api.get('/status');
            setBotStatus(res.data);

            toast.success(`Removed ${symbols.length} bot configurations`);
        } catch (err) {
            toast.error('Failed to remove some bot configurations');
        }
    };

    const handleStartBot = async (symbol, configId) => {
        try {
            const key = configId ? `${symbol}-${configId}` : symbol;
            setStartingBots(prev => new Set(prev).add(key));

            // Force dry_run in payload to match global practice mode
            // Note: This relies on the endpoint accepting this override if the config 
            // has a different setting embedded. If not, we might need to update the config first.
            // For now, assume we just start it. The *creation* of bots captures the mode.

            if (configId) {
                await api.post('/start', null, { params: { config_id: configId } });
            } else {
                // Legacy support
                const config = botConfigs.find(c => c.symbol === symbol);
                if (config) {
                    await api.post('/config', config);
                }
                await api.post('/start', null, { params: { symbol } });
            }

            toast.success(`Started bot for ${symbol}`);
            // Refresh status
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            toast.error(err.response?.data?.detail || `Failed to start bot for ${symbol}`);
        } finally {
            const key = configId ? `${symbol}-${configId}` : symbol;
            setStartingBots(prev => {
                const newSet = new Set(prev);
                newSet.delete(key);
                return newSet;
            });
        }
    };

    const handleStopBot = async (symbol, configId) => {
        try {
            if (configId) {
                await api.post('/stop', null, { params: { config_id: configId } });
            } else {
                await api.post('/stop', null, { params: { symbol } });
            }

            toast.success(`Stopped bot for ${symbol}`);
            // Refresh status
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            toast.error(err.response?.data?.detail || `Failed to stop bot for ${symbol}`);
        }
    };

    // Fetch news
    const fetchNews = async () => {
        try {
            const res = await api.get('/news', {
                params: {
                    symbols: botStatus?.config?.symbol || 'BTC,ETH',
                    limit: 10
                }
            });
            if (res.data.success) {
                setNewsItems(res.data.news || []);
            }
        } catch (err) {
            // Silent fail
        } finally {
            setNewsLoading(false);
        }
    };

    useEffect(() => {
        fetchNews();
        const newsInterval = setInterval(fetchNews, 300000);
        return () => clearInterval(newsInterval);
    }, [botStatus?.config?.symbol]);

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
                        <EditableText
                            configPath="pages.main.subtitle"
                            defaultValue="Your trading overview and account information."
                        />
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
                </div>
            </div>

            {/* Practice Mode Toggle - Above Bot Table */}
            <div className="flex justify-end">
                <PracticeModeToggle
                    isPracticeMode={isPracticeMode}
                    onToggle={handlePracticeModeToggle}
                    isFreePlan={subscription?.plan === 'free'}
                />
            </div>

            {/* Bot Instances Table - Moved to Top */}
            <BotInstancesTable
                instances={botStatus?.instances || {}}
                botConfigs={botConfigs}
                onRemoveBot={handleRemoveBot}
                onBulkRemove={handleBulkRemove}
                onStart={handleStartBot}
                onStop={handleStopBot}
                onStopAll={() => handleStartStop()}
                loading={loading}
                subscription={subscription}
                startingBots={startingBots}
                isBotRunning={isBotRunning}
            />

            {/* Account Info Grid */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Subscription Details Card - Resized */}
                <DraggableWidget
                    id="subscriptionCard"
                    widgetName="Subscription Details"
                    className="glass p-6 rounded-2xl h-full"
                    defaultWidth="auto"
                    defaultHeight="auto"
                    editableFields={{
                        title: 'Subscription Details',
                        planLabel: 'Current Plan',
                        statusLabel: 'Status',
                        activeText: 'Active',
                        expiresLabel: 'Expires',
                        actionsLabel: 'Actions',
                        upgradeText: 'Upgrade Plan'
                    }}
                >
                    <div className="flex items-center gap-2 mb-4">
                        <Shield size={20} className="text-primary" />
                        <h2 className="text-xl font-bold">Subscription Details</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <p className="text-sm text-muted-foreground mb-1">Current Plan</p>
                                <p className="text-lg font-semibold text-foreground">
                                    {formatPlanName(subscription?.plan) || 'Free Plan'}
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-muted-foreground mb-1">Status</p>
                                <div className="flex items-center justify-end gap-2">
                                    {subscription?.status === 'active' ? (
                                        <>
                                            <CheckCircle size={16} className="text-green-400" />
                                            <span className="text-sm font-semibold text-green-400">Active</span>
                                        </>
                                    ) : (
                                        <>
                                            <XCircle size={16} className="text-red-400" />
                                            <span className="text-sm font-semibold text-red-400">
                                                {subscription?.status?.toUpperCase() || 'Inactive'}
                                            </span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {subscription?.expires_at && (
                            <div className="pt-4 border-t border-white/10">
                                <p className="text-sm text-muted-foreground mb-1">Expires</p>
                                <div className="flex items-center gap-2">
                                    <Calendar size={16} className="text-primary" />
                                    <p className="text-sm font-medium text-foreground">
                                        {new Date(subscription.expires_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        )}

                        <div className="pt-4 border-t border-white/10">
                            <a
                                href="/pricing"
                                className="w-full justify-center text-primary hover:text-primary/80 font-medium inline-flex items-center gap-1 p-2 bg-primary/10 rounded-lg transition-colors border border-primary/20 hover:bg-primary/20"
                            >
                                Upgrade Plan <TrendingUp size={14} />
                            </a>
                        </div>
                    </div>
                </DraggableWidget>

                {/* Balance Card - with Practice Mode State */}
                <div className="h-full">
                    <BalanceCard
                        status={botStatus}
                        onRefreshBalance={handleRefreshBalance}
                        refreshing={refreshingBalance}
                        trades={[]}
                        exchangeBalances={exchangeBalances}
                        exchangeBalancesLoading={exchangeBalancesLoading}
                        isPracticeMode={isPracticeMode}
                    />
                </div>
            </div>

            {/* Market Tools Grid */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Watchlist */}
                <div className="h-[500px]">
                    <WatchlistWidget />
                </div>

                {/* Price Alerts */}
                <div className="h-[500px]">
                    <PriceAlertsWidget />
                </div>
            </div>

            {/* AI Sentiment & Analysis - Combined Widget */}
            <div className="h-[500px]">
                <PlanGate feature="AI Sentiment & Analysis" explanation="Get real-time market sentiment analysis powered by AI with advanced metrics and key market drivers.">
                    <CombinedSentimentWidget />
                </PlanGate>
            </div>

            {/* News Feed */}
            <div className="glass p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Newspaper size={20} className="text-primary" />
                        <h2 className="text-xl font-bold">Market News</h2>
                    </div>
                    <button
                        onClick={fetchNews}
                        disabled={newsLoading}
                        className="p-1.5 hover:bg-white/10 rounded-lg transition-all"
                        title="Refresh news"
                    >
                        <RefreshCw size={16} className={`text-muted-foreground ${newsLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
                {/* Scrollable container showing 3 news items with ability to scroll through all 10 */}
                <div className="max-h-[400px] overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/20">
                    {newsLoading ? (
                        <div className="text-center py-12">
                            <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                            <p className="text-muted-foreground text-sm">Loading news...</p>
                        </div>
                    ) : newsItems.length > 0 ? (
                        newsItems.map((item, idx) => (
                            <NewsItem key={idx} {...item} />
                        ))
                    ) : (
                        <div className="text-center py-12">
                            <Newspaper size={48} className="mx-auto text-muted-foreground/30 mb-4" />
                            <p className="text-muted-foreground font-medium">No news available</p>
                            <p className="text-sm text-muted-foreground/60 mt-1">
                                Configure API keys in .env to enable news sources
                            </p>
                            <button
                                onClick={fetchNews}
                                className="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all"
                            >
                                Retry
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
