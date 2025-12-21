import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Square, Plus, RefreshCw, Trash2, Settings, Zap } from 'lucide-react';
import { useModal } from './Modal';
import BotRow from './BotRow';
import BotCard from './BotCard';

/**
 * BotInstancesTable - Displays all bot instances with checkboxes and multi-bot controls
 */
export default function BotInstancesTable({
    instances,
    botConfigs,
    onRemoveBot,
    onBulkRemove,
    onStart,
    onStop,
    onBulkStart,
    onBulkStop,
    loading,
    subscription,
    startingBots,
    onQuickScalp
}) {
    const navigate = useNavigate();
    const modal = useModal();
    const [selectedBots, setSelectedBots] = useState(new Set());

    // Check if user is on free plan
    const isFreePlan = !subscription || subscription.plan === 'free' || !subscription.plan;

    // Handler for Add Bot button - shows upgrade modal for free plan users with existing bots
    const handleAddBot = () => {
        if (isFreePlan && botConfigs && botConfigs.length >= 1) {
            modal.show({
                title: '🚀 Upgrade Your Plan',
                type: 'info',
                content: (
                    <div className="space-y-4">
                        <p className="text-muted-foreground">
                            Your free plan is limited to <span className="text-foreground font-semibold">1 bot</span>.
                        </p>
                        <p className="text-muted-foreground">
                            Upgrade to unlock:
                        </p>
                        <ul className="space-y-2 text-sm">
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                <span className="text-foreground">Multiple trading bots</span>
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                <span className="text-foreground">All trading strategies</span>
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                <span className="text-foreground">Real money trading</span>
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                <span className="text-foreground">Priority support</span>
                            </li>
                        </ul>
                        <button
                            onClick={() => {
                                modal.hide();
                                navigate('/pricing');
                            }}
                            className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-xl font-semibold transition-all shadow-lg shadow-purple-500/25"
                        >
                            View Upgrade Options
                        </button>
                    </div>
                )
            });
        } else {
            navigate('/strategies');
        }
    };

    // Handle multi-instance response format - combine with botConfigs
    const allBots = React.useMemo(() => {
        const botMap = new Map();

        // 1. Add all configured bots first
        botConfigs?.forEach(config => {
            const id = config.id; // config_id
            botMap.set(id, {
                ...config,
                config_id: id,
                is_running: false, // Default, will be overridden if running
                source: 'config'
            });
        });

        // 2. Merge running instances
        if (instances && typeof instances === 'object' && !Array.isArray(instances)) {
            // Check if it's a single instance response (legacy)
            if ('is_running' in instances) {
                const status = instances;
                const configId = status.config_id;
                const symbol = status.symbol || 'BTC/USDT';

                // If we have a configId, merge with existing or add new
                if (configId) {
                    const existing = botMap.get(configId) || {};
                    botMap.set(configId, { ...existing, ...status, config_id: configId, source: 'running' });
                } else {
                    // Legacy: try to match by symbol or add as "legacy-{symbol}"
                    // This is tricky if we have multiple configs for same symbol.
                    // But legacy usually implies single bot.
                    // Let's just add it with a special key if not found
                    const foundConfig = botConfigs?.find(c => c.symbol === symbol);
                    if (foundConfig) {
                        botMap.set(foundConfig.id, { ...foundConfig, ...status, config_id: foundConfig.id });
                    } else {
                        botMap.set(`legacy-${symbol}`, { ...status, symbol, source: 'running_legacy' });
                    }
                }
            } else {
                // Dict of instances {config_id: status}
                Object.entries(instances).forEach(([key, status]) => {
                    const configId = status.config_id || parseInt(key); // key might be string "1"

                    if (configId) {
                        const existing = botMap.get(configId) || {};
                        botMap.set(configId, { ...existing, ...status, config_id: configId, source: 'running' });
                    } else {
                        // Fallback for purely symbol-keyed legacy maps (if any)
                        const symbol = status.symbol || key;
                        botMap.set(`legacy-${symbol}`, { ...status, symbol, source: 'running_legacy' });
                    }
                });
            }
        }

        return Array.from(botMap.values());
    }, [instances, botConfigs]);

    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedBots(new Set(allBots.map(b => b.config_id || b.symbol)));
        } else {
            setSelectedBots(new Set());
        }
    };

    const handleSelectBot = (id, checked) => {
        const newSelected = new Set(selectedBots);
        if (checked) {
            newSelected.add(id);
        } else {
            newSelected.delete(id);
        }
        setSelectedBots(newSelected);
    };

    const handleStartSelected = async () => {
        const botsToStart = [];
        for (const id of selectedBots) {
            const bot = allBots.find(b => (b.config_id || b.symbol) === id);
            if (bot) {
                botsToStart.push({
                    symbol: bot.symbol,
                    config_id: bot.config_id
                });
            }
        }
        if (botsToStart.length > 0) {
            await onBulkStart(botsToStart);
        }
    };

    const handleStopSelected = async () => {
        const botsToStop = [];
        for (const id of selectedBots) {
            const bot = allBots.find(b => (b.config_id || b.symbol) === id);
            if (bot) {
                botsToStop.push({
                    symbol: bot.symbol,
                    config_id: bot.config_id
                });
            }
        }
        if (botsToStop.length > 0) {
            await onBulkStop(botsToStop);
        }
    };

    const handleBulkDelete = async () => {
        if (onBulkRemove) {
            const configIds = [];
            for (const id of selectedBots) {
                const bot = allBots.find(b => (b.config_id || b.symbol) === id);
                if (bot && bot.config_id) {
                    configIds.push(bot.config_id);
                }
            }

            if (configIds.length > 0) {
                await onBulkRemove(configIds);
                setSelectedBots(new Set());
            }
        }
    };

    const allSelected = allBots.length > 0 && selectedBots.size === allBots.length;
    const someSelected = selectedBots.size > 0;

    if (loading) {
        return (
            <div className="glass rounded-2xl p-8">
                <div className="flex items-center justify-center">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="glass rounded-2xl overflow-hidden shadow-lg shadow-purple-900/10 border border-purple-500/10">
            <div className="p-6 border-b border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gradient-to-r from-purple-900/20 to-transparent">
                <div>
                    <h3 className="text-lg font-semibold text-foreground">Active Bot Instances</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        {allBots.length} {allBots.length === 1 ? 'bot' : 'bots'} configured
                        {someSelected && ` • ${selectedBots.size} selected`}
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
                    <button
                        onClick={handleAddBot}
                        className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white rounded-xl transition-all font-medium whitespace-nowrap shadow-lg shadow-primary/20"
                    >
                        <Plus size={16} />
                        Add Bot
                    </button>
                    {!subscription || (subscription.plan && subscription.plan !== 'free') || (botConfigs && botConfigs.length === 0) ? (
                        <button
                            onClick={onQuickScalp}
                            className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white rounded-xl transition-all font-medium whitespace-nowrap shadow-lg shadow-orange-500/20"
                            title="Create Quick Scalping Bot"
                        >
                            <Zap size={16} />
                            Quick Scalp
                        </button>
                    ) : null}
                    {someSelected && (
                        <>
                            <button
                                onClick={handleStartSelected}
                                className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-500 hover:bg-green-500/20 rounded-lg transition-colors border border-green-500/20"
                                title="Start Selected"
                            >
                                <Play size={16} fill="currentColor" />
                            </button>
                            <button
                                onClick={handleStopSelected}
                                className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
                                title="Stop Selected"
                            >
                                <Square size={16} fill="currentColor" />
                            </button>
                            <button
                                onClick={handleBulkDelete}
                                className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
                                title="Delete Selected"
                            >
                                <Trash2 size={16} />
                            </button>
                        </>
                    )}
                </div>
            </div>

            {allBots.length === 0 ? (
                <div className="p-12 text-center">
                    <div className="flex justify-center mb-4">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center">
                            <Plus size={32} className="text-muted-foreground opacity-50" />
                        </div>
                    </div>
                    <p className="text-muted-foreground mb-4">No bot instances configured</p>
                    <button
                        onClick={() => navigate('/strategies')}
                        className="text-primary hover:underline font-medium"
                    >
                        Click "Add Bot" to create your first trading bot
                    </button>
                </div>
            ) : (
                <>
                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto max-h-[400px] overflow-y-auto relative scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                        <table className="w-full">
                            <thead className="bg-white/5 sticky top-0 backdrop-blur-md z-10 border-b border-white/5">
                                <tr>
                                    <th className="px-3 py-4 text-center w-8">
                                        <input
                                            type="checkbox"
                                            checked={allSelected}
                                            onChange={(e) => handleSelectAll(e.target.checked)}
                                            className="w-4 h-4 rounded border-white/20 bg-black/20 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer mx-auto"
                                        />
                                    </th>
                                    <th className="px-3 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Symbol</th>
                                    <th className="px-3 py-4 text-center text-xs font-medium text-muted-foreground uppercase tracking-wider">Mode</th>
                                    <th className="px-3 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Strategy</th>
                                    <th className="px-3 py-4 text-center text-xs font-medium text-muted-foreground uppercase tracking-wider">Timeframe</th>
                                    <th className="px-3 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Amount</th>
                                    <th className="px-3 py-4 text-center text-xs font-medium text-muted-foreground uppercase tracking-wider">Lev.</th>
                                    <th className="px-3 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Exchange</th>
                                    <th className="px-3 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">TP / SL</th>
                                    <th className="px-3 py-4 text-center text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                    <th className="px-3 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">PnL</th>
                                    <th className="px-3 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {allBots.map((bot) => (
                                    <BotRow
                                        key={bot.config_id || bot.symbol}
                                        bot={bot}
                                        isSelected={selectedBots.has(bot.config_id || bot.symbol)}
                                        isStarting={startingBots?.has(bot.symbol) || startingBots?.has(`${bot.symbol}-${bot.config_id}`)}
                                        onSelect={handleSelectBot}
                                        onStart={onStart}
                                        onStop={onStop}
                                        onRemove={onRemoveBot}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile Card View */}
                    <div className="md:hidden space-y-4 p-4">
                        <div className="flex items-center justify-between mb-2 px-1">
                            <label className="flex items-center gap-2 text-sm text-muted-foreground">
                                <input
                                    type="checkbox"
                                    checked={allSelected}
                                    onChange={(e) => handleSelectAll(e.target.checked)}
                                    className="w-4 h-4 rounded border-white/20 bg-black/20 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer"
                                />
                                Select All
                            </label>
                        </div>
                        {allBots.map((bot) => (
                            <BotCard
                                key={bot.config_id || bot.symbol}
                                bot={bot}
                                isSelected={selectedBots.has(bot.config_id || bot.symbol)}
                                isStarting={startingBots?.has(bot.symbol) || startingBots?.has(`${bot.symbol}-${bot.config_id}`)}
                                onSelect={handleSelectBot}
                                onStart={onStart}
                                onStop={onStop}
                                onRemove={onRemoveBot}
                            />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
