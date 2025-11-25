import React from 'react';
import { Clock, TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';

const TradeHistory = ({ trades }) => {
    return (
        <div className="glass rounded-2xl overflow-hidden flex flex-col h-full">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                <h3 className="font-semibold flex items-center gap-2 text-lg">
                    <Activity size={20} className="text-primary" />
                    Recent Trades
                </h3>
                <span className="text-sm text-muted-foreground bg-black/20 px-3 py-1 rounded-full border border-white/5">
                    {trades.length} trades
                </span>
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
                                <th className="px-6 py-4 text-right">PnL</th>
                                <th className="px-6 py-4 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {trades.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="px-6 py-12 text-center text-muted-foreground">
                                        No trades recorded yet.
                                    </td>
                                </tr>
                            ) : (
                                trades.slice().reverse().map((trade, i) => (
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
                                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold uppercase ${trade.side === 'buy'
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
                                            {trade.amount}
                                        </td>
                                        <td className={`px-6 py-4 text-right font-bold font-mono ${trade.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                                            }`}>
                                            {trade.profit_loss > 0 ? '+' : ''}{trade.profit_loss?.toFixed(2)}
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
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TradeHistory;
