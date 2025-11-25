import time
import logging
import sys
import threading
from .exchange.client import ExchangeClient
from .strategies.sma_crossover import SMACrossover
from . import config

# Global event to control bot execution
running_event = threading.Event()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TradingBot")

def main():
    logger.info("Starting Trading Bot...")
    
    # Initialize Exchange Client
    if getattr(config, 'DRY_RUN', False):
        from .exchange.paper import PaperExchange
        logger.info("⚠️ DRY RUN MODE ENABLED: Using Paper Exchange")
        client = PaperExchange(config.API_KEY, config.API_SECRET)
    else:
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
    
    # Set Leverage
    client.set_leverage(config.SYMBOL, config.LEVERAGE)
    
    # Initialize Strategy
    strategy_name = getattr(config, 'STRATEGY', 'mean_reversion')
    logger.info(f"Selected Strategy: {strategy_name}")

    if strategy_name == 'mean_reversion':
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion()
    elif strategy_name == 'sma_crossover':
        from .strategies.sma_crossover import SMACrossover
        strategy = SMACrossover()
    elif strategy_name == 'combined':
        from .strategies.combined import CombinedStrategy
        strategy = CombinedStrategy()
    elif strategy_name == 'macd':
        from .strategies.macd import MACDStrategy
        strategy = MACDStrategy()
    elif strategy_name == 'rsi':
        from .strategies.rsi import RSIStrategy

    while True:
        try:
            if not running_event.is_set():
                # Wait for the event to be set
                running_event.wait()
                logger.info("▶️ Bot resumed trading.")

            logger.info("Fetching market data...")
            # Fetch OHLCV data
            df = client.fetch_ohlcv(config.SYMBOL, config.TIMEFRAME)
            
            if df is not None:
                # Generate Signal
                result = strategy.generate_signal(df)
                signal = result['signal']
                score = result['score']
                details = result['details']
                
                current_price = df.iloc[-1]['close']
                
                # --- Multi-Timeframe Analysis (Trend Filter) ---
                if trend_filter:
                    try:
                        trend, price_high, ema_200 = trend_filter.check_trend()
                        logger.info(f"Trend ({config.HIGHER_TIMEFRAME}): {trend} | Price: {price_high} | EMA 200: {ema_200:.2f}")
                        
                        # Apply Filter
                        if signal == 'BUY' and trend == 'DOWNTREND':
                            logger.info("Signal is BUY but Trend is DOWNTREND. Filtering signal.")
                            signal = 'HOLD'
                        elif signal == 'SELL' and trend == 'UPTREND':
                            logger.info("Signal is SELL but Trend is UPTREND. Filtering signal.")
                            signal = 'HOLD'
                    except Exception as e:
                        logger.error(f"TrendFilter check failed: {e}")
                # -----------------------------------------------
                
                # Log Indicators
                # sma_short = df.iloc[-1].get('sma_short', 0)
                # sma_long = df.iloc[-1].get('sma_long', 0)
                # rsi = df.iloc[-1].get('rsi', 0)
                # macd = df.iloc[-1].get('macd', 0)
                
                # logger.info(f"Price: {current_price} | SMA: {details.get('sma', 'N/A')} | RSI: {details.get('rsi', 'N/A')} | MACD: {details.get('macd', 'N/A')}")
                logger.info(f"Price: {current_price} | Signal: {signal} | Score: {score}/3")
                logger.info(f"Details: {details}")
                
                # Fetch current position
                position = client.fetch_position(config.SYMBOL)
                current_pos_size = position.get('size', 0.0)
                current_pos_side = position.get('side', 'None') # 'Buy', 'Sell', 'None'
                
                # break # REMOVED: This break was killing the bot after one loop!
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            # Add a small delay to avoid rapid error loops
            time.sleep(10)

if __name__ == "__main__":
    main()
