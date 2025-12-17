import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import PlanGate from '../components/PlanGate';

// Hooks
import useUltimateOptimization from '../hooks/useUltimateOptimization';

// Components
import UltimateOptimization from '../components/optimization/UltimateOptimization';

// Constants
import {
    strategyInfo,
    presets,
    POPULAR_SYMBOLS,
    STRATEGY_PARAM_KEYS
} from '../lib/constants/strategyConstants';

export default function UltimateOptimizationPage() {
    // Ultimate Optimization State
    const [ultimateSymbol, setUltimateSymbol] = useState(() => localStorage.getItem('ultimate_optimization_symbol') || 'BTC/USDT');
    const [ultimateCustomSymbol, setUltimateCustomSymbol] = useState(false);
    const [subscription, setSubscription] = useState(null);
    const [symbol, setSymbol] = useState(() => localStorage.getItem('optimization_symbol') || 'BTC/USDT'); // Reuse symbol for consistency if needed, though ultimate has its own

    // Fetch subscription
    useEffect(() => {
        api.get('/billing/status')
            .then(res => setSubscription(res.data))
            .catch(err => console.error("Failed to fetch subscription:", err));
    }, []);

    const {
        ultimateResults,
        clearUltimateResults,
        isUltimateOptimizing,
        runUltimateOptimization,
        progress: ultimateProgress
    } = useUltimateOptimization(ultimateSymbol, presets, strategyInfo, STRATEGY_PARAM_KEYS, subscription);

    // Persistence Effects
    useEffect(() => { localStorage.setItem('ultimate_optimization_symbol', ultimateSymbol); }, [ultimateSymbol]);

    const applyToBacktest = (params, strategyOverride = null, timeframeOverride = null, symbolOverride = null) => {
        const suggestion = {
            strategy: strategyOverride, // Ultimate results always have a strategy override
            timeframe: timeframeOverride || '1h',
            symbol: symbolOverride || ultimateSymbol,
            params: params // Params is already the flat object passed from component
        };
        localStorage.setItem('backtest_params_suggestion', JSON.stringify(suggestion));
        window.location.href = '/backtest';
    };

    return (
        <PlanGate feature="Ultimate Optimization" explanation="Automatically find the absolute best strategy and parameters across all combinations.">
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
                        <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 mb-2">
                            Ultimate Optimization
                        </h1>
                        <p className="text-muted-foreground max-w-2xl">
                            Run all strategies automatically to find the absolute best market fit.
                        </p>
                    </div>
                </div>

                <UltimateOptimization
                    ultimateSymbol={ultimateSymbol}
                    setUltimateSymbol={setUltimateSymbol}
                    ultimateCustomSymbol={ultimateCustomSymbol}
                    setUltimateCustomSymbol={setUltimateCustomSymbol}
                    POPULAR_SYMBOLS={POPULAR_SYMBOLS}
                    isOptimizing={false} // Independent page, valid to say not standard optimizing
                    isUltimateOptimizing={isUltimateOptimizing}
                    runUltimateOptimization={runUltimateOptimization}
                    clearUltimateResults={clearUltimateResults}
                    ultimateResults={ultimateResults}
                    progress={ultimateProgress}
                    subscription={subscription}
                    applyToBacktest={applyToBacktest}
                    symbol={symbol} // Used for comparison or default? checking UltimateOptimization props usage. 
                // It uses symbol and ultimateSymbol. passing symbol (Optimization page symbol) might be confusing if they differ.
                // In Optimization.jsx, it passed 'symbol' from the main state.
                // Inside UltimateOptimization, it compares symbol vs ultimateSymbol? 
                // No, checking UltimateOptimization.jsx usage...
                />
            </div>
        </PlanGate>
    );
}
