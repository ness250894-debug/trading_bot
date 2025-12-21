import { useState, useEffect, useMemo, useCallback } from 'react';
import api from '../lib/api';
import { useToast } from '../components/ToastContext';
import { useWebSocket } from './useWebSocket';

export const useDashboardData = () => {
    const toast = useToast();
    // User & Global State
    const [user, setUser] = useState(null);
    const [subscription, setSubscription] = useState(null);
    const [isPracticeMode, setIsPracticeMode] = useState(true);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [pollingInterval, setPollingInterval] = useState(30000); // Default 30s (backup)

    // WebSocket Handler
    const handleWebSocketMessage = useCallback((message) => {
        // console.log('WS Msg:', message);
        if (message.type === 'status_update') {
            setBotStatus(message.data);

            // Allow PnL to update live?
            // Bot status includes PnL, so this updates it.
        }
        else if (message.type === 'signal') {
            // toast.info(`Signal: ${message.data.signal} @ $${message.data.price}`);
        }
        else if (message.type === 'trade') {
            toast.success(`Trade Executed: ${message.data.side} ${message.data.symbol}`);
            // Trigger balance refresh ?
            // fetchExchangeBalances(); 
        }
        else if (message.type === 'trade_closed') {
            toast.success(`Trade Closed. PnL: $${message.data.pnl?.toFixed(2)}`);
        }
    }, [toast]);

    // Connect WS
    const { isConnected } = useWebSocket(user?.id, handleWebSocketMessage);


    // Bot State
    const [botStatus, setBotStatus] = useState(null);
    const [botConfigs, setBotConfigs] = useState([]);
    const [startingBots, setStartingBots] = useState(new Set());

    // Exchange & News
    const [exchangeBalances, setExchangeBalances] = useState(null);
    const [exchangeBalancesLoading, setExchangeBalancesLoading] = useState(true);
    const [refreshingBalance, setRefreshingBalance] = useState(false);

    const [newsItems, setNewsItems] = useState([]);
    const [newsLoading, setNewsLoading] = useState(true);

    // Initial Load - Practice Mode
    useEffect(() => {
        const savedMode = localStorage.getItem('globalPracticeMode');
        setIsPracticeMode(savedMode === null ? true : savedMode === 'true');
    }, []);

    // Initial Load - Bot Configs
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

    // Main Data Fetcher
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

            if (subRes.data?.plan === 'free') {
                setIsPracticeMode(true);
                localStorage.setItem('globalPracticeMode', 'true');
            }

        } catch (err) {
            // Error handled by loading state via setRefreshing(false) eventually
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    // Smart Polling
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) setPollingInterval(60000);
            else setPollingInterval(30000);
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);

        fetchData();
        const interval = setInterval(fetchData, pollingInterval);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            clearInterval(interval);
        };
    }, [pollingInterval]);

    // Exchange Balances Fetcher
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

    useEffect(() => {
        fetchExchangeBalances();
        const balanceInterval = setInterval(fetchExchangeBalances, 60000);
        return () => clearInterval(balanceInterval);
    }, []);

    // News Fetcher
    const fetchNews = async () => {
        setNewsLoading(true); // Ensure loading state shows on manual refresh
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
            // silent fail
        } finally {
            setNewsLoading(false);
        }
    };

    useEffect(() => {
        fetchNews();
        const newsInterval = setInterval(fetchNews, 300000);
        return () => clearInterval(newsInterval);
    }, [botStatus?.config?.symbol]);

    // Handlers
    const handlePracticeModeToggle = (newValue) => {
        setIsPracticeMode(newValue);
        localStorage.setItem('globalPracticeMode', String(newValue));
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await Promise.all([fetchData(), fetchExchangeBalances(), fetchNews()]);
        setRefreshing(false);
    };

    const handleRefreshBalance = async () => {
        if (isPracticeMode) {
            if (refreshingBalance) return;
            setRefreshingBalance(true);
            try {
                // Call real API
                await api.post('/balance/reset');
                toast.success('Practice balance has been reset to $1,000!');
                const statusRes = await api.get('/status');
                setBotStatus(statusRes.data);
            } catch (err) {
                toast.error('Failed to reset practice balance.');
            } finally {
                setRefreshingBalance(false);
            }
        } else {
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

    // Bot Actions (could be extracted further, but keeping here for now)
    const handleStartStop = async () => {
        try {
            if (botStatus?.is_running) {
                await api.post('/stop');
            } else {
                await api.post('/start');
            }
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            // error
        }
    };

    const isBotRunning = (symbol) => {
        if (!botStatus?.instances) return false;
        if (typeof botStatus.instances === 'object') {
            return botStatus.instances[symbol]?.is_running || false;
        }
        return false;
    };

    const handleRemoveBot = async (symbol, configId) => {
        try {
            if (configId) {
                await api.delete(`/bot-configs/${configId}`);
                setBotConfigs(prev => prev.filter(c => c.id !== configId));
            } else {
                if (isBotRunning(symbol)) {
                    await api.post('/stop', null, { params: { symbol } });
                }
            }
            const res = await api.get('/status');
            setBotStatus(res.data);
            toast.success('Bot removed');
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to remove bot');
        }
    };

    const handleBulkStart = async (bots) => {
        try {
            // bots: array of {symbol, config_id}
            await api.post('/bulk/start', { bots });
            toast.success(`Started ${bots.length} bots`);
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            toast.error('Failed to start some bots');
        }
    };

    const handleBulkStop = async (bots) => {
        try {
            await api.post('/bulk/stop', { bots });
            toast.success(`Stopped ${bots.length} bots`);
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            toast.error('Failed to stop some bots');
        }
    };

    const handleClosePosition = async (configId) => {
        try {
            await api.post(`/bot-configs/${configId}/close-position`);
            toast.success('Position closed');
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            console.error(err);
            toast.error(err.response?.data?.detail || 'Failed to close position');
        }
    };

    const handleBulkRemove = async (configIds) => {
        try {
            await api.post('/bulk/delete', { config_ids: configIds });
            setBotConfigs(prev => prev.filter(c => !configIds.includes(c.id)));
            const res = await api.get('/status');
            setBotStatus(res.data);
            toast.success(`Removed ${configIds.length} bot configurations`);
        } catch (err) {
            toast.error('Failed to remove some bot configurations');
        }
    };

    const handleQuickScalp = async () => {
        try {
            await api.post('/quick-scalping');
            toast.success('Quick Scalp Bot Created! 🚀');
            const configRes = await api.get('/bot-configs');
            setBotConfigs(configRes.data.configs || []);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to create Quick Scalp bot');
        }
    };

    const handleStartBot = async (symbol, configId) => {
        try {
            const key = configId ? `${symbol}-${configId}` : symbol;
            setStartingBots(prev => new Set(prev).add(key));

            if (configId) {
                await api.post('/start', null, { params: { config_id: configId } });
            } else {
                const config = botConfigs.find(c => c.symbol === symbol);
                if (config) await api.post('/config', config);
                await api.post('/start', null, { params: { symbol } });
            }
            toast.success(`Started bot for ${symbol}`);
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
            const res = await api.get('/status');
            setBotStatus(res.data);
        } catch (err) {
            toast.error(err.response?.data?.detail || `Failed to stop bot for ${symbol}`);
        }
    };

    return {
        user,
        subscription,
        isPracticeMode,
        loading,
        refreshing,
        botStatus,
        botConfigs,
        startingBots,
        exchangeBalances,
        exchangeBalancesLoading,
        refreshingBalance,
        newsItems,
        newsLoading,
        handlePracticeModeToggle,
        handleRefresh,
        handleRefreshBalance,
        handleStartStop,
        isBotRunning,
        handleRemoveBot,
        handleBulkRemove,
        handleBulkStart,
        handleBulkStop,
        handleQuickScalp,
        handleStartBot,
        handleStopBot,
        handleClosePosition,
        fetchNews
    };
};
