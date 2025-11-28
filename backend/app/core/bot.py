import time
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from .exchange.client import ExchangeClient
from .strategies.sma_crossover import SMACrossover
from . import config

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            "logs/trading_bot.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5  # Keep 5 old files
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TradingBot")

def run_bot_instance(user_id: int, strategy_config: dict, running_event: threading.Event):
    """
    Run a bot instance for a specific user.
    
    Args:
        user_id: The user ID this bot belongs to
        strategy_config: Dictionary containing strategy configuration
        running_event: Thread event to control pause/resume
    """
    logger.info(f"Starting bot instance for user {user_id} with strategy: {strategy_config.get('STRATEGY', 'unknown')}")
    
    # Extract config values with defaults
    symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
    timeframe = strategy_config.get('TIMEFRAME', '1m')
    amount_usdt = strategy_config.get('AMOUNT_USDT', 10.0)
    strategy_name = strategy_config.get('STRATEGY', 'mean_reversion')
    strategy_params = strategy_config.get('STRATEGY_PARAMS', {})
    dry_run = strategy_config.get('DRY_RUN', True)
    
    # Load API keys for this user from database
    from .database import DuckDBHandler
    from .encryption import EncryptionHelper
    
    db = DuckDBHandler()
    encryption = EncryptionHelper()
    
    # Try to get user's API keys
    api_key_data = db.get_api_key(user_id, 'bybit')
    
    if api_key_data:
        # Decrypt user's API keys
        api_key = encryption.decrypt(api_key_data['api_key_encrypted'])
        api_secret = encryption.decrypt(api_key_data['api_secret_encrypted'])
        logger.info(f"✓ Loaded encrypted API keys for user {user_id}")
    else:
        # Fallback to global config (for backward compatibility)
        api_key = config.API_KEY
        api_secret = config.API_SECRET
        logger.warning(f"⚠️ No encrypted API keys found for user {user_id}, using global config")
    
    if not api_key or not api_secret:
        logger.error(f"❌ No API keys available for user {user_id}")
        raise ValueError(f"Missing API credentials for user {user_id}")
    
    # Initialize Exchange Client
    if dry_run:
        from .exchange.paper import PaperExchange
        logger.info(f"⚠️ DRY RUN MODE for user {user_id}")
        client = PaperExchange(api_key, api_secret)
    else:
        client = ExchangeClient(api_key, api_secret, demo=config.DEMO)
    
    # Test connectivity
    try:
        balance = client.fetch_balance()
        logger.info(f"✓ User {user_id} connected to exchange")
    except Exception as e:
        logger.error(f"❌ User {user_id} failed to connect: {e}")
        raise ConnectionError(f"Cannot connect to exchange: {e}")
    
    # Set Leverage
    client.set_leverage(symbol, config.LEVERAGE)
    
    # Initialize Strategy
    logger.info(f"Initializing strategy '{strategy_name}' for user {user_id}")
    
    if strategy_name == 'mean_reversion':
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion(**strategy_params)
    elif strategy_name == 'sma_crossover':
        strategy = SMACrossover(**strategy_params)
    elif strategy_name == 'combined':
        from .strategies.combined import CombinedStrategy
        strategy = CombinedStrategy(**strategy_params)
    elif strategy_name == 'macd':
        from .strategies.macd import MACDStrategy
        strategy = MACDStrategy(**strategy_params)
    elif strategy_name == 'rsi':
        from .strategies.rsi import RSIStrategy
        strategy = RSIStrategy(**strategy_params)
    else:
        logger.warning(f"Unknown strategy '{strategy_name}' for user {user_id}. Using Mean Reversion.")
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion(**strategy_params)

    # Initialize Notifier
    from .notifier import TelegramNotifier
    notifier = TelegramNotifier()
    notifier.send_message(f"🚀 *Bot Started for User {user_id}*\nStrategy: {strategy_name}")

    logger.info(f"✓ User {user_id} bot initialized. Entering trading loop...")

    # Main trading loop - simplified version
    while True:
        try:
            if not running_event.is_set():
                running_event.wait()
                logger.info(f"▶️ User {user_id} bot resumed")

            # Fetch market data
            try:
                df = client.fetch_ohlcv(symbol, timeframe, limit=100)
            except Exception as e:
                logger.error(f"User {user_id} OHLCV fetch failed: {e}")
                time.sleep(config.LOOP_DELAY_SECONDS)
                continue

            # Get current position
            position = client.fetch_position(symbol)
            position_size = position.get('size', 0.0)

            # Generate signal
            signal = strategy.generate_signal(df)

            # Simple trading logic (enter/exit based on signal)
            if position_size == 0 and signal in ['long', 'short']:
                # Open position
                ticker = client.fetch_ticker(symbol)
                current_price = ticker['last']
                amount = amount_usdt / current_price
                side = 'buy' if signal == 'long' else 'sell'
                
                
                try:
                    client.create_order(symbol=symbol, type='market', side=side, amount=amount)
                    # Log trade to database
                    trade_data = {
                        'symbol': symbol,
                        'side': side,
                        'price': current_price,
                        'amount': amount,
                        'type': 'OPEN',
                        'pnl': 0.0,
                        'strategy': strategy_name
                    }
                    db.save_trade(trade_data, user_id=user_id)
                    logger.info(f"✓ User {user_id}: {signal} entry at {current_price}")
                except Exception as e:
                    logger.error(f"User {user_id} order failed: {e}")

            elif position_size > 0:
                # Check exit (simplified - just on opposite signal)
                position_side = position.get('side')
                if (position_side == 'long' and signal == 'short') or (position_side == 'short' and signal == 'long'):
                    ticker = client.fetch_ticker(symbol)
                    side = 'sell' if position_side == 'long' else 'buy'
                    try:
                        client.create_order(symbol=symbol, type='market', side=side, amount=position_size)
                        logger.info(f"✓ User {user_id}: Closed position")
                    except Exception as e:
                        logger.error(f"User {user_id} close failed: {e}")

            time.sleep(config.LOOP_DELAY_SECONDS)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"User {user_id} bot error: {e}")
            time.sleep(10)
    
    logger.info(f"Bot instance for user {user_id} terminated")


def main():
    """Original main function - kept for backward compatibility."""
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
    strategy_params = getattr(config, 'STRATEGY_PARAMS', {})
    logger.info(f"Selected Strategy: {strategy_name} with params: {strategy_params}")

    if strategy_name == 'mean_reversion':
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion(**strategy_params)
    elif strategy_name == 'sma_crossover':
        from .strategies.sma_crossover import SMACrossover
        strategy = SMACrossover(**strategy_params)
    elif strategy_name == 'combined':
        from .strategies.combined import CombinedStrategy
        strategy = CombinedStrategy(**strategy_params)
    elif strategy_name == 'macd':
        from .strategies.macd import MACDStrategy
        strategy = MACDStrategy(**strategy_params)
    elif strategy_name == 'rsi':
        from .strategies.rsi import RSIStrategy
        strategy = RSIStrategy(**strategy_params)
    else:
        logger.warning(f"Unknown strategy '{strategy_name}'. Defaulting to Mean Reversion.")
        from .strategies.mean_reversion import MeanReversion
        strategy = MeanReversion(**strategy_params)

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

    # Initialize Edge Positioning
    from .edge import Edge
    edge = Edge()
    if edge.enabled:
        logger.info(f"Edge Positioning Enabled (Window: {edge.window}, Min Exp: {edge.min_expectancy})")

    # Initialize Notifier
    from .notifier import TelegramNotifier
    notifier = TelegramNotifier()
    notifier.send_message("🚀 *Trading Bot Started*")

    logger.info("Bot initialized. Waiting for start signal...")

    # Track position duration
    position_start_time = None
    
    # Track Open Orders (Limit Order Management)
    open_order = None # {'id': '...', 'time': 1234567890, 'side': 'Buy', 'type': 'limit'}

    while True:
        try:
            if not running_event.is_set():
                # Wait for the event to be set
                running_event.wait()
                logger.info("▶️ Bot resumed trading.")
                notifier.send_message("▶️ *Bot Resumed*")

            # --- Market Scanner Logic ---
            if scanner and (time.time() - last_scan_time > config.SCANNER_INTERVAL_MINUTES * 60):
                # Only scan if no position is open
                position = client.fetch_position(config.SYMBOL)
                if position.get('size', 0.0) == 0 and open_order is None:
                    new_symbol = scanner.get_best_pair()
                    if new_symbol and new_symbol != config.SYMBOL:
                        logger.info(f"🔄 Switching symbol from {config.SYMBOL} to {new_symbol}")
                        notifier.send_message(f"🔄 Switching symbol to `{new_symbol}`")
                        config.SYMBOL = new_symbol
                        # Re-initialize trend filter if needed
                        if trend_filter:
                            trend_filter.symbol = new_symbol
                    last_scan_time = time.time()
            # ----------------------------

            # --- Limit Order Management ---
            if open_order:
                # Check if order is still open
                # In a real bot, we'd fetch order status from exchange. 
                # For simplicity/Paper, we assume it fills if price crosses, or we check timeout.
                
                # Check Timeout
                if time.time() - open_order['time'] > config.ORDER_TIMEOUT_SECONDS:
                    logger.warning(f"⏳ Order {open_order['id']} timed out! Cancelling and forcing Market Order.")
                    
                    # Cancel Order
                    try:
                        client.cancel_order(open_order['id'], config.SYMBOL)
                    except Exception as e:
                        logger.error(f"Failed to cancel order: {e}")
                    
                    # Force Market Order
                    try:
                        # Fetch current price for amount calculation
                        ticker = client.fetch_ticker(config.SYMBOL)
                        current_price = ticker['last']
                        
                        amount = config.AMOUNT_USDT / current_price
                        
                        order = client.create_order(
                            symbol=config.SYMBOL,
                            side=open_order['side'],
                            amount=amount,
                            order_type='market', # Force Market
                            take_profit_pct=config.TAKE_PROFIT_PCT,
                            stop_loss_pct=config.STOP_LOSS_PCT
                        )
                        logger.info(f"🚀 Forced Market Order placed: {order}")
                        
                        # Log Trade (Simplified)
                        fee = amount * current_price * config.TAKER_FEE_PCT
                        trade_data = {
                            'symbol': config.SYMBOL,
                            'side': open_order['side'],
                            'price': current_price,
                            'amount': amount,
                            'type': 'OPEN',
                            'pnl': -fee,
                            'strategy': strategy_name,
                            'fee': fee,
                            'leverage': config.LEVERAGE
                        }
                        db.save_trade(trade_data, user_id=user_id)
                        notifier.send_trade_alert(trade_data)
                        
                        # Reset
                        open_order = None
                        position_start_time = time.time()
                        
                    except Exception as e:
                        logger.error(f"Failed to place forced market order: {e}")
                        notifier.send_error(f"Failed to place forced market order: {e}")
                
                # If not timed out, we skip the rest of the loop to wait for fill
                # In a real bot, we'd check if it filled here.
                # For PaperExchange, it usually fills instantly, so open_order might be cleared immediately if we checked.
                # But let's assume we wait.
                time.sleep(1) 
                continue 
            # ------------------------------

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
                        # Fetch higher timeframe data
                        df_htf = client.fetch_ohlcv(config.SYMBOL, config.HIGHER_TIMEFRAME)
                        trend, price_high, ema_200 = trend_filter.check_trend(df_htf)
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
                
                # --- Edge Positioning Check ---
                # Only check if we are looking to open a new position (size == 0)
                if current_pos_size == 0 and edge.enabled:
                    if not edge.check_edge(db):
                        logger.info("⛔ Edge is negative. Skipping new trade entries.")
                        # We continue the loop but we must ensure we don't enter new trades.
                        # We can set signal to HOLD to prevent entry.
                        signal = 'HOLD'
                # ------------------------------
                
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
                    
                    # Check Activation
                    entry_price = float(position.get('avgPrice', current_price))
                    if strategy.highest_price >= entry_price * (1 + config.TRAILING_STOP_ACTIVATION_PCT):
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
                    
                    # Check Activation
                    entry_price = float(position.get('avgPrice', current_price))
                    if strategy.lowest_price <= entry_price * (1 - config.TRAILING_STOP_ACTIVATION_PCT):
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
                        trade_data = {
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_SHORT',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': 0.0 - fee,  # Exchange PnL + Fee deduction (simplified)
                            'strategy': strategy_name,
                            'fee': fee,
                            'leverage': config.LEVERAGE
                        }
                        db.save_trade(trade_data, user_id=user_id)
                        notifier.send_trade_alert(trade_data)
                    
                    # Open new LONG position
                    logger.info(f"Opening LONG position | Signal Score: {score}")
                    try:
                        # Determine Order Type and Price
                        order_type = getattr(config, 'ORDER_TYPE', 'market')
                        price = None
                        if order_type == 'limit':
                            # Get Best Bid
                            ticker = client.fetch_ticker(config.SYMBOL)
                            price = ticker['bid']
                            logger.info(f"🎯 Placing LIMIT BUY at {price}")
                        
                        order = client.create_order(
                            symbol=config.SYMBOL,
                            side='Buy',
                            amount=config.AMOUNT_USDT / (price if price else current_price),
                            order_type=order_type,
                            price=price,
                            take_profit_pct=config.TAKE_PROFIT_PCT,
                            stop_loss_pct=config.STOP_LOSS_PCT
                        )
                        logger.info(f"LONG order placed: {order}")
                        
                        if order_type == 'limit':
                            # Track Open Order
                            open_order = {
                                'id': order['id'],
                                'time': time.time(),
                                'side': 'Buy',
                                'type': 'limit'
                            }
                        else:
                            # Market Order filled immediately (conceptually)
                            # Initialize Trailing Stop
                            strategy.highest_price = current_price
                            position_start_time = time.time()
                            
                            # Calculate Fee
                            trade_amount = config.AMOUNT_USDT / current_price
                            fee = trade_amount * current_price * config.TAKER_FEE_PCT
                            
                            # Log trade to database
                            trade_data = {
                                'symbol': config.SYMBOL,
                                'side': 'Buy',
                                'price': current_price,
                                'amount': trade_amount,
                                'type': 'OPEN',
                                'pnl': -fee,
                                'strategy': strategy_name,
                                'fee': fee,
                                'leverage': config.LEVERAGE
                            }
                            db.save_trade(trade_data, user_id=user_id)
                            notifier.send_trade_alert(trade_data)

                    except Exception as e:
                        logger.error(f"Failed to open LONG: {e}")
                        notifier.send_error(f"Failed to open LONG: {e}")
                
                elif signal == 'SELL' and current_pos_side != 'Sell':
                    # Close long if exists
                    if current_pos_side == 'Buy':
                        logger.info("Closing LONG position before opening SHORT")
                        client.close_position(config.SYMBOL)
                        
                        # Calculate Fee
                        fee = current_pos_size * current_price * config.TAKER_FEE_PCT
                        
                        # Log trade to database
                        trade_data = {
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_LONG',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': 0.0 - fee, # Exchange PnL + Fee deduction
                            'strategy': strategy_name,
                            'fee': fee,
                            'leverage': config.LEVERAGE
                        }
                        db.save_trade(trade_data, user_id=user_id)
                        notifier.send_trade_alert(trade_data)
                    
                    # Open new SHORT position
                    logger.info(f"Opening SHORT position | Signal Score: {score}")
                    try:
                        # Determine Order Type and Price
                        order_type = getattr(config, 'ORDER_TYPE', 'market')
                        price = None
                        if order_type == 'limit':
                            # Get Best Ask
                            ticker = client.fetch_ticker(config.SYMBOL)
                            price = ticker['ask']
                            logger.info(f"🎯 Placing LIMIT SELL at {price}")

                        order = client.create_order(
                            symbol=config.SYMBOL,
                            side='Sell',
                            amount=config.AMOUNT_USDT / (price if price else current_price),
                            order_type=order_type,
                            price=price,
                            take_profit_pct=config.TAKE_PROFIT_PCT,
                            stop_loss_pct=config.STOP_LOSS_PCT
                        )
                        logger.info(f"SHORT order placed: {order}")
                        
                        if order_type == 'limit':
                            # Track Open Order
                            open_order = {
                                'id': order['id'],
                                'time': time.time(),
                                'side': 'Sell',
                                'type': 'limit'
                            }
                        else:
                            # Initialize Trailing Stop
                            strategy.lowest_price = current_price
                            position_start_time = time.time()
                            
                            # Calculate Fee
                            trade_amount = config.AMOUNT_USDT / current_price
                            fee = trade_amount * current_price * config.TAKER_FEE_PCT
                            
                            # Log trade to database
                            trade_data = {
                                'symbol': config.SYMBOL,
                                'side': 'Sell',
                                'price': current_price,
                                'amount': trade_amount,
                                'type': 'OPEN',
                                'pnl': -fee,
                                'strategy': strategy_name,
                                'fee': fee,
                                'leverage': config.LEVERAGE
                            }
                            db.save_trade(trade_data, user_id=user_id)
                            notifier.send_trade_alert(trade_data)

                    except Exception as e:
                        logger.error(f"Failed to open SHORT: {e}")
                        notifier.send_error(f"Failed to open SHORT: {e}")
                
            # Sleep to prevent API spam (configurable delay)
            time.sleep(config.LOOP_DELAY_SECONDS)
                
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            notifier.send_error(f"Bot Loop Error: {e}")
            # Add a small delay to avoid rapid error loops
            time.sleep(10)

if __name__ == "__main__":
    main()
