import React from 'react';
import { Play, Square, Trash2 } from 'lucide-react';

/**
 * BotInstancesTable - Displays all running bot instances with per-symbol controls
 */
export default function BotInstancesTable({ instances, onStart, onStop, onStopAll, loading }) {
    // Handle multi-instance response format
    const instancesArray = React.useMemo(() => {
        if (!instances) return [];

        // Check if it's a multi-instance dict (object with nested status objects)
        if (typeof instances === 'object' && !Array.isArray(instances)) {
            // If it has 'is_running' key, it's a single instance wrapped in old format
            if ('is_running' in instances) {
                return [{
                    symbol: instances.symbol || 'BTC/USDT',
                    ...instances
                }];
            }

            // Otherwise it's multi-instance: {symbol: {status obj}}
            return Object.entries(instances).map(([symbol, status]) => ({
                symbol,
                ...status
            }));
        }

        return [];
    }, [instances]);

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
                        {instancesArray.length} {instancesArray.length === 1 ? 'bot' : 'bots'} running
                    </p>
                </div>
                {instancesArray.length > 0 && (
                    <button
                        onClick={onStopAll}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors border border-red-500/20"
                    >
                        <Square size={16} fill="currentColor" />
                        Stop All
                    </button>
                )}
            </div>

            {instancesArray.length === 0 ? (
                <div className="p-12 text-center">
                    <p className="text-muted-foreground mb-4">No bot instances running</p>
                    <p className="text-sm text-muted-foreground/60">Configure your strategy and click Start Bot to begin trading</p>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-white/5">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Symbol</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Strategy</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Started At</th>
                                <th className="px-6 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {instancesArray.map((instance) => (
                                <tr key={instance.symbol} className="hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className={`w-2 h-2 rounded-full ${instance.is_running ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
                                            <span className="font-mono font-bold text-foreground">{instance.symbol}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-muted-foreground capitalize">
                                            {instance.strategy?.replace(/_/g, ' ') || 'Unknown'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${instance.is_running
                                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                                : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                            }`}>
                                            {instance.is_running ? 'Running' : 'Stopped'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-muted-foreground font-mono">
                                        {instance.started_at ? new Date(instance.started_at).toLocaleString() : 'N/A'}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        {instance.is_running ? (
                                            <button
                                                onClick={() => onStop(instance.symbol)}
                                                className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors text-sm font-medium border border-red-500/20"
                                            >
                                                <Square size={14} fill="currentColor" />
                                                Stop
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => onStart(instance.symbol)}
                                                className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded-lg transition-colors text-sm font-medium border border-primary/20"
                                            >
                                                <Play size={14} fill="currentColor" />
                                                Restart
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
