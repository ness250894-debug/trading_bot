import React from 'react';
import axios from 'axios';
import { Clock, TrendingUp, TrendingDown, DollarSign, Activity, Trash2 } from 'lucide-react';
import { useToast } from './Toast';
import { useModal } from './Modal';

const TradeHistory = ({ trades, onRefresh }) => {
    const toast = useToast();
    const modal = useModal();

    const handleClearHistory = async () => {
        modal.confirm({
            title: 'Clear Trade History',
            message: 'Are you sure you want to clear all trade history? This cannot be undone.',
            confirmText: 'Clear',
            cancelText: 'Cancel',
            type: 'danger',
            onConfirm: async () => {
                try {
                    await axios.delete('/api/trades');
                    toast.success('Trade history cleared successfully');
                    if (onRefresh) onRefresh();
                } catch (err) {
                    console.error("Failed to clear history:", err);
                    toast.error("Failed to clear history");
                }
            }
        });
    };

    return (
        <div className="glass rounded-2xl overflow-hidden flex flex-col h-full">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                <h3 className="font-semibold flex items-center gap-2 text-lg">
                    <Activity size={20} className="text-primary" />
                    Recent Trades
                </h3>
                <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground bg-black/20 px-3 py-1 rounded-full border border-white/5">
                        {trades.length} trades
                    </span>
                    {trades.length > 0 && (
                        <button
                            onClick={handleClearHistory}
                            className="p-2 hover:bg-red-500/10 text-muted-foreground hover:text-red-400 rounded-lg transition-colors"
                            title="Clear History"
                        >
                            <Trash2 size={16} />
                        </button>
                    )}
                </div>
            </div>

            <div className="overflow-x-auto flex-1">
                <div className="max-h-[400px] overflow-y-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-white/5 text-muted-foreground uppercase text-xs font-medium sticky top-0 backdrop-blur-md z-10">
                            <tr>
                                <th className="px-6 py-4">Time</th>
                                <th className="px-6 py-4">Symbol</th>
                                <th className="px-6 py-4">Side</th>
                                <th className="px-6 py-4 text-right">Price</th>
                                <th className="px-6 py-4 text-right">Amount</th>
                                <th className="px-6 py-4 text-right">Size / Margin</th>
                                <th className="px-6 py-4 text-right">PnL</th>
                                <th className="px-6 py-4 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {trades.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="px-6 py-12 text-center text-muted-foreground">
                                        No trades recorded yet.
                                    </td>
                                </tr>
                            ) : (
                                trades.slice().reverse().map((trade, i) => {
                                    const pnl = trade.pnl !== undefined ? trade.pnl : (trade.profit_loss || 0);
                                    const value = trade.total_value || (trade.price * trade.amount);
                                    const leverage = trade.leverage || 1;
                                    const margin = value / leverage;

                                    return (
                                        <tr key={i} className="hover:bg-white/5 transition-colors">
                                            <td className="px-6 py-4 text-muted-foreground whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <Clock size={14} />
                                                    {new Date(trade.timestamp || Date.now()).toLocaleString()}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 font-medium">
                                                {trade.symbol || 'BTC/USDT'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold uppercase ${trade.side === 'buy' || trade.side === 'Buy'
                                                    ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                                    : 'bg-red-500/10 text-red-400 border border-red-500/20'
                                                    }`}>
                                                    {trade.side}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right font-mono">
                                                ${trade.price?.toFixed(2)}
                                            </td>
                                            <td className="px-6 py-4 text-right font-mono">
                                                {trade.amount?.toFixed(4)}
                                            </td>
                                            <td className="px-6 py-4 text-right font-mono">
                                                <div className="flex flex-col items-end">
                                                    <span className="text-white">${value?.toFixed(2)}</span>
                                                    {leverage > 1 && (
                                                        <span className="text-xs text-muted-foreground">
                                                            Margin: ${margin?.toFixed(2)} ({leverage}x)
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className={`px-6 py-4 text-right font-bold font-mono ${pnl >= 0 ? 'text-green-400' : 'text-red-400'
                                                }`}>
                                                {pnl > 0 ? '+' : ''}
                                                {pnl?.toFixed(2)}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={`text-xs px-2 py-1 rounded-full border ${trade.status === 'closed'
                                                    ? 'bg-white/5 text-muted-foreground border-white/10'
                                                    : 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse'
                                                    }`}>
                                                    {trade.status || 'Closed'}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TradeHistory;
