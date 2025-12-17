export const strategyInfo = {
    'SMA Crossover': "A classic trend-following strategy. It buys when a short-term moving average crosses above a long-term one (bullish signal) and sells when it crosses below (bearish signal). Best for trending markets.",
    'Mean Reversion': "Assumes prices will revert to their average. Uses Bollinger Bands and RSI to identify overbought (sell) or oversold (buy) conditions. Best for ranging/sideways markets.",
    'RSI': "Uses the Relative Strength Index to find momentum. Buys when RSI is low (oversold) and sells when RSI is high (overbought). Simple and effective for catching reversals.",
    'MACD': "Moving Average Convergence Divergence. A momentum indicator that follows trends. Good for identifying the strength and direction of a trend.",
    'Bollinger Breakout': "Buys when price breaks above the upper Bollinger Band with volume confirmation. Sells when price drops below the middle band.",
    'Momentum': "Uses Rate of Change (ROC) and RSI to identify strong momentum. Buys when momentum is high and RSI is not overbought.",
    'DCA Dip': "Dollar Cost Averaging on dips. Buys when price drops below a short-term EMA while above a long-term EMA (uptrend)."
};

export const parameterInfo = {
    fast_period: "The period for the faster moving average. A smaller number makes it more sensitive to recent price changes.",
    slow_period: "The period for the slower moving average. A larger number smooths out noise but reacts slower to trends.",
    bb_period: "The number of periods used for the Bollinger Bands moving average.",
    bb_std: "Standard Deviations for the bands. Higher values make the bands wider, requiring more extreme price moves to trigger signals.",
    rsi_period: "The lookback period for RSI calculation. Standard is 14.",
    rsi_oversold: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    rsi_overbought: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    period: "The lookback period for the indicator.",
    oversold: "The RSI level considered 'oversold'. Prices below this trigger a buy signal.",
    overbought: "The RSI level considered 'overbought'. Prices above this trigger a sell signal.",
    signal_period: "The EMA period for the signal line.",
    volume_factor: "Multiplier for volume to confirm a breakout. Volume must be > average volume * factor.",
    roc_period: "The period for Rate of Change calculation.",
    rsi_min: "Minimum RSI required to enter a momentum trade.",
    rsi_max: "Maximum RSI allowed to enter (to avoid buying tops).",
    ema_long: "Long-term EMA period to define the major trend.",
    ema_short: "Short-term EMA period to define the dip."
};

export const paramLimits = {
    fast_period: { min: 2, max: 50, step: 1 },
    slow_period: { min: 10, max: 200, step: 5 },
    bb_period: { min: 5, max: 50, step: 1 },
    bb_std: { min: 0.5, max: 4.0, step: 0.1 },
    rsi_period: { min: 2, max: 30, step: 1 },
    rsi_oversold: { min: 5, max: 45, step: 1 },
    rsi_overbought: { min: 55, max: 95, step: 1 },
    period: { min: 2, max: 50, step: 1 },
    oversold: { min: 5, max: 45, step: 1 },
    overbought: { min: 55, max: 95, step: 1 },
    signal_period: { min: 2, max: 30, step: 1 },
    volume_factor: { min: 1.0, max: 5.0, step: 0.1 },
    roc_period: { min: 2, max: 50, step: 1 },
    rsi_min: { min: 30, max: 60, step: 1 },
    rsi_max: { min: 60, max: 90, step: 1 },
    ema_long: { min: 50, max: 300, step: 10 },
    ema_short: { min: 5, max: 50, step: 1 }
};

export const presets = {
    'SMA Crossover': [
        { name: 'Conservative', timeframe: '1h', ranges: { fast_period: { start: 10, end: 20, step: 2 }, slow_period: { start: 50, end: 100, step: 10 } } },
        { name: 'Aggressive', timeframe: '5m', ranges: { fast_period: { start: 3, end: 10, step: 1 }, slow_period: { start: 15, end: 40, step: 5 } } },
        { name: 'Wide Search', timeframe: '15m', ranges: { fast_period: { start: 2, end: 30, step: 2 }, slow_period: { start: 20, end: 150, step: 10 } } }
    ],
    'Mean Reversion': [
        { name: 'Standard', timeframe: '1h', ranges: { bb_period: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, rsi_period: { start: 14, end: 14, step: 1 }, rsi_oversold: { start: 30, end: 30, step: 1 }, rsi_overbought: { start: 70, end: 70, step: 1 } } },
        { name: 'Volatile Market', timeframe: '15m', ranges: { bb_period: { start: 10, end: 30, step: 5 }, bb_std: { start: 2.0, end: 3.0, step: 0.2 }, rsi_period: { start: 10, end: 20, step: 2 }, rsi_oversold: { start: 20, end: 40, step: 5 }, rsi_overbought: { start: 60, end: 80, step: 5 } } }
    ],
    'RSI': [
        { name: 'Scalping', timeframe: '1m', ranges: { period: { start: 5, end: 10, step: 1 }, oversold: { start: 20, end: 30, step: 2 }, overbought: { start: 70, end: 80, step: 2 } } },
        { name: 'Swing', timeframe: '4h', ranges: { period: { start: 14, end: 28, step: 2 }, oversold: { start: 30, end: 40, step: 2 }, overbought: { start: 60, end: 70, step: 2 } } }
    ],
    'MACD': [
        { name: 'Standard', timeframe: '1h', ranges: { fast_period: { start: 12, end: 12, step: 1 }, slow_period: { start: 26, end: 26, step: 1 }, signal_period: { start: 9, end: 9, step: 1 } } },
        { name: 'Fast', timeframe: '15m', ranges: { fast_period: { start: 5, end: 15, step: 1 }, slow_period: { start: 15, end: 30, step: 2 }, signal_period: { start: 5, end: 10, step: 1 } } }
    ],
    'Bollinger Breakout': [
        { name: 'Standard', timeframe: '1h', ranges: { bb_period: { start: 20, end: 20, step: 1 }, bb_std: { start: 2.0, end: 2.0, step: 0.1 }, volume_factor: { start: 1.5, end: 1.5, step: 0.1 } } },
        { name: 'Volatile', timeframe: '15m', ranges: { bb_period: { start: 10, end: 30, step: 2 }, bb_std: { start: 1.5, end: 2.5, step: 0.1 }, volume_factor: { start: 1.2, end: 2.0, step: 0.1 } } }
    ],
    'Momentum': [
        { name: 'Standard', timeframe: '1h', ranges: { roc_period: { start: 10, end: 10, step: 1 }, rsi_period: { start: 14, end: 14, step: 1 }, rsi_min: { start: 50, end: 50, step: 1 }, rsi_max: { start: 70, end: 70, step: 1 } } },
        { name: 'Scalp', timeframe: '5m', ranges: { roc_period: { start: 5, end: 15, step: 1 }, rsi_period: { start: 7, end: 14, step: 1 }, rsi_min: { start: 40, end: 55, step: 5 }, rsi_max: { start: 65, end: 80, step: 5 } } }
    ],
    'DCA Dip': [
        { name: 'Standard', timeframe: '4h', ranges: { ema_long: { start: 200, end: 200, step: 10 }, ema_short: { start: 20, end: 20, step: 1 } } },
        { name: 'Aggressive', timeframe: '1h', ranges: { ema_long: { start: 100, end: 200, step: 20 }, ema_short: { start: 10, end: 30, step: 2 } } }
    ]
};

export const STRATEGY_NAME_MAP = {
    'SMA Crossover': 'sma_crossover',
    'Mean Reversion': 'mean_reversion',
    'RSI': 'rsi',
    'MACD': 'macd',
    'Bollinger Breakout': 'bollinger_breakout',
    'Momentum': 'momentum',
    'DCA Dip': 'dca_dip'
};

export const TIMEFRAME_OPTIONS = ['1m', '5m', '15m', '1h', '4h', '1d'];
export const POPULAR_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'CUSTOM'];

export const STRATEGY_PARAM_KEYS = {
    'SMA Crossover': ['fast_period', 'slow_period'],
    'Mean Reversion': ['bb_period', 'bb_std', 'rsi_period', 'rsi_oversold', 'rsi_overbought'],
    'RSI': ['period', 'oversold', 'overbought'],
    'MACD': ['fast_period', 'slow_period', 'signal_period'],
    'Bollinger Breakout': ['bb_period', 'bb_std', 'volume_factor'],
    'Momentum': ['roc_period', 'rsi_period', 'rsi_min', 'rsi_max'],
    'DCA Dip': ['ema_long', 'ema_short']
};
