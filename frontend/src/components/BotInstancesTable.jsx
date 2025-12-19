import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Square, Plus, RefreshCw, Trash2, Settings } from 'lucide-react';
import { useModal } from './Modal';

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
    onStopAll,
    loading,
    subscription,
    startingBots,
    isBotRunning
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
        for (const id of selectedBots) {
            const bot = allBots.find(b => (b.config_id || b.symbol) === id);
            if (bot) {
                await onStart(bot.symbol, bot.config_id);
            }
        }
    };

    const handleStopSelected = async () => {
        for (const id of selectedBots) {
            const bot = allBots.find(b => (b.config_id || b.symbol) === id);
            if (bot) {
                await onStop(bot.symbol, bot.config_id);
            }
        }
    };

    const handleBulkDelete = async () => {
        if (onBulkRemove) {
            // We need to pass symbols for bulk remove? Or IDs?
            // The API expects IDs for configs.
            // But handleBulkRemove in Main.jsx currently expects symbols.
            // I should update Main.jsx handleBulkRemove to accept IDs too, or just loop here.

            // Actually, let's just use onRemoveBot for each selected item for now to be safe,
            // or update Main.jsx. 
            // Main.jsx handleBulkRemove: const configsToDelete = botConfigs.filter(c => symbols.includes(c.symbol));
            // It filters by symbol. This is bad for multiple bots.

            // Let's assume we can't easily bulk remove by ID with current Main.jsx without changing it.
            // But wait, I can just call onRemoveBot for each.
            for (const id of selectedBots) {
                const bot = allBots.find(b => (b.config_id || b.symbol) === id);
                if (bot) {
                    await onRemoveBot(bot.symbol, bot.config_id);
                }
            }
            setSelectedBots(new Set());
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
        <div className="glass rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
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
                        className="flex-1 md:flex-none justify-center flex items-center gap-2 px-4 py-2 bg-primary text-white hover:bg-primary/90 rounded-lg transition-all font-medium whitespace-nowrap"
                    >
                        <Plus size={16} />
                        Add Bot
                    </button>
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
                    <p className="text-muted-foreground mb-4">No bot instances configured</p>
                    <button
                        onClick={() => navigate('/strategies')}
                        className="text-primary hover:underline"
                    >
                        Click "Add Bot" to create your first trading bot
                    </button>
                </div>
            ) : (
                <div className="overflow-x-auto max-h-[350px] overflow-y-auto relative scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                    <table className="w-full">
                        <thead className="bg-white/5">
                            <tr>
                                <th className="px-6 py-4 text-left">
                                    <input
                                        type="checkbox"
                                        checked={allSelected}
                                        onChange={(e) => handleSelectAll(e.target.checked)}
                                        className="w-4 h-4 rounded border-white/20 bg-black/20 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer"
                                    />
                                </th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Symbol</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Mode</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Strategy</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Timeframe</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Amount</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Current PnL</th>
                                <th className="px-6 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {allBots.map((bot) => {
                                const isRunning = bot.is_running || false;
                                const uniqueId = bot.config_id || bot.symbol; // Use config_id if available
                                const isStarting = startingBots?.has(bot.symbol) || startingBots?.has(`${bot.symbol}-${bot.config_id}`);
                                const isSelected = selectedBots.has(uniqueId);

                                return (
                                    <tr key={uniqueId} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4">
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={(e) => handleSelectBot(uniqueId, e.target.checked)}
                                                className="w-4 h-4 rounded border-white/20 bg-black/20 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer"
                                            />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
                                                <span className="font-mono font-bold text-foreground">{bot.symbol}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${bot.dry_run
                                                ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                                                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                                }`}>
                                                {bot.dry_run ? 'PRACTICE' : 'LIVE'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-muted-foreground capitalize">
                                                {(bot.strategy || 'Unknown').replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-mono text-muted-foreground">
                                                {bot.timeframe || '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-mono text-muted-foreground">
                                                ${bot.amount_usdt?.toFixed(0) || '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${isRunning
                                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                                : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                                }`}>
                                                {isRunning ? 'Running' : 'Stopped'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {(() => {
                                                const pnl = bot.pnl || bot.current_pnl || 0;
                                                const isPositive = pnl >= 0;
                                                return (
                                                    <span className={`font-mono font-semibold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                                                        {isPositive ? '+' : ''}{pnl.toFixed(2)} USDT
                                                    </span>
                                                );
                                            })()}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                {/* Configure Button */}
                                                <button
                                                    onClick={() => navigate('/strategies')}
                                                    className="p-1.5 hover:bg-white/10 rounded text-muted-foreground hover:text-foreground transition-all"
                                                    title="Configure Strategy"
                                                >
                                                    <Settings size={14} />
                                                </button>

                                                {isRunning ? (
                                                    <button
                                                        onClick={() => onStop(bot.symbol, bot.config_id)}
                                                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors text-sm font-medium border border-red-500/20"
                                                    >
                                                        <Square size={14} fill="currentColor" />
                                                        Stop
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => onStart(bot.symbol, bot.config_id)}
                                                        disabled={isStarting}
                                                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded-lg transition-colors text-sm font-medium border border-primary/20 disabled:opacity-50"
                                                    >
                                                        {isStarting ? (
                                                            <RefreshCw size={14} className="animate-spin" />
                                                        ) : (
                                                            <Play size={14} fill="currentColor" />
                                                        )}
                                                        {isStarting ? 'Starting...' : 'Start'}
                                                    </button>
                                                )}

                                                {/* Delete Button */}
                                                <button
                                                    onClick={() => onRemoveBot(bot.symbol, bot.config_id)}
                                                    className="p-1.5 hover:bg-red-500/10 rounded text-red-400 transition-all"
                                                    title="Delete bot"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
