import time
import logging
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler

from .exchange import ExchangeClient
from .strategies.sma_crossover import SMACrossover
from . import config
from .resilience import retry, CircuitBreaker

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

def create_strategy(strategy_name: str, strategy_params: dict, user_id: int = None):
    """
    Factory function to create strategy instances.
    
    Args:
        strategy_name: Name of the strategy
        strategy_params: Strategy parameters
        user_id: Optional user ID for logging
    
    Returns:
        Strategy instance
    """
    # Define valid parameters for each strategy
    strategy_param_map = {
        'mean_reversion': ['bb_period', 'bb_std', 'rsi_period', 'rsi_oversold', 'rsi_overbought'],
        'sma_crossover': ['fast_period', 'slow_period'],
        'macd': ['fast', 'slow', 'signal', 'fast_period', 'slow_period', 'signal_period'],
        'rsi': ['period', 'overbought', 'oversold', 'buy_threshold', 'sell_threshold'],
        'bollinger_breakout': ['bb_period', 'bb_std', 'volume_factor'],
        'momentum': ['roc_period', 'rsi_period', 'rsi_min', 'rsi_max'],
        'dca_dip': ['ema_long', 'ema_short'],
        'combined': []  # Combined accepts any kwargs
    }
    
    # Filter parameters to only include valid ones for the selected strategy
    valid_params = strategy_param_map.get(strategy_name, [])
    if valid_params:  # If not combined strategy
        filtered_params = {k: v for k, v in strategy_params.items() if k in valid_params}
        logger.info(f"Filtered params for {strategy_name}: {filtered_params}")
    else:
        filtered_params = strategy_params  # Combined strategy accepts all
    
    # Import and instantiate the appropriate strategy
    if strategy_name == 'mean_reversion':
        from .strategies.mean_reversion import MeanReversion
        return MeanReversion(**filtered_params)
    elif strategy_name == 'sma_crossover':
        return SMACrossover(**filtered_params)
    elif strategy_name == 'combined':
        from .strategies.combined import CombinedStrategy
        return CombinedStrategy(**filtered_params)
    elif strategy_name == 'macd':
        from .strategies.macd import MACDStrategy
        return MACDStrategy(**filtered_params)
    elif strategy_name == 'rsi':
        from .strategies.rsi import RSIStrategy
        return RSIStrategy(**filtered_params)
    elif strategy_name == 'bollinger_breakout':
        from .strategies.bollinger_breakout import BollingerBreakout
        return BollingerBreakout(**filtered_params)
    elif strategy_name == 'momentum':
        from .strategies.momentum import Momentum
        return Momentum(**filtered_params)
    elif strategy_name == 'dca_dip':
        from .strategies.dca_dip import DCADip
        return DCADip(**filtered_params)
    else:
        user_msg = f" for user {user_id}" if user_id else ""
        logger.warning(f"Unknown strategy '{strategy_name}'{user_msg}. Using Mean Reversion.")
        from .strategies.mean_reversion import MeanReversion
        return MeanReversion(**filtered_params)


def run_bot_instance(user_id: int, strategy_config: dict, running_event: threading.Event, runtime_state: dict = None):
    """
    Run a bot instance for a specific user.
    
    Args:
        user_id: The user ID this bot belongs to
        strategy_config: Dictionary containing strategy configuration
        running_event: Thread event to control pause/resume
        runtime_state: Dictionary to share runtime state (e.g. active_trades) with manager
    """
    logger.info(f"Starting bot instance for user {user_id} with strategy: {strategy_config.get('STRATEGY', 'unknown')}")
    
    # Extract config values with defaults
    symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
    timeframe = strategy_config.get('TIMEFRAME', '1m')
    amount_usdt = strategy_config.get('AMOUNT_USDT', 10.0)
    strategy_name = strategy_config.get('STRATEGY', 'mean_reversion')
    strategy_params = strategy_config.get('STRATEGY_PARAMS', {})
    dry_run = strategy_config.get('DRY_RUN', True)
    exchange = strategy_config.get('EXCHANGE', 'bybit')
    
    # Load Persistent State
    position_start_time = strategy_config.get('position_start_time')
    if position_start_time:
        logger.info(f"Loaded persisted position start time: {position_start_time}")
        # Convert to float timestamp for logic
        try:
            position_start_time = position_start_time.timestamp()
        except (AttributeError, TypeError):
            # Already a float timestamp or cannot be converted
            logger.debug(f"Position start time already in correct format: {type(position_start_time)}")

    active_order_id = strategy_config.get('active_order_id')
    open_order = None
    if active_order_id:
        logger.info(f"Loaded persisted active order: {active_order_id}")
        # We will verify this order exists in the startup check below

    
    logger.info(f"Loading exchange: {exchange} for user {user_id}")
    
    # Load API keys for this user from database
    from .database import DuckDBHandler
    from .encryption import EncryptionHelper
    from .client_manager import client_manager
    
    db = DuckDBHandler()
    encryption = EncryptionHelper()
    
    # Try to get user's API keys for the selected exchange
    api_key_data = db.get_api_key(user_id, exchange)
    
    if api_key_data:
        # Decrypt user's API keys
        api_key = encryption.decrypt(api_key_data['api_key_encrypted'])
        api_secret = encryption.decrypt(api_key_data['api_secret_encrypted'])
        logger.info(f"✓ Loaded encrypted API keys for user {user_id} ({exchange})")
    else:
        # Fallback to global config (for backward compatibility - only for bybit)
        if exchange == 'bybit':
            api_key = config.API_KEY
            api_secret = config.API_SECRET
            logger.warning(f"⚠️ No encrypted API keys found for user {user_id}, using global config")
        else:
            logger.error(f"❌ No API keys found for user {user_id} on exchange {exchange}")
            raise ValueError(f"Missing API credentials for user {user_id} on {exchange}")
    
    if not api_key or not api_secret:
        if dry_run:
            logger.warning(f"⚠️ No API keys found for user {user_id}. Proceeding in DRY RUN mode with public data only.")
            # Use dummy keys for public data access in Dry Run
            api_key = "dummy_key"
            api_secret = "dummy_secret"
        else:
            logger.error(f"❌ No API keys available for user {user_id}")
            raise ValueError(f"Missing API credentials for user {user_id}")
    
    # Initialize Exchange Client via ClientManager
    try:
        client = client_manager.get_client(
            user_id=user_id,
            api_key=api_key,
            api_secret=api_secret,
            dry_run=dry_run,
            exchange=exchange
        )
        logger.info(f"✓ User {user_id} initialized {exchange} client")
    except Exception as e:
        logger.error(f"❌ Failed to initialize {exchange} client for user {user_id}: {e}")
        raise
    
    # Test connectivity
    try:
        balance = client.fetch_balance()
        logger.info(f"✓ User {user_id} connected to exchange")
    except Exception as e:
        logger.error(f"❌ User {user_id} failed to connect: {e}")
        raise ConnectionError(f"Cannot connect to exchange: {e}")
    
    # Set Leverage
    client.set_leverage(symbol, config.LEVERAGE)

    # --- Startup State Reconciliation ---
    try:
        # Fetch open orders from exchange
        # Note: We need to ensure client has fetch_open_orders. 
        # CCXT has it. PaperExchange now has it.
        if hasattr(client, 'fetch_open_orders'):
            open_orders = client.fetch_open_orders(symbol)
            
            # 1. Reconcile Active Order
            if active_order_id:
                found = False
                for order in open_orders:
                    if str(order['id']) == str(active_order_id):
                        found = True
                        open_order = {
                            'id': order['id'],
                            'time': time.time(), # We don't know exact start, reset timeout clock? Or fetch?
                            # Fetching exact time is better but for now reset clock to give it a chance
                            'side': order['side'],
                            'type': order['type']
                        }
                        logger.info(f"✅ Resumed tracking Limit Order {active_order_id}")
                        break
                
                if not found:
                    logger.warning(f"⚠️ Persisted order {active_order_id} not found on exchange. Clearing state.")
                    active_order_id = None
                    db.update_bot_state(user_id, active_order_id=None)
            
            # 2. Orphan Cleanup
            # Cancel any open orders that we are NOT tracking
            for order in open_orders:
                if active_order_id and str(order['id']) == str(active_order_id):
                    continue
                
                logger.warning(f"🧹 Cancelling orphaned order {order['id']} on {symbol}")
                try:
                    client.cancel_order(order['id'], symbol)
                except Exception as e:
                    logger.error(f"Failed to cancel orphan: {e}")
                    
    except Exception as e:
        logger.error(f"Startup reconciliation failed: {e}")
    # ------------------------------------
    
    # Initialize Strategy
    logger.info(f"Initializing strategy '{strategy_name}' for user {user_id}")
    strategy = create_strategy(strategy_name, strategy_params, user_id)

    # Initialize Notifier
    from .notifier import TelegramNotifier
    
    # Get user's Telegram settings (Chat ID only)
    user_settings = db.get_user_by_id(user_id)
    tg_chat_id = user_settings.get('telegram_chat_id') if user_settings else None
    
    # Use global token from config, user's chat_id
    notifier = TelegramNotifier(token=config.TELEGRAM_BOT_TOKEN, chat_id=tg_chat_id)
    
    # Escape underscores for Telegram Markdown
    safe_strategy_name = strategy_name.replace('_', '\\_')
    notifier.send_message(f"🚀 *Bot Started for User {user_id}*\nStrategy: {safe_strategy_name}")

    logger.info(f"✓ User {user_id} bot initialized. Entering trading loop...")
    
    # Initialize Circuit Breaker
    circuit_breaker = CircuitBreaker(threshold=5, window=60, cooldown=300)
    logger.info(f"Circuit breaker initialized: {circuit_breaker.threshold} failures in {circuit_breaker.window}s triggers {circuit_breaker.cooldown}s pause")
    
    # Initialize subscription check counter
    subscription_check_counter = 0
    SUBSCRIPTION_CHECK_INTERVAL = 10  # Check every 10 loops (~5 minutes with 30s delay)

    # Main trading loop - simplified version
    while True:
        try:
            if not running_event.is_set():
                running_event.wait()
                logger.info(f"▶️ User {user_id} bot resumed")

            # Check circuit breaker
            if circuit_breaker.is_open():
                remaining = circuit_breaker.get_cooldown_remaining()
                logger.warning(f"⚠️ Circuit breaker is {circuit_breaker.get_state()} - cooling down for {remaining:.0f}s")
                time.sleep(min(30, remaining))  # Check every 30s or remaining time
                continue
                
            # Fetch market data with retry
            @retry(max_attempts=3, delay=1, backoff=2)
            def fetch_ohlcv_with_retry():
                return client.fetch_ohlcv(symbol, timeframe, limit=100)
                
            try:
                df = fetch_ohlcv_with_retry()
                circuit_breaker.record_success()  # Success, reset failures
            except Exception as e:
                logger.error(f"User {user_id} OHLCV fetch failed after retries: {e}")
                circuit_breaker.record_failure()
                time.sleep(config.LOOP_DELAY_SECONDS)
                continue

            # Get current position with retry
            @retry(max_attempts=3, delay=1, backoff=2)
            def fetch_position_with_retry():
                return client.fetch_position(symbol)
                
            try:
                position = fetch_position_with_retry()
                position_size = position.get('size', 0.0)
                logger.debug(f"User {user_id} Position: size={position_size}, side={position.get('side', 'N/A')}")
                circuit_breaker.record_success()
            except Exception as e:
                logger.error(f"❌ User {user_id} position fetch failed after retries: {type(e).__name__}: {e}")
                circuit_breaker.record_failure()
                time.sleep(config.LOOP_DELAY_SECONDS)
                continue

            # Generate signal
            try:
                signal = strategy.generate_signal(df)
                logger.debug(f"User {user_id} Signal Generated: {signal}")
            except Exception as e:
                logger.error(f"❌ User {user_id} signal generation failed: {type(e).__name__}: {e}")
                time.sleep(config.LOOP_DELAY_SECONDS)
                continue
            
            # --- Periodic Subscription Check ---
            subscription_check_counter += 1
            if subscription_check_counter >= SUBSCRIPTION_CHECK_INTERVAL:
                subscription_check_counter = 0
                
                if not db.is_subscription_active(user_id):
                    logger.warning(f"⚠️ User {user_id} subscription expired!")
                    
                    # Check if position is open
                    if position_size > 0:
                        logger.info(f"📤 Closing position gracefully for user {user_id} (subscription expired)")
                        notifier.send_message(
                            f"⚠️ *Subscription Expired*\n"
                            f"Closing your open position gracefully.\n"
                            f"Please renew to continue trading."
                        )
                        
                        # Close position at market
                        try:
                            side = 'sell' if position.get('side') == 'Buy' else 'buy'
                            close_order = client.create_order(
                                symbol=symbol,
                                type='market',
                                side=side,
                                amount=position_size
                            )
                            logger.info(f"✅ Position closed for user {user_id} due to subscription expiry")
                            
                            # Clear state
                            db.update_bot_state(user_id, position_start_time=None, active_order_id='NO_CHANGE')
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to close position on subscription expiry: {e}")
                            notifier.send_error(f"Failed to close position: {e}")
                    
                    # Send final notification and exit
                    notifier.send_message(
                        f"🛑 *Bot Stopped*\n"
                        f"Your subscription has expired.\n"
                        f"Please renew to resume trading."
                    )
                    
                    logger.info(f"Bot stopped for user {user_id} - subscription expired")
                    break  # Exit loop gracefully
            # -----------------------------------

            # Simple trading logic (enter/exit based on signal)
            if position_size == 0 and signal in ['long', 'short']:
                # Check subscription before opening new position
                if not db.is_subscription_active(user_id):
                    logger.warning(f"⚠️ User {user_id} subscription inactive - skipping new trade")
                    time.sleep(config.LOOP_DELAY_SECONDS)
                    continue

                # --- Risk Management Checks ---
                risk_profile = db.get_risk_profile(user_id)
                if risk_profile:
                    # 1. Check Max Daily Loss
                    if risk_profile.get('max_daily_loss'):
                        daily_pnl = db.get_daily_pnl(user_id)
                        limit = abs(float(risk_profile['max_daily_loss']))
                        if daily_pnl <= -limit:
                            logger.warning(f"⛔ Max Daily Loss breached for user {user_id}. PnL: {daily_pnl}, Limit: {limit}")
                            notifier.send_message(f"⛔ *Risk Warning*: Daily Loss Limit Hit ({daily_pnl:.2f}). Trading paused.")
                            
                            if risk_profile.get('stop_trading_on_breach'):
                                logger.info(f"Stopping bot for user {user_id} due to risk breach")
                                running_event.clear()
                                break # Exit loop
                            
                            time.sleep(config.LOOP_DELAY_SECONDS)
                            continue # Skip trade
                    
                    # 2. Check Max Position Size
                    if risk_profile.get('max_position_size'):
                        max_size = float(risk_profile['max_position_size'])
                        if amount_usdt > max_size:
                            logger.warning(f"⛔ Max Position Size exceeded for user {user_id}. Amount: {amount_usdt}, Max: {max_size}")
                            notifier.send_message(f"⚠️ Trade blocked: Amount ({amount_usdt}) exceeds limit ({max_size})")
                            time.sleep(config.LOOP_DELAY_SECONDS)
                            continue

                    # 3. Check Max Open Positions
                    if risk_profile.get('max_open_positions'):
                        max_pos = int(risk_profile['max_open_positions'])
                        try:
                            # Dynamic import to avoid circular dependency
                            from .bot_manager import bot_manager
                            bot_stats = bot_manager.get_status(user_id)
                            
                            open_positions = 0
                            if bot_stats:
                                if isinstance(bot_stats, dict) and 'is_running' not in bot_stats:
                                    # Multi-instance dict: count instances with active trades
                                    for s in bot_stats.values():
                                        if s.get('active_trades', 0) > 0:
                                            open_positions += 1
                                elif bot_stats.get('active_trades', 0) > 0:
                                    open_positions = 1
                            
                            # Note: We are currently at 0 (checked by position_size == 0)
                            # So open_positions represents *other* bots. 
                            # If we trade now, we will be open_positions + 1
                            if open_positions >= max_pos:
                                logger.warning(f"⛔ Max Open Positions reached for user {user_id}. Current: {open_positions}, Max: {max_pos}")
                                notifier.send_message(f"⚠️ Trade blocked: Max open positions reached ({max_pos})")
                                time.sleep(config.LOOP_DELAY_SECONDS)
                                continue
                        except Exception as e:
                            logger.error(f"Failed to check open positions: {e}")
                # ------------------------------
                    
                # Open position
                ticker = client.fetch_ticker(symbol)
                current_price = ticker['last']
                amount = amount_usdt / current_price
                side = 'buy' if signal == 'long' else 'sell'
                
                
                try:
                    order = client.create_order(symbol=symbol, type='market', side=side, amount=amount)
                    
                    # Verify Fill
                    time.sleep(1) # Wait for fill
                    exec_price = current_price
                    if order and 'id' in order:
                        fetched = client.fetch_order(order['id'], symbol)
                        if fetched and fetched.get('average'):
                            exec_price = fetched.get('average')
                            logger.info(f"Verified Fill Price: {exec_price}")

                    # Log trade to database
                    trade_data = {
                        'symbol': symbol,
                        'side': side,
                        'price': exec_price,
                        'amount': amount,
                        'type': 'OPEN',
                        'pnl': 0.0,
                        'strategy': strategy_name
                    }
                    db.save_trade(trade_data, user_id=user_id)
                    
                    # Persist State
                    db.update_bot_state(user_id, position_start_time=datetime.fromtimestamp(time.time()), active_order_id='NO_CHANGE')
                    
                    logger.info(f"✓ User {user_id}: {signal} entry at {exec_price}")
                except Exception as e:
                    logger.error(f"❌ User {user_id} order creation failed:")
                    logger.error(f"   Symbol: {symbol}, Side: {side}, Amount: {amount:.6f}")
                    logger.error(f"   Error: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.debug(f"   Stack: {traceback.format_exc()}")

            elif position_size > 0:
                # Check exit (simplified - just on opposite signal)
                position_side = position.get('side')
                if (position_side == 'long' and signal == 'short') or (position_side == 'short' and signal == 'long'):
                    ticker = client.fetch_ticker(symbol)
                    side = 'sell' if position_side == 'long' else 'buy'
                    try:
                        client.create_order(symbol=symbol, type='market', side=side, amount=position_size)
                        logger.info(f"✓ User {user_id}: Closed position")
                        
                        # Fetch Realized PnL
                        time.sleep(2)
                        trades = client.fetch_my_trades(symbol, limit=1)
                        if trades:
                            last_trade = trades[0]
                            # Note: This is a simplification. Real PnL might need matching open/close.
                            # But for now, getting the fee is a good start.
                            logger.info(f"Trade Info: {last_trade}")
                            
                        # Clear State
                        db.update_bot_state(user_id, position_start_time=None, active_order_id='NO_CHANGE')
                        
                    except Exception as e:
                        logger.error(f"❌ User {user_id} position close failed:")
                        logger.error(f"   Symbol: {symbol}, Side: {side}, Size: {position_size}")
                        logger.error(f"   Error: {type(e).__name__}: {str(e)}")

            time.sleep(config.LOOP_DELAY_SECONDS)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"User {user_id} bot error: {e}")
            time.sleep(10)
    
    logger.info(f"Bot instance for user {user_id} terminated")


def main(user_id: int = 0):
    """Original main function - kept for backward compatibility.
    
    Args:
        user_id: User ID (default 0 for standalone mode)
    """
    logger.info("Starting Trading Bot...")
    
    # Initialize Exchange Client
    if getattr(config, 'DRY_RUN', False):
        from .exchange.paper import PaperExchange
        logger.info("⚠️ DRY RUN MODE ENABLED: Using Paper Exchange")
        client = PaperExchange(config.API_KEY, config.API_SECRET)
    else:
        client = ExchangeClient(config.API_KEY, config.API_SECRET)
    
    # Set Leverage
    client.set_leverage(config.SYMBOL, config.LEVERAGE)
    
    # Initialize Strategy
    strategy_name = getattr(config, 'STRATEGY', 'mean_reversion')
    strategy_params = getattr(config, 'STRATEGY_PARAMS', {})
    logger.info(f"Selected Strategy: {strategy_name} with params: {strategy_params}")
    strategy = create_strategy(strategy_name, strategy_params)

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
                
                # Check Order Status
                try:
                    fetched_order = client.fetch_order(open_order['id'], config.SYMBOL)
                    if fetched_order and fetched_order['status'] in ['closed', 'filled']:
                        logger.info(f"✅ Limit Order {open_order['id']} FILLED at {fetched_order.get('average')}")
                        open_order = None # Stop tracking
                        
                        # Update State: Order Filled -> Position Open
                        position_start_time = time.time()
                        if user_id:
                            db.update_bot_state(user_id, position_start_time=datetime.fromtimestamp(position_start_time), active_order_id=None)
                        
                        continue
                except Exception as e:
                    logger.error(f"Failed to check order status: {e}")

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
                        if user_id:
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
                
                # Update Runtime State (Active Trades)
                if runtime_state is not None:
                    runtime_state['active_trades'] = 1 if current_pos_size > 0 else 0
                
                # Execute Trading Logic
                
                # --- Edge Positioning Check ---
                # Only check if we are looking to open a new position (size == 0)
                if current_pos_size == 0 and edge.enabled:
                    if not edge.check_edge(db, user_id=user_id if user_id else None):
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
                    
                    # --- Time-Based Exit (Stagnant Position) ---
                    # If position has been open too long with minimal movement, force close
                    max_duration = getattr(config, 'MAX_POSITION_DURATION_MINUTES', 60)
                    min_movement = getattr(config, 'MIN_MOVEMENT_PCT', 0.005)
                    
                    if duration_minutes >= max_duration and abs(pnl_pct) < min_movement:
                        logger.info(f"⏰ Time-Based Exit Triggered! Duration: {duration_minutes:.1f}m, PnL: {pnl_pct*100:.2f}% (stagnant)")
                        signal = 'SELL' if current_pos_side == 'Buy' else 'BUY'
                        details['reason'] = 'Stagnant Position Timeout'
                    # -------------------------------------------
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
                        
                        # Calculate Fee & PnL
                        realized_pnl = 0.0
                        fee = current_pos_size * current_price * config.TAKER_FEE_PCT
                        
                        # Try to fetch actual data
                        time.sleep(2)
                        try:
                            trades = client.fetch_my_trades(config.SYMBOL, limit=1)
                            if trades:
                                last_trade = trades[0]
                                fee = last_trade.get('fee', fee)
                                # PnL is tricky without full history, but we can try
                                # For now, we stick to estimated PnL but actual Fee
                        except Exception as e:
                            logger.error(f"Failed to fetch trade info: {e}")
                        
                        # Log trade to database
                        trade_data = {
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_SHORT',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': realized_pnl - fee, 
                            'strategy': strategy_name,
                            'fee': fee,
                            'leverage': config.LEVERAGE
                        }
                        db.save_trade(trade_data, user_id=user_id)
                        
                        # Clear State
                        db.update_bot_state(user_id, position_start_time=None, active_order_id='NO_CHANGE')
                        
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
                            # Persist Order ID
                            db.update_bot_state(user_id, active_order_id=order['id'], position_start_time='NO_CHANGE')
                        else:
                            # Market Order filled immediately (conceptually)
                            # Initialize Trailing Stop
                            strategy.highest_price = current_price
                            position_start_time = time.time()
                            
                            # Verify Fill
                            time.sleep(1)
                            exec_price = current_price
                            if order and 'id' in order:
                                fetched = client.fetch_order(order['id'], config.SYMBOL)
                                if fetched and fetched.get('average'):
                                    exec_price = fetched.get('average')
                            
                            # Calculate Fee
                            trade_amount = config.AMOUNT_USDT / exec_price
                            fee = trade_amount * exec_price * config.TAKER_FEE_PCT
                            
                            # Log trade to database
                            trade_data = {
                                'symbol': config.SYMBOL,
                                'side': 'Buy',
                                'price': exec_price,
                                'amount': trade_amount,
                                'type': 'OPEN',
                                'pnl': -fee,
                                'strategy': strategy_name,
                                'fee': fee,
                                'leverage': config.LEVERAGE
                            }
                            db.save_trade(trade_data, user_id=user_id)
                            
                            # Persist State
                            db.update_bot_state(user_id, position_start_time=datetime.fromtimestamp(time.time()), active_order_id='NO_CHANGE')
                            
                            notifier.send_trade_alert(trade_data)

                    except Exception as e:
                        logger.error(f"Failed to open LONG: {e}")
                        notifier.send_error(f"Failed to open LONG: {e}")
                
                elif signal == 'SELL' and current_pos_side != 'Sell':
                    # Close long if exists
                    if current_pos_side == 'Buy':
                        logger.info("Closing LONG position before opening SHORT")
                        client.close_position(config.SYMBOL)
                        
                        # Calculate Fee & PnL
                        realized_pnl = 0.0
                        fee = current_pos_size * current_price * config.TAKER_FEE_PCT
                        
                        # Try to fetch actual data
                        time.sleep(2)
                        try:
                            trades = client.fetch_my_trades(config.SYMBOL, limit=1)
                            if trades:
                                last_trade = trades[0]
                                fee = last_trade.get('fee', fee)
                        except Exception as e:
                            logger.error(f"Failed to fetch trade info: {e}")
                        
                        # Log trade to database
                        trade_data = {
                            'symbol': config.SYMBOL,
                            'side': 'CLOSE_LONG',
                            'price': current_price,
                            'amount': current_pos_size,
                            'type': 'CLOSE',
                            'pnl': realized_pnl - fee, # Exchange PnL + Fee deduction
                            'strategy': strategy_name,
                            'fee': fee,
                            'leverage': config.LEVERAGE
                        }
                        db.save_trade(trade_data, user_id=user_id)
                        
                        # Clear State
                        db.update_bot_state(user_id, position_start_time=None, active_order_id='NO_CHANGE')
                        
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
                            # Persist Order ID
                            db.update_bot_state(user_id, active_order_id=order['id'], position_start_time='NO_CHANGE')
                        else:
                            # Initialize Trailing Stop
                            strategy.lowest_price = current_price
                            position_start_time = time.time()
                            
                            # Verify Fill
                            time.sleep(1)
                            exec_price = current_price
                            if order and 'id' in order:
                                fetched = client.fetch_order(order['id'], config.SYMBOL)
                                if fetched and fetched.get('average'):
                                    exec_price = fetched.get('average')
                            
                            # Calculate Fee
                            trade_amount = config.AMOUNT_USDT / exec_price
                            fee = trade_amount * exec_price * config.TAKER_FEE_PCT
                            
                            # Log trade to database
                            trade_data = {
                                'symbol': config.SYMBOL,
                                'side': 'Sell',
                                'price': exec_price,
                                'amount': trade_amount,
                                'type': 'OPEN',
                                'pnl': -fee,
                                'strategy': strategy_name,
                                'fee': fee,
                                'leverage': config.LEVERAGE
                            }
                            db.save_trade(trade_data, user_id=user_id)
                            
                            # Persist State
                            db.update_bot_state(user_id, position_start_time=datetime.fromtimestamp(time.time()), active_order_id='NO_CHANGE')
                            
                            notifier.send_trade_alert(trade_data)

                    except Exception as e:
                        logger.error(f"Failed to open SHORT: {e}")
                        notifier.send_error(f"Failed to open SHORT: {e}")
                
            # Sleep to prevent API spam (configurable delay)
            time.sleep(config.LOOP_DELAY_SECONDS)
                
        except KeyboardInterrupt:
            logger.info(f"⏸️ User {user_id} bot stopped by keyboard interrupt")
            notifier.send_message(f"⏹️ *Bot Stopped*\nUser {user_id} bot manually stopped")
            break
        except Exception as e:
            import traceback
            error_details = {
                'user_id': user_id,
                'symbol': symbol,
                'strategy': strategy_name,
                'position_size': position.get('size', 'unknown') if 'position' in locals() else 'unknown',
                'signal': signal if 'signal' in locals() else 'unknown',
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            
            logger.error(f"❌ Critical Error in Bot Loop for User {user_id}")
            logger.error(f"Context: {error_details}")
            logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            
            notifier.send_error(f"❌ *Bot Loop Error*\nUser: {user_id}\nError: {type(e).__name__}\nMessage: {str(e)[:200]}")
            
            # Add a small delay to avoid rapid error loops
            time.sleep(10)

if __name__ == "__main__":
    main()
