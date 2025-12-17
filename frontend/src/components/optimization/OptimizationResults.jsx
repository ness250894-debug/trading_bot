import React, { useState } from 'react';
import { TrendingUp, ArrowUp, ArrowDown, ArrowUpDown, CheckCircle, Activity } from 'lucide-react';
import { formatLabel } from '../../lib/utils';

export default function OptimizationResults({
    results, clearResults, symbol, applyToBacktest
}) {
    const [sortConfig, setSortConfig] = useState({ key: 'return', direction: 'desc' });

    const handleSort = (key) => {
        setSortConfig((current) => {
            if (current.key === key) {
                return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
            }
            return { key, direction: 'desc' };
        });
    };

    const sortedResults = [...results].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    return (
        <div className="glass rounded-2xl overflow-hidden flex flex-col mb-8">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                <h3 className="font-semibold flex items-center gap-2 text-lg">
                    <TrendingUp size={20} className="text-green-400" />
                    Optimization Results
                </h3>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground bg-black/20 px-3 py-1 rounded-full border border-white/5">
                        {results.length} combinations
                    </span>
                    {results.length > 0 && (
                        <button
                            onClick={clearResults}
                            className="text-xs text-red-400 hover:text-red-300 font-medium px-3 py-1 hover:bg-red-500/10 rounded transition-colors"
                        >
                            Clear
                        </button>
                    )}
                </div>
            </div>

            <div className="overflow-x-auto">
                <div className="max-h-[500px] overflow-y-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-white/5 text-muted-foreground uppercase text-xs font-medium sticky top-0 backdrop-blur-md z-10">
                            <tr>
                                <th className="px-6 py-4">Rank</th>
                                <th className="px-6 py-4">Symbol</th>
                                <th className="px-6 py-4">Parameters</th>
                                <th
                                    className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                    onClick={() => handleSort('return')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Return
                                        {sortConfig.key === 'return' ? (
                                            sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                        ) : (
                                            <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                        )}
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                    onClick={() => handleSort('win_rate')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Win Rate
                                        {sortConfig.key === 'win_rate' ? (
                                            sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                        ) : (
                                            <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                        )}
                                    </div>
                                </th>
                                <th
                                    className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors group select-none"
                                    onClick={() => handleSort('trades')}
                                >
                                    <div className="flex items-center justify-end gap-1">
                                        Trades
                                        {sortConfig.key === 'trades' ? (
                                            sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                                        ) : (
                                            <ArrowUpDown size={14} className="opacity-0 group-hover:opacity-50" />
                                        )}
                                    </div>
                                </th>
                                <th className="px-6 py-4 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {sortedResults.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="px-6 py-24 text-center">
                                        <div className="flex flex-col items-center justify-center text-muted-foreground">
                                            <Activity size={48} className="mb-4 opacity-20" />
                                            <p className="text-lg font-medium">No results yet</p>
                                            <p className="text-sm opacity-70 max-w-xs mt-2">
                                                Configure your parameters above and click "Run Optimization" to find the best strategy settings.
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                sortedResults.map((res, i) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors group">
                                        <td className="px-6 py-4 font-mono text-muted-foreground">
                                            {i === 0 && sortConfig.key === 'return' && sortConfig.direction === 'desc' ? (
                                                <span className="flex items-center gap-1 text-yellow-400 font-bold">
                                                    <CheckCircle size={14} /> #1
                                                </span>
                                            ) : `#${i + 1}`}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-cyan-300 text-xs">
                                            {symbol}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-wrap gap-2">
                                                {Object.entries(res.params).map(([k, v]) => (
                                                    <span key={k} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-white/10 text-foreground border border-white/5">
                                                        <span className="opacity-70 mr-1">{formatLabel(k)}:</span> <span className="font-bold">{v}</span>
                                                    </span>
                                                ))}
                                            </div>

                                        </td>
                                        <td className={`px-6 py-4 text-right font-bold ${res.return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {res.return > 0 ? '+' : ''}{res.return.toFixed(2)}%
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-primary"
                                                        style={{ width: `${res.win_rate}%` }}
                                                    />
                                                </div>
                                                {res.win_rate.toFixed(1)}%
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right text-muted-foreground font-mono">
                                            {res.trades}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex justify-center gap-2">
                                                <button
                                                    onClick={() => applyToBacktest(res.params)}
                                                    className="text-xs bg-white/10 text-white hover:bg-white/20 px-3 py-1.5 rounded-md font-medium transition-colors border border-white/20"
                                                >
                                                    Backtest
                                                </button>
                                            </div>
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
}
