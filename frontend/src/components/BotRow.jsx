import React from 'react';
import { Settings, Square, Play, RefreshCw, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * BotRow - Renders a single row in the BotInstancesTable for desktop view
 */
export default function BotRow({
    bot,
    isSelected,
    isStarting,
    onSelect,
    onStart,
    onStop,
    onRemove
}) {
    const navigate = useNavigate();
    const isRunning = bot.is_running || false;
    const uniqueId = bot.config_id || bot.symbol;

    // Calculate PnL display
    const pnl = bot.pnl || bot.current_pnl || 0;
    const isPositive = pnl >= 0;

    return (
        <tr className="hover:bg-white/5 transition-colors">
            <td className="px-6 py-4">
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => onSelect(uniqueId, e.target.checked)}
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
                <span className={`font-mono font-semibold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                    {isPositive ? '+' : ''}{pnl.toFixed(2)} USDT
                </span>
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
                        onClick={() => onRemove(bot.symbol, bot.config_id)}
                        className="p-1.5 hover:bg-red-500/10 rounded text-red-400 transition-all"
                        title="Delete bot"
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </td>
        </tr>
    );
}
