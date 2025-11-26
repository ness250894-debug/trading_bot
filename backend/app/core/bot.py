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
        strategy = RSIStrategy()
    else:
        logger.warning(f"Unknown strategy '{strategy_name}'. Defaulting to Mean Reversion.")
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion()

    # Initialize Trend Filter with error handling
    try:
        from .strategies.filters import TrendFilter
        trend_filter = TrendFilter(client, config.SYMBOL, config.HIGHER_TIMEFRAME)
    except Exception as e:
        logger.error(f"Failed to initialize TrendFilter: {e}")
        trend_filter = None

    # Initialize Database for Trade Logging
    from .database import DuckDBHandler
    db = DuckDBHandler()

    # Initialize Scanner
    scanner = None
    last_scan_time = 0
    if getattr(config, 'SCANNER_ENABLED', False):
        from .scanner import Scanner
        scanner = Scanner(client)
        logger.info("Market Scanner Enabled")

    logger.info("Bot initialized. Waiting for start signal...")

    # Track position duration
    position_start_time = None

    while True:
        try:
            if not running_event.is_set():
                # Wait for the event to be set
                running_event.wait()
                logger.info("▶️ Bot resumed trading.")

            # --- Market Scanner Logic ---
            if scanner and (time.time() - last_scan_time > config.SCANNER_INTERVAL_MINUTES * 60):
                # Only scan if no position is open
                position = client.fetch_position(config.SYMBOL)
                if position.get('size', 0.0) == 0:
                    new_symbol = scanner.get_best_pair()
                    if new_symbol and new_symbol != config.SYMBOL:
                        logger.info(f"🔄 Switching symbol from {config.SYMBOL} to {new_symbol}")
                        config.SYMBOL = new_symbol
                        # Re-initialize trend filter if needed
                        if trend_filter:
                            trend_filter.symbol = new_symbol
                    last_scan_time = time.time()
            # ----------------------------

            logger.info(f"Fetching market data for {config.SYMBOL}...")
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
                
                logger.info(f"Price: {current_price} | Signal: {signal} | Score: {score}/3")
                logger.info(f"Details: {details}")
                
                # Fetch current position
                position = client.fetch_position(config.SYMBOL)
                current_pos_size = position.get('size', 0.0)
                current_pos_side = position.get('side', 'None') # 'Buy', 'Sell', 'None'
                
                logger.info(f"Current Position: {current_pos_side} | Size: {current_pos_size}")
                
                # Update Position Start Time
                if current_pos_size > 0 and position_start_time is None:
                    position_start_time = time.time() # Start tracking
                elif current_pos_size == 0:
                    position_start_time = None # Reset
                
                # Execute Trading Logic
                
                # --- Smart ROI Logic ---
                if current_pos_size > 0 and position_start_time:
                    duration_minutes = (time.time() - position_start_time) / 60
                    
                    # Calculate current unrealized PnL %
                    if current_pos_side == 'Buy':
                        pnl_pct = (current_price - float(position.get('avgPrice', current_price))) / float(position.get('avgPrice', current_price))
                    else:
                        pnl_pct = (float(position.get('avgPrice', current_price)) - current_price) / float(position.get('avgPrice', current_price))
                    
                    # Check against Smart ROI table
                    for time_threshold, target_roi in sorted(config.SMART_ROI.items()):
                        if duration_minutes >= time_threshold:
                            if pnl_pct >= target_roi:
                                logger.info(f"🧠 Smart ROI Triggered! Duration: {duration_minutes:.1f}m, PnL: {pnl_pct*100:.2f}%, Target: {target_roi*100}%")
                                signal = 'SELL' if current_pos_side == 'Buy' else 'BUY'
                                details['reason'] = 'Smart ROI'
                                break
                # -----------------------

                # --- Trailing Stop Logic ---
                if current_pos_side == 'Buy':
                    # Update highest price for Long
                    if not hasattr(strategy, 'highest_price') or current_price > strategy.highest_price:
                        strategy.highest_price = current_price
                    
                    # Check Trailing Stop
                    stop_price = strategy.highest_price * (1 - config.TRAILING_STOP_PCT)
                    if current_price < stop_price:
                        logger.info(f"📉 Trailing Stop Triggered for LONG! Current: {current_price}, High: {strategy.highest_price}, Stop: {stop_price}")
                        signal = 'SELL' # Force sell signal
                        details['reason'] = 'Trailing Stop'

                elif current_pos_side == 'Sell':
                    # Update lowest price for Short
                    if not hasattr(strategy, 'lowest_price') or current_price < strategy.lowest_price:
                        strategy.lowest_price = current_price
                    
                    # Check Trailing Stop
                    stop_price = strategy.lowest_price * (1 + config.TRAILING_STOP_PCT)
                    if current_price > stop_price:
                        logger.info(f"📈 Trailing Stop Triggered for SHORT! Current: {current_price}, Low: {strategy.lowest_price}, Stop: {stop_price}")
                        signal = 'BUY' # Force buy signal (to cover short)
                        details['reason'] = 'Trailing Stop'
                else:
                    # Reset tracking when no position
                    strategy.highest_price = 0
                    strategy.lowest_price = float('inf')
                # ---------------------------

                if signal == 'BUY' and current_pos_side != 'Buy':
                    # Close short if exists
                    if current_pos_side == 'Sell':
                        logger.info("Closing SHORT position before opening LONG")
                        client.close_position(config.SYMBOL)
                        
                        # Calculate Fee
                        fee = current_pos_size * current_price * config.TAKER_FEE_PCT
                        
                        # Log trade to database
                        db.save_trade({
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_SHORT',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': 0.0 - fee,  # Exchange PnL + Fee deduction (simplified)
                            'strategy': strategy_name,
                            'fee': fee
                        })
                    
                    # Open new LONG position
                    logger.info(f"Opening LONG position | Signal Score: {score}")
                    try:
                        order = client.create_order(
                            symbol=config.SYMBOL,
                            side='Buy',
                            amount=config.AMOUNT_USDT / current_price,
                            take_profit_pct=config.TAKE_PROFIT_PCT,
                            stop_loss_pct=config.STOP_LOSS_PCT
                        )
                        logger.info(f"LONG order placed: {order}")
                        
                        # Initialize Trailing Stop
                        strategy.highest_price = current_price
                        position_start_time = time.time() # Reset start time
                        
                        # Calculate Fee
                        trade_amount = config.AMOUNT_USDT / current_price
                        fee = trade_amount * current_price * config.TAKER_FEE_PCT
                        
                        # Log trade to database
                        db.save_trade({
                            'symbol': config.SYMBOL,
                            'side': 'Buy',
                            'price': current_price,
                            'amount': trade_amount,
                            'type': 'OPEN',
                            'pnl': -fee, # Initial PnL is just the fee
                            'strategy': strategy_name,
                            'fee': fee
                        })
                    except Exception as e:
                        logger.error(f"Failed to open LONG: {e}")
                
                elif signal == 'SELL' and current_pos_side != 'Sell':
                    # Close long if exists
                    if current_pos_side == 'Buy':
                        logger.info("Closing LONG position before opening SHORT")
                        client.close_position(config.SYMBOL)
                        
                        # Calculate Fee
                        fee = current_pos_size * current_price * config.TAKER_FEE_PCT
                        
                        # Log trade to database
                        db.save_trade({
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_LONG',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': 0.0 - fee, # Exchange PnL + Fee deduction
                            'strategy': strategy_name,
                            'fee': fee
                        })
                    
                    # Open new SHORT position
                    logger.info(f"Opening SHORT position | Signal Score: {score}")
                    try:
                        order = client.create_order(
                            symbol=config.SYMBOL,
                            side='Sell',
                            amount=config.AMOUNT_USDT / current_price,
                            take_profit_pct=config.TAKE_PROFIT_PCT,
                            stop_loss_pct=config.STOP_LOSS_PCT
                        )
                        logger.info(f"SHORT order placed: {order}")
                        
                        # Initialize Trailing Stop
                        strategy.lowest_price = current_price
                        position_start_time = time.time() # Reset start time
                        
                        # Calculate Fee
                        trade_amount = config.AMOUNT_USDT / current_price
                        fee = trade_amount * current_price * config.TAKER_FEE_PCT
                        
                        # Log trade to database
                        db.save_trade({
                            'symbol': config.SYMBOL,
                            'side': 'Sell',
                            'price': current_price,
                            'amount': trade_amount,
                            'type': 'OPEN',
                            'pnl': -fee, # Initial PnL is just the fee
                            'strategy': strategy_name,
                            'fee': fee
                        })
                    except Exception as e:
                        logger.error(f"Failed to open SHORT: {e}")
                
            # Sleep to prevent API spam (configurable delay)
            time.sleep(config.LOOP_DELAY_SECONDS)
                
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            # Add a small delay to avoid rapid error loops
            time.sleep(10)

if __name__ == "__main__":
    main()
