import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import PlanGate from '../components/PlanGate';
import { useAppState } from '../hooks/useAppState';
import { STORAGE_KEYS } from '../constants/storageKeys';
import secureStorage from '../lib/secureStorage';

// Hooks
import useOptimization from '../hooks/useOptimization';
// Components
import OptimizationConfig from '../components/optimization/OptimizationConfig';
import OptimizationResults from '../components/optimization/OptimizationResults';

// Constants
import {
    strategyInfo,
    presets,
    TIMEFRAME_OPTIONS,
    POPULAR_SYMBOLS,
    STRATEGY_PARAM_KEYS,
    STRATEGY_NAME_MAP
} from '../lib/constants/strategyConstants';

export default function Optimization() {
    const [strategy, setStrategy] = useAppState(STORAGE_KEYS.OPTIMIZATION_STRATEGY, 'SMA Crossover');
    const [symbol, setSymbol] = useAppState(STORAGE_KEYS.OPTIMIZATION_SYMBOL, 'BTC/USDT');
    const [customSymbol, setCustomSymbol] = useState(false);
    const [timeframe, setTimeframe] = useAppState(STORAGE_KEYS.OPTIMIZATION_TIMEFRAME, '1m');
    const [nTrials, setNTrials] = useState(50);
    const [leverage, setLeverage] = useAppState(STORAGE_KEYS.OPTIMIZATION_LEVERAGE, 10);

    // Initial Ranges State with validation
    const [ranges, setRanges] = useAppState(STORAGE_KEYS.OPTIMIZATION_RANGES, {
        fast_period: { start: 5, end: 20, step: 5 },
        slow_period: { start: 30, end: 60, step: 10 }
    });

    // Hooks
    const {
        results,
        clearResults,
        loading,
        isOptimizing,
        progress: optimizationProgress,
        runOptimization
    } = useOptimization(strategy, symbol, timeframe, ranges, nTrials, leverage);

    // Handlers
    const strategies = Object.keys(strategyInfo);

    const handleStrategyChange = (e) => {
        const newStrategy = e.target.value;
        setStrategy(newStrategy);
        clearResults();
        // Reset ranges to first preset or defaults
        if (presets[newStrategy] && presets[newStrategy].length > 0) {
            setRanges(presets[newStrategy][0].ranges);
        } else {
            setRanges({});
        }
    };

    const applyPreset = (preset) => {
        setRanges(preset.ranges);
        if (preset.timeframe) {
            setTimeframe(preset.timeframe);
        }
    };

    const handleRangeChange = (param, field, value) => {
        setRanges(prev => {
            const currentRange = prev[param];
            let newValue = parseFloat(value);
            let newRange = { ...currentRange, [field]: newValue };

            if (field === 'start') {
                if (newValue > currentRange.end) {
                    newValue = Math.min(newValue, currentRange.end);
                    newRange.start = newValue;
                }
            } else if (field === 'end') {
                if (newValue < currentRange.start) {
                    newValue = Math.max(newValue, currentRange.start);
                    newRange.end = newValue;
                }
            }

            return { ...prev, [param]: newRange };
        });
    };

    const applyToBacktest = (params, strategyOverride = null, timeframeOverride = null, symbolOverride = null) => {
        const suggestion = {
            strategy: strategyOverride || strategy,
            timeframe: timeframeOverride || timeframe,
            symbol: symbolOverride || symbol,
            leverage: leverage,
            params: params
        };
        secureStorage.setAppState(STORAGE_KEYS.BACKTEST_PARAMS, suggestion);
        window.location.href = '/backtest';
    };

    return (
        <PlanGate feature="Strategy Optimization" explanation="Fine-tune your strategy parameters to maximize profitability using historical data.">
            <div className="max-w-7xl mx-auto space-y-8">
                <style>{`
                    .glass {
                        background: rgba(10, 10, 15, 0.4);
                        backdrop-filter: blur(16px);
                        -webkit-backdrop-filter: blur(16px);
                    }
                `}</style>

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div>
                        <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-indigo-500 mb-2">
                            Strategy Optimization
                        </h1>
                        <p className="text-muted-foreground max-w-2xl">
                            Find the perfect parameters for your trading strategy using genetic algorithms.
                        </p>
                    </div>
                </div>

                {/* Main Configuration Config */}
                <OptimizationConfig
                    symbol={symbol}
                    setSymbol={setSymbol}
                    customSymbol={customSymbol}
                    setCustomSymbol={setCustomSymbol}
                    POPULAR_SYMBOLS={POPULAR_SYMBOLS}
                    timeframe={timeframe}
                    setTimeframe={setTimeframe}
                    TIMEFRAME_OPTIONS={TIMEFRAME_OPTIONS}
                    strategy={strategy}
                    setStrategy={setStrategy}
                    strategies={strategies}
                    handleStrategyChange={handleStrategyChange}
                    presets={presets}
                    applyPreset={applyPreset}
                    ranges={ranges}
                    handleRangeChange={handleRangeChange}
                    nTrials={nTrials}
                    setNTrials={setNTrials}
                    leverage={leverage}
                    setLeverage={setLeverage}
                    runOptimization={runOptimization}
                    isOptimizing={isOptimizing}
                    progress={optimizationProgress}
                />

                {/* Standard Optimization Results */}
                <OptimizationResults
                    results={results}
                    clearResults={clearResults}
                    symbol={symbol}
                    leverage={leverage}
                    applyToBacktest={(params) => applyToBacktest(params)}
                />
            </div>
        </PlanGate>
    );
}
