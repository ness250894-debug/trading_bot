import React from 'react';
import { Crown, Lock, Play } from 'lucide-react';
import { formatLabel } from '../../lib/utils';

export default function UltimateOptimization({
    ultimateSymbol, setUltimateSymbol, ultimateCustomSymbol, setUltimateCustomSymbol, POPULAR_SYMBOLS,
    isOptimizing, isUltimateOptimizing, runUltimateOptimization, clearUltimateResults, ultimateResults, progress, subscription,
    applyToBacktest, symbol
}) {
    return (
        <div className="glass rounded-2xl overflow-hidden flex flex-col border border-purple-500/20 shadow-lg shadow-purple-900/10 mb-8">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-gradient-to-r from-purple-900/20 to-transparent">
                <div className="flex items-center gap-3">
                    <h3 className="font-semibold flex items-center gap-2 text-lg text-purple-100">
                        <Crown size={20} className="text-purple-400" />
                        Ultimate Optimization Results
                    </h3>
                    {isUltimateOptimizing && (
                        <span className="text-xs text-purple-300 animate-pulse bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                            Running... {progress.current} / {progress.total}
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    {/* Symbol Selector for Ultimate */}
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-purple-200">Symbol:</label>
                        {ultimateCustomSymbol ? (
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    placeholder="e.g., BTC/USDT"
                                    className="bg-black/20 border border-purple-500/30 rounded-lg p-2 text-foreground focus:ring-2 focus:ring-purple-500/50 outline-none transition-all text-sm font-mono uppercase w-32"
                                    value={ultimateSymbol}
                                    onChange={(e) => setUltimateSymbol(e.target.value.toUpperCase())}
                                />
                                <button
                                    onClick={() => setUltimateCustomSymbol(false)}
                                    className="text-xs text-purple-300 hover:text-purple-200 transition-colors"
                                >
                                    ← Back
                                </button>
                            </div>
                        ) : (
                            <div className="relative">
                                <select
                                    className="bg-black/20 border border-purple-500/30 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-purple-500/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white font-mono"
                                    value={POPULAR_SYMBOLS.includes(ultimateSymbol) ? ultimateSymbol : 'CUSTOM'}
                                    onChange={(e) => {
                                        if (e.target.value === 'CUSTOM') {
                                            setUltimateCustomSymbol(true);
                                        } else {
                                            setUltimateSymbol(e.target.value);
                                        }
                                    }}
                                >
                                    {POPULAR_SYMBOLS.map(s => <option key={s} value={s}>{s === 'CUSTOM' ? '+ Custom' : s}</option>)}
                                </select>
                                <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={runUltimateOptimization}
                        disabled={isOptimizing || isUltimateOptimizing}
                        className={`px-4 py-2 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg text-sm ${subscription?.plan === 'free'
                            ? 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 cursor-pointer'
                            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/25'
                            }`}
                    >
                        {isUltimateOptimizing ? (
                            <span className="animate-spin rounded-full h-4 w-4 border-2 border-white/20 border-t-white"></span>
                        ) : (
                            subscription?.plan === 'free' ? <Lock size={16} /> : <Play size={16} fill="currentColor" />
                        )}
                        Run Ultimate Optimization
                    </button>
                    {ultimateResults.length > 0 && (
                        <button
                            onClick={clearUltimateResults}
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
                                <th className="px-6 py-4">Strategy</th>
                                <th className="px-6 py-4">Symbol</th>
                                <th className="px-6 py-4">Rank</th>
                                <th className="px-6 py-4">Parameters</th>
                                <th className="px-6 py-4 text-right">Return</th>
                                <th className="px-6 py-4 text-right">Win Rate</th>
                                <th className="px-6 py-4 text-right">Trades</th>
                                <th className="px-6 py-4 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {ultimateResults.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="px-6 py-16 text-center text-muted-foreground">
                                        <div className="flex flex-col items-center justify-center gap-2 opacity-50">
                                            <Crown size={32} />
                                            <p>Run Ultimate Optimization to compare all strategies</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                ultimateResults.sort((a, b) => b.return - a.return).map((res, i) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors group">
                                        <td className="px-6 py-4 font-medium text-purple-200">
                                            {res.strategy}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-cyan-300 text-xs">
                                            {res.params?.symbol || res.symbol || symbol}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-muted-foreground">
                                            #{i + 1}
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
                                            {res.win_rate.toFixed(1)}%
                                        </td>
                                        <td className="px-6 py-4 text-right text-muted-foreground font-mono">
                                            {res.trades}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex justify-center gap-2">
                                                <button
                                                    onClick={() => {
                                                        applyToBacktest(res.params, res.strategy, res.timeframe || '1h', res.symbol);
                                                    }}
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
