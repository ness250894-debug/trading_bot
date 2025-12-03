import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Square, Plus, RefreshCw, Trash2, Settings } from 'lucide-react';

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
    const [selectedBots, setSelectedBots] = useState(new Set());

    // Handle multi-instance response format - combine with botConfigs
    const allBots = React.useMemo(() => {
        const runningBots = [];

        // Parse running instances
        if (instances && typeof instances === 'object' && !Array.isArray(instances)) {
            if ('is_running' in instances) {
                runningBots.push({
                    symbol: instances.symbol || 'BTC/USDT',
                    ...instances
                });
            } else {
                Object.entries(instances).forEach(([symbol, status]) => {
                    runningBots.push({
                        symbol,
                        ...status
                    });
                });
            }
        }

        // Merge with bot configs - show all configured bots
        const allBotsMap = new Map();

        // Add running bots
        runningBots.forEach(bot => {
            allBotsMap.set(bot.symbol, bot);
        });

        // Add configured bots (not yet started)
        botConfigs?.forEach(config => {
            if (!allBotsMap.has(config.symbol)) {
                allBotsMap.set(config.symbol, {
                    ...config,
                    is_running: false,
                    strategy: config.strategy
                });
            }
        });

        return Array.from(allBotsMap.values());
    }, [instances, botConfigs]);

    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedBots(new Set(allBots.map(b => b.symbol)));
        } else {
            setSelectedBots(new Set());
        }
    };

    const handleSelectBot = (symbol, checked) => {
        const newSelected = new Set(selectedBots);
        if (checked) {
            newSelected.add(symbol);
        } else {
            newSelected.delete(symbol);
        }
        setSelectedBots(newSelected);
    };

    const handleStartSelected = async () => {
        for (const symbol of selectedBots) {
            await onStart(symbol);
        }
    };

    const handleStopSelected = async () => {
        for (const symbol of selectedBots) {
            await onStop(symbol);
        }
    };

    const handleBulkDelete = async () => {
        if (onBulkRemove) {
            await onBulkRemove(Array.from(selectedBots));
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
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-semibold text-foreground">Active Bot Instances</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        {allBots.length} {allBots.length === 1 ? 'bot' : 'bots'} configured
                        {someSelected && ` • ${selectedBots.size} selected`}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => navigate('/strategies')}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-white hover:bg-primary/90 rounded-lg transition-all font-medium"
                    >
                        <Plus size={16} />
                        Add Bot
                    </button>
                    {someSelected && (
                        <>
                            <button
                                onClick={handleStartSelected}
                                className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-500 hover:bg-green-500/20 rounded-lg transition-colors border border-green-500/20"
                                title="Start Selected"
                            >
                                <Play size={16} fill="currentColor" />
                            </button>
                            <button
                                onClick={handleStopSelected}
                                className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
                                title="Stop Selected"
                            >
                                <Square size={16} fill="currentColor" />
                            </button>
                            <button
                                onClick={handleBulkDelete}
                                className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
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
                <div className="overflow-x-auto">
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
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Strategy</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Started At</th>
                                <th className="px-6 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {allBots.map((bot) => {
                                const isRunning = bot.is_running || false;
                                const isStarting = startingBots?.has(bot.symbol);
                                const isSelected = selectedBots.has(bot.symbol);
                                const config = botConfigs?.find(c => c.symbol === bot.symbol);

                                return (
                                    <tr key={bot.symbol} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4">
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={(e) => handleSelectBot(bot.symbol, e.target.checked)}
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
                                            <span className="text-sm text-muted-foreground capitalize">
                                                {(bot.strategy || bot.config?.strategy || 'Unknown').replace(/_/g, ' ')}
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
                                        <td className="px-6 py-4 text-sm text-muted-foreground font-mono">
                                            {bot.started_at ? new Date(bot.started_at).toLocaleString() : 'N/A'}
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
                                                        onClick={() => onStop(bot.symbol)}
                                                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors text-sm font-medium border border-red-500/20"
                                                    >
                                                        <Square size={14} fill="currentColor" />
                                                        Stop
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => onStart(bot.symbol)}
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
                                                    onClick={() => config ? onRemoveBot(config.id) : null}
                                                    disabled={!config}
                                                    className="p-1.5 hover:bg-red-500/10 rounded text-red-400 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                                                    title="Remove bot configuration"
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
