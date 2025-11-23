import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from backtest import Backtester
from strategies.mean_reversion import MeanReversion
from strategies.sma_crossover import SMACrossover
from strategies.macd import MACDStrategy
from strategies.rsi import RSIStrategy
import config
from database import DuckDBHandler
from optimizer import Optimizer

# --- Configuration ---
STRATEGY_CONFIG = {
    "Mean Reversion": {
        "class": MeanReversion,
        "description": "Buys when price is low (oversold) and sells when high (overbought) relative to Bollinger Bands.",
        "params": [
            {"name": "bb_length", "label": "BB Length", "type": "slider", "min": 10, "max": 50, "default": 20, "help": "Period for Bollinger Bands SMA. Typical: 20."},
            {"name": "bb_std", "label": "BB Std Dev", "type": "slider", "min": 1.0, "max": 4.0, "step": 0.1, "default": 2.0, "help": "Standard Deviations for the bands. Typical: 2.0."},
            {"name": "rsi_length", "label": "RSI Length", "type": "slider", "min": 5, "max": 30, "default": 14, "help": "Lookback period for RSI. Typical: 14."},
            {"name": "rsi_buy", "label": "RSI Buy Threshold", "type": "slider", "min": 10, "max": 50, "default": 30, "help": "RSI level to trigger a BUY (Oversold). Typical: 30."},
            {"name": "rsi_sell", "label": "RSI Sell Threshold", "type": "slider", "min": 50, "max": 90, "default": 70, "help": "RSI level to trigger a SELL (Overbought). Typical: 70."},
        ],
        "presets": {
            "Standard": {"bb_length": 20, "bb_std": 2.0, "rsi_length": 14, "rsi_buy": 30, "rsi_sell": 70},
            "Aggressive": {"bb_length": 20, "bb_std": 1.5, "rsi_length": 7, "rsi_buy": 40, "rsi_sell": 60},
            "Conservative": {"bb_length": 30, "bb_std": 2.5, "rsi_length": 14, "rsi_buy": 20, "rsi_sell": 80},
        },
        "opt_ranges": {
            "bb_length": (10, 50, 5),
            "bb_std": [2.0],
            "rsi_length": (5, 25, 2),
            "rsi_buy": [30],
            "rsi_sell": [70]
        }
    },
    "SMA Crossover": {
        "class": SMACrossover,
        "description": "Trend following. Buys when short-term average crosses above long-term average.",
        "params": [
            {"name": "short_window", "label": "Short Window", "type": "slider", "min": 2, "max": 50, "default": 10, "help": "Period for the fast moving average."},
            {"name": "long_window", "label": "Long Window", "type": "slider", "min": 5, "max": 200, "default": 30, "help": "Period for the slow moving average."},
        ],
        "presets": {
            "Standard": {"short_window": 10, "long_window": 30},
            "Scalping": {"short_window": 5, "long_window": 15},
            "Swing": {"short_window": 20, "long_window": 50},
            "Golden Cross": {"short_window": 50, "long_window": 200},
        },
        "opt_ranges": {
            "short_window": (5, 30, 5),
            "long_window": (20, 100, 10)
        }
    },
    "MACD": {
        "class": MACDStrategy,
        "description": "Momentum strategy. Buys on bullish MACD crossovers.",
        "params": [
            {"name": "fast", "label": "Fast Period", "type": "slider", "min": 5, "max": 50, "default": 12, "help": "Period for the fast EMA. Typical: 12."},
            {"name": "slow", "label": "Slow Period", "type": "slider", "min": 10, "max": 100, "default": 26, "help": "Period for the slow EMA. Typical: 26."},
            {"name": "signal", "label": "Signal Period", "type": "slider", "min": 5, "max": 50, "default": 9, "help": "Period for the Signal Line EMA. Typical: 9."},
        ],
        "presets": {
            "Standard": {"fast": 12, "slow": 26, "signal": 9},
            "Fast": {"fast": 8, "slow": 21, "signal": 5},
            "Slow": {"fast": 24, "slow": 52, "signal": 18},
        },
        "opt_ranges": {
            "fast": (8, 20, 2),
            "slow": (20, 40, 2),
            "signal": [9]
        }
    },
    "RSI": {
        "class": RSIStrategy,
        "description": "Momentum oscillator. Buys when oversold (<30) and sells when overbought (>70).",
        "params": [
            {"name": "period", "label": "RSI Period", "type": "slider", "min": 5, "max": 30, "default": 14, "help": "Lookback period for RSI. Typical: 14."},
            {"name": "overbought", "label": "Overbought", "type": "slider", "min": 50, "max": 90, "default": 70, "help": "RSI level to trigger a SELL. Typical: 70."},
            {"name": "oversold", "label": "Oversold", "type": "slider", "min": 10, "max": 50, "default": 30, "help": "RSI level to trigger a BUY. Typical: 30."},
        ],
        "presets": {
            "Standard": {"period": 14, "oversold": 30, "overbought": 70},
            "Sensitive": {"period": 7, "oversold": 20, "overbought": 80},
            "Trend": {"period": 21, "oversold": 40, "overbought": 60},
        },
        "opt_ranges": {
            "period": (5, 25, 2),
            "oversold": (20, 40, 5),
            "overbought": [70]
        }
    }
}

# --- Page Config ---
st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")
st.title("🤖 Trading Bot Dashboard")

# --- Leaderboard Section ---
if st.checkbox("Show Leaderboard", value=True):
    db = DuckDBHandler()
    results_df = db.get_leaderboard()
    
    if not results_df.empty:
        st.dataframe(results_df, use_container_width=True)
        if st.button("Clear Leaderboard"):
            db.clear_leaderboard()
            st.rerun()
    else:
        st.info("No results yet. Run a backtest to populate the leaderboard.")
st.markdown("---")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")

symbol = st.sidebar.text_input("Symbol", "BTC/USDT", help="The trading pair to backtest.")
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=0, help="Candlestick duration.")
days = st.sidebar.slider("Days to Backtest", 1, 30, 1, help="Historical data duration.")

st.sidebar.subheader("Strategy Parameters")
strategy_name = st.sidebar.selectbox("Strategy", list(STRATEGY_CONFIG.keys()))
strategy_info = STRATEGY_CONFIG[strategy_name]

st.sidebar.info(strategy_info["description"])

# Presets
presets = strategy_info.get("presets", {})
if presets:
    preset_names = list(presets.keys()) + ["Custom"]
    selected_preset = st.sidebar.selectbox("Preset", preset_names, index=0)
    
    # Apply Preset
    if selected_preset != "Custom":
        preset_vals = presets[selected_preset]
        # Store in session state to update sliders
        for k, v in preset_vals.items():
            st.session_state[f"{strategy_name}_{k}"] = v

# Dynamic Parameters
params = {}
for param in strategy_info["params"]:
    key = f"{strategy_name}_{param['name']}"
    
    # Initialize default if not in session state
    if key not in st.session_state:
        st.session_state[key] = param["default"]
        
    # Create widget
    if param["type"] == "slider":
        val = st.sidebar.slider(
            param["label"], 
            min_value=param["min"], 
            max_value=param["max"], 
            step=param.get("step", 1), 
            key=key,
            help=param.get("help")
        )
        params[param["name"]] = val

# Initialize Strategy
strategy_class = strategy_info["class"]
strategy = strategy_class(**params)

# --- Backtest Execution ---
if st.sidebar.button("Run Backtest"):
    with st.spinner("Fetching data and running simulation..."):
        bt = Backtester(symbol, timeframe, strategy, days=days)
        bt.fetch_data()
        
        if bt.df is not None and not bt.df.empty:
            bt.run()
            
            # Metrics
            total_return = ((bt.balance - 1000) / 1000) * 100
            wins = [t for t in bt.trades if t['pnl'] > 0]
            win_rate = (len(wins) / len(bt.trades)) * 100 if bt.trades else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Final Balance", f"${bt.balance:.2f}")
            col2.metric("Total Return", f"{total_return:.2f}%", delta_color="normal")
            col3.metric("Win Rate", f"{win_rate:.2f}%")
            col4.metric("Total Trades", len(bt.trades))
            
            # Save Results
            db = DuckDBHandler()
            result = {
                'strategy': strategy_name,
                'params': params,
                'return': total_return,
                'win_rate': win_rate,
                'trades': len(bt.trades),
                'final_balance': bt.balance
            }
            db.save_result(result)
            st.success("Result saved to Leaderboard! 🏆")
            
            # Visualization
            df = bt.df
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Price'))
            
            # Add Indicators (Generic attempt to find common indicators)
            if 'bb_upper' in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_upper'], name='BB Upper', line=dict(color='gray', width=1)))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_lower'], name='BB Lower', line=dict(color='gray', width=1), fill='tonexty'))
            if 'ema_200' in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema_200'], name='EMA 200', line=dict(color='orange', width=2)))
                
            # Trades
            for trade in bt.trades:
                color = 'green' if trade['pnl'] > 0 else 'red'
                fig.add_trace(go.Scatter(
                    x=[trade['time']], 
                    y=[df.loc[df['timestamp'] == trade['time'], 'close'].values[0]],
                    mode='markers',
                    marker=dict(symbol='circle', size=10, color=color),
                    name='Trade Exit',
                    showlegend=False
                ))
            
            fig.update_layout(title=f"{symbol} Backtest Results", xaxis_title="Time", yaxis_title="Price", height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade List
            st.subheader("Trade History")
            if bt.trades:
                st.dataframe(pd.DataFrame(bt.trades))
            else:
                st.info("No trades executed.")
        else:
            st.error(f"No data found. Error: {bt.error}")

# --- Optimization Mode ---
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Optimization")
if st.sidebar.checkbox("Enable Optimization Mode"):
    st.header("🔬 Strategy Optimization")
    
    opt_ranges = strategy_info.get("opt_ranges", {})
    final_ranges = {}
    
    st.subheader("Parameter Ranges")
    for param_name, range_def in opt_ranges.items():
        if isinstance(range_def, list):
            # Fixed value (no range)
            final_ranges[param_name] = range_def
        elif isinstance(range_def, tuple):
            # Range (min, max, step)
            min_val, max_val, step = range_def
            # Allow user to adjust range
            user_range = st.slider(f"{param_name} Range", min_val, max_val * 2, (min_val, max_val), step=step)
            final_ranges[param_name] = range(user_range[0], user_range[1] + 1, step)
            
    if st.button("Run Optimization"):
        with st.spinner("Optimizing..."):
            bt_temp = Backtester(symbol, timeframe, strategy, days=days)
            bt_temp.fetch_data()
            
            if bt_temp.df is not None:
                opt = Optimizer(symbol, timeframe, strategy_class, bt_temp.df)
                results = opt.optimize(final_ranges)
                
                st.success(f"Optimization Complete! Tested {len(results)} combinations.")
                st.dataframe(results.style.highlight_max(axis=0, subset=['return', 'win_rate']), use_container_width=True)
                
                best = results.iloc[0]
                st.info(f"🏆 Best Params: {best['params']} | Return: {best['return']:.2f}%")
            else:
                st.error(f"Could not fetch data for optimization. Error: {bt_temp.error}")
else:
    st.info("Adjust parameters and click 'Run Backtest' to start.")
