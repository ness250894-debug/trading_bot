import React from 'react';
import { Settings, Square, Play, RefreshCw, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * BotCard - Renders a single card in the BotInstancesTable for mobile view
 */
export default function BotCard({
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
        <div className={`glass p-4 rounded-xl border transition-all ${isSelected ? 'border-primary/50 bg-primary/5' : 'border-white/5'}`}>
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => onSelect(uniqueId, e.target.checked)}
                        className="w-4 h-4 rounded border-white/20 bg-black/20 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer"
                    />
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-foreground text-lg">{bot.symbol}</span>
                            <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${bot.dry_run
                                ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                }`}>
                                {bot.dry_run ? 'PRACTICE' : 'LIVE'}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${isRunning
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                }`}>
                                {isRunning ? 'Running' : 'Stopped'}
                            </span>
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className={`font-mono font-bold text-lg ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {isPositive ? '+' : ''}{pnl.toFixed(2)}
                    </div>
                    <div className="text-xs text-muted-foreground">USDT PnL</div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground mb-4 bg-white/5 p-3 rounded-lg">
                <div>Strategy: <span className="text-foreground capitalize">{(bot.strategy || 'Unknown').replace(/_/g, ' ')}</span></div>
                <div>Timeframe: <span className="text-foreground font-mono">{bot.timeframe || '-'}</span></div>
                <div>Amount: <span className="text-foreground font-mono">${bot.amount_usdt?.toFixed(0) || '-'}</span></div>
                <div>TP/SL:
                    <span className="text-green-400 font-mono">
                        {bot.take_profit_pct ? (bot.take_profit_pct * 100).toFixed(1) + '%' : '-'}
                        {bot.tp_price ? ` ($${bot.tp_price.toFixed(2)})` : ''}
                    </span> /{' '}
                    <span className="text-red-400 font-mono">
                        {bot.stop_loss_pct ? (bot.stop_loss_pct * 100).toFixed(1) + '%' : '-'}
                        {bot.sl_price ? ` ($${bot.sl_price.toFixed(2)})` : ''}
                    </span>
                </div>
                <div>Trades: <span className="text-foreground font-mono">{bot.active_trades || 0}</span></div>
            </div>

            <div className="flex gap-2">
                {isRunning ? (
                    <button
                        onClick={() => onStop(bot.symbol, bot.config_id)}
                        className="flex-1 inline-flex justify-center items-center gap-2 px-3 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors text-sm font-medium border border-red-500/20"
                    >
                        <Square size={16} fill="currentColor" />
                        Stop
                    </button>
                ) : (
                    <button
                        onClick={() => onStart(bot.symbol, bot.config_id)}
                        disabled={isStarting}
                        className="flex-1 inline-flex justify-center items-center gap-2 px-3 py-2 bg-primary/10 text-primary hover:bg-primary/20 rounded-lg transition-colors text-sm font-medium border border-primary/20 disabled:opacity-50"
                    >
                        {isStarting ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <Play size={16} fill="currentColor" />
                        )}
                        {isStarting ? 'Starting...' : 'Start'}
                    </button>
                )}
                <button
                    onClick={() => navigate('/strategies')}
                    className="px-3 py-2 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-foreground transition-all border border-white/10"
                    title="Configure"
                >
                    <Settings size={18} />
                </button>
                <button
                    onClick={() => onRemove(bot.symbol, bot.config_id)}
                    className="px-3 py-2 hover:bg-red-500/10 rounded-lg text-red-400 transition-all border border-red-500/10"
                    title="Delete"
                >
                    <Trash2 size={18} />
                </button>
            </div>
        </div>
    );
}
