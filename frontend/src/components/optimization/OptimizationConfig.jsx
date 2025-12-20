import React from 'react';
import { Settings, Sliders, Activity, Play } from 'lucide-react';
import SliderInput from '../ui/SliderInput';
import { formatLabel } from '../../lib/utils';
import { parameterInfo, paramLimits } from '../../lib/constants/strategyConstants';

export default function OptimizationConfig({
    symbol, setSymbol, customSymbol, setCustomSymbol, POPULAR_SYMBOLS,
    timeframe, setTimeframe, TIMEFRAME_OPTIONS,
    strategy, setStrategy, strategies, handleStrategyChange,
    presets, applyPreset,
    ranges, handleRangeChange,
    nTrials, setNTrials,

    leverage, setLeverage,
    runOptimization, isOptimizing, progress
}) {
    return (
        <div className="glass p-4 rounded-2xl">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 border-b border-white/10 pb-3 gap-4">
                <h3 className="font-semibold flex items-center gap-2 text-base text-foreground">
                    <Settings size={18} className="text-primary" />
                    Configuration
                </h3>
                <div className="flex flex-col sm:flex-row w-full md:w-auto items-start sm:items-center gap-4">
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-foreground">Symbol:</label>
                        {customSymbol ? (
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    placeholder="e.g., BTC/USDT"
                                    className="bg-black/20 border border-white/10 rounded-lg p-2 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm font-mono uppercase w-32"
                                    value={symbol}
                                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                />
                                <button
                                    onClick={() => setCustomSymbol(false)}
                                    className="text-xs text-primary hover:text-primary/80 transition-colors"
                                >
                                    ← Back
                                </button>
                            </div>
                        ) : (
                            <div className="relative">
                                <select
                                    className="bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white font-mono"
                                    value={POPULAR_SYMBOLS.includes(symbol) ? symbol : 'CUSTOM'}
                                    onChange={(e) => {
                                        if (e.target.value === 'CUSTOM') {
                                            setCustomSymbol(true);
                                        } else {
                                            setSymbol(e.target.value);
                                        }
                                    }}
                                >
                                    {POPULAR_SYMBOLS.map(s => <option key={s} value={s}>{s === 'CUSTOM' ? '+ Custom' : s}</option>)}
                                </select>
                                <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-foreground">Timeframe:</label>
                        <div className="relative">
                            <select
                                className="bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white"
                                value={timeframe}
                                onChange={(e) => setTimeframe(e.target.value)}
                            >
                                {(TIMEFRAME_OPTIONS || []).map(tf => <option key={tf} value={tf}>{tf}</option>)}
                            </select>
                            <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 min-w-[140px]">
                        <SliderInput
                            label="Leverage (x)"
                            value={leverage}
                            min={1}
                            max={125}
                            step={1}
                            onChange={setLeverage}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-foreground">Strategy:</label>
                        <div className="relative">
                            <select
                                className="bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground focus:ring-2 focus:ring-primary/50 outline-none transition-all text-sm appearance-none cursor-pointer hover:bg-black/30 [&>option]:bg-zinc-900 [&>option]:text-white"
                                value={strategy}
                                onChange={handleStrategyChange}
                            >
                                {(strategies || []).map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Presets */}
            {presets && presets[strategy] && presets[strategy].length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6 p-3 bg-white/5 rounded-xl border border-white/10">
                    <span className="text-xs font-bold text-muted-foreground uppercase flex items-center mr-2">
                        <Sliders size={12} className="mr-1" /> Presets:
                    </span>
                    {presets[strategy].map((preset, idx) => (
                        <button
                            key={idx}
                            onClick={() => applyPreset(preset)}
                            className="px-3 py-1 bg-black/20 hover:bg-primary/20 hover:text-primary text-xs font-medium rounded-full border border-white/5 transition-all"
                        >
                            {preset.name}
                        </button>
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {ranges && Object.entries(ranges).map(([param, range]) => {
                    const limits = paramLimits[param] || { min: 0, max: 100, step: 1 };
                    return (
                        <div key={param} className="p-3 bg-white/5 rounded-xl border border-white/5">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs font-bold text-foreground capitalize">
                                    {formatLabel(param)}
                                </span>
                            </div>

                            <SliderInput
                                label="Start"
                                value={range.start}
                                min={limits.min}
                                max={limits.max}
                                step={limits.step}
                                onChange={(val) => handleRangeChange(param, 'start', val)}
                                description={parameterInfo[param]}
                            />

                            <SliderInput
                                label="End"
                                value={range.end}
                                min={limits.min}
                                max={limits.max}
                                step={limits.step}
                                onChange={(val) => handleRangeChange(param, 'end', val)}
                            />

                            <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
                                <label className="text-[10px] text-muted-foreground">Step</label>
                                <input
                                    type="number"
                                    className="w-12 bg-black/20 border border-white/10 rounded px-1.5 py-0.5 text-[10px] text-right"
                                    value={range.step}
                                    min={limits.step}
                                    step={limits.step}
                                    onChange={(e) => handleRangeChange(param, 'step', e.target.value)}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-6 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <div className="w-full sm:w-48">
                    <label className="text-xs font-medium text-muted-foreground mb-1 block">Trials: {nTrials}</label>
                    <input
                        type="range"
                        min="10"
                        max="200"
                        step="10"
                        value={nTrials}
                        onChange={(e) => setNTrials(Number(e.target.value))}
                        className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary hover:accent-primary/80 transition-all"
                    />
                </div>
                <button
                    onClick={runOptimization}
                    disabled={isOptimizing}
                    className="flex-1 bg-primary hover:bg-primary/90 text-white py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 disabled:opacity-70 disabled:cursor-not-allowed text-sm"
                >
                    {isOptimizing ? (
                        <span className="animate-pulse flex items-center gap-2">
                            <Activity className="animate-spin" size={16} /> Optimizing...
                        </span>
                    ) : (
                        <>
                            <Play size={16} fill="currentColor" /> Run Optimization
                        </>
                    )}
                </button>
                {isOptimizing && (
                    <div className="flex-1 flex flex-col gap-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Progress</span>
                            <span>{progress.current} / {progress.total}</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary transition-all duration-300"
                                style={{ width: `${(progress.current / Math.max(progress.total, 1)) * 100}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
