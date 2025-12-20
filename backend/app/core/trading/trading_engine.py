"""
Trading Engine Module

Main orchestrator that ties all trading components together.
Replaces the monolithic run_bot_instance() function with clean, modular architecture.
"""
import time
import logging
import threading

from ..resilience import CircuitBreaker
from .. import config
from ..socket_manager import socket_manager
import asyncio

from .strategy_factory import create_strategy
from .market_data import MarketDataFetcher
from .signal_generator import SignalGenerator
from .risk_manager import RiskManager
from .order_executor import OrderExecutor
from .position_manager import PositionManager
from .subscription_checker import SubscriptionChecker

logger = logging.getLogger("TradingBot")


class TradingEngine:
    """
    Main trading engine orchestrator.
    
    Coordinates all trading components in a clean, modular way.
    """
    
    def __init__(self, user_id: int, strategy_config: dict, running_event: threading.Event, runtime_state: dict = None, main_loop = None):
        """
        Initialize trading engine with all components.
        
        Args:
            user_id: The user ID this bot belongs to
            strategy_config: Dictionary containing strategy configuration
            running_event: Thread event to control pause/resume
            runtime_state: Dictionary to share runtime state with manager
        """
        self.user_id = user_id
        self.strategy_config = strategy_config
        self.running_event = running_event
        self.runtime_state = runtime_state
        self.main_loop = main_loop
        
        # Extract configuration
        self.symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
        self.timeframe = strategy_config.get('TIMEFRAME', '1m')
        self.amount_usdt = strategy_config.get('AMOUNT_USDT', 10.0)
        self.strategy_name = strategy_config.get('STRATEGY', 'mean_reversion')
        self.strategy_params = strategy_config.get('STRATEGY_PARAMS', {})
        self.dry_run = strategy_config.get('DRY_RUN', True)
        self.exchange = strategy_config.get('EXCHANGE', 'bybit')
        self.leverage = strategy_config.get('LEVERAGE', 10.0)
        self.take_profit_pct = strategy_config.get('TAKE_PROFIT_PCT', getattr(config, 'TAKE_PROFIT_PCT', 0.01))
        self.stop_loss_pct = strategy_config.get('STOP_LOSS_PCT', getattr(config, 'STOP_LOSS_PCT', 0.01))
        
        # Calculate loop delay
        self.loop_delay = self._calculate_loop_delay()
        
        # Components (initialized in setup())
        self.client = None
        self.db = None
        self.notifier = None
        self.strategy = None
        self.market_data = None
        self.signal_gen = None
        self.risk_mgr = None
        self.order_exec = None
        self.position_mgr = None
        self.sub_checker = None
        self.circuit_breaker = None
        
        # Error handling state
        self.error_count = 0
        self.last_error_time = 0
        
        logger.info(f"Starting bot instance for user {user_id} with strategy: {self.strategy_name}")
    
    def _calculate_loop_delay(self):
        """Calculate appropriate loop delay based on strategy and timeframe"""
        STRATEGY_LOOP_DELAYS = {
            'mean_reversion': 5,
            'momentum': 5,
            'sma_crossover': 30,
            'macd': 20,
            'rsi': 10,
            'bollinger_breakout': 5,
            'dca_dip': 60,
            'combined': 15
        }
        
        strategy_key = self.strategy_name.lower()
        loop_delay = STRATEGY_LOOP_DELAYS.get(strategy_key, 30)
        
        # Override based on timeframe
        if self.timeframe == '1m':
            loop_delay = min(loop_delay, 5)
        elif self.timeframe == '5m':
            loop_delay = min(loop_delay, 10)
        
        return loop_delay
    
    def _initialize_components(self):
        """Initialize all trading components"""
        from ..database import DuckDBHandler
        from ..encryption import EncryptionHelper
        from ..client_manager import client_manager
        from ..notifier import TelegramNotifier
        
        # Initialize database and encryption
        self.db = DuckDBHandler()
        encryption = EncryptionHelper()
        
        # Load API keys
        api_key_data = self.db.get_api_key(self.user_id, self.exchange)
        if api_key_data:
            api_key = encryption.decrypt(api_key_data['api_key_encrypted'])
            api_secret = encryption.decrypt(api_key_data['api_secret_encrypted'])
            logger.info(f"✓ Loaded encrypted API keys for user {self.user_id} ({self.exchange})")
        elif self.exchange == 'bybit':
            api_key = config.API_KEY
            api_secret = config.API_SECRET
            logger.warning(f"⚠️ No encrypted API keys found for user {self.user_id}, using global config")
        else:
            raise ValueError(f"Missing API credentials for user {self.user_id} on {self.exchange}")
        
        if not api_key or not api_secret:
            if self.dry_run:
                logger.warning(f"⚠️ No API keys found for user {self.user_id}. Proceeding in DRY RUN mode.")
                api_key, api_secret = "dummy_key", "dummy_secret"
            else:
                raise ValueError(f"Missing API credentials for user {self.user_id}")
        
        # Initialize exchange client
        self.client = client_manager.get_client(
            user_id=self.user_id,
            api_key=api_key,
            api_secret=api_secret,
            dry_run=self.dry_run,
            exchange=self.exchange
        )
        logger.info(f"✓ User {self.user_id} initialized {self.exchange} client")
        
        # Test connectivity and set leverage
        self.client.fetch_balance()
        self.client.set_leverage(self.symbol, self.leverage)
        logger.info(f"✓ User {self.user_id} connected to exchange")
        
        # Initialize strategy
        self.strategy = create_strategy(self.strategy_name, self.strategy_params, self.user_id)
        
        # Initialize notifier
        user_settings = self.db.get_user_by_id(self.user_id)
        tg_chat_id = user_settings.get('telegram_chat_id') if user_settings else None
        self.notifier = TelegramNotifier(token=config.TELEGRAM_BOT_TOKEN, chat_id=tg_chat_id)
        safe_strategy_name = self.strategy_name.replace('_', '\\\\_')
        self.notifier.send_message(f"🚀 *Bot Started for User {self.user_id}*\\nStrategy: {safe_strategy_name}")
        
        # Initialize trading components
        self.market_data = MarketDataFetcher(self.client, self.symbol, self.timeframe)
        self.signal_gen = SignalGenerator(self.strategy, self.user_id)
        self.risk_mgr = RiskManager(self.db, self.notifier, self.user_id)
        self.order_exec = OrderExecutor(self.client, self.db, self.notifier, self.user_id)
        self.position_mgr = PositionManager(self.user_id, self.db)
        self.sub_checker = SubscriptionChecker(self.db, self.notifier, self.user_id, self.loop_delay)
        self.circuit_breaker = CircuitBreaker(threshold=5, window=60, cooldown=300)
        
        # Load persisted state and reconcile
        self.position_mgr.load_persisted_state(self.strategy_config)
        self.position_mgr.reconcile_on_startup(self.client, self.symbol)
        
        logger.info(f"✓ User {self.user_id} bot initialized. Entering trading loop...")
    
    def run(self):
        """Main trading loop - clean and orchestrated"""
        try:
            self._initialize_components()
            self._trading_loop()
        except Exception as e:
            logger.error(f"CRITICAL: User {self.user_id} bot crashed: {e}")
            try:
                self.notifier.send_error(f"Bot Crashed:\\n{str(e)}")
            except:
                pass
        finally:
            logger.info(f"Bot instance for user {self.user_id} terminated")
            try:
                self.notifier.send_message(f"🛑 *Bot Stopped for User {self.user_id}*")
            except:
                pass
    
    def _trading_loop(self):
        """Main trading loop"""
        while True:
            try:
                # Check if paused
                if not self.running_event.is_set():
                    self.running_event.wait()
                    logger.info(f"▶️ User {self.user_id} bot resumed")
                
                logger.info(f"--- [User {self.user_id}] {self.symbol} Loop Start ---")
                
                # Check circuit breaker
                if self.circuit_breaker.is_open():
                    remaining = self.circuit_breaker.get_cooldown_remaining()
                    logger.warning(f"⚠️ Circuit breaker is {self.circuit_breaker.get_state()} - cooling down for {remaining:.0f}s")
                    time.sleep(min(30, remaining))
                    continue
                
                # Determine required data points
                required_limit = self._calculate_required_limit()
                
                # 1. Fetch market data
                logger.info(f"1. 📥 [User {self.user_id}] Fetching Market Data ({required_limit} candles)...")
                try:
                    df = self.market_data.fetch_ohlcv(limit=required_limit)
                    self.circuit_breaker.record_success()
                except Exception as e:
                    logger.error(f"User {self.user_id} OHLCV fetch failed: {e}")
                    self.circuit_breaker.record_failure()
                    time.sleep(self.loop_delay)
                    continue
                
                current_price = self.market_data.get_current_price(df)
                
                # 2. Get current position
                try:
                    position = self.market_data.fetch_position()
                    position_size = position.get('size', 0.0)
                    self.circuit_breaker.record_success()
                except Exception as e:
                    logger.error(f"❌ User {self.user_id} position fetch failed: {e}")
                    self.circuit_breaker.record_failure()
                    time.sleep(self.loop_delay)
                    continue
                
                # 3. Generate signal
                signal, score, details, log_msg = self.signal_gen.generate_and_parse_signal(df, self.strategy_params)
                
                # Emit Signal (only if significant)
                if self.main_loop and signal and signal.lower() not in ('hold', 'neutral', 'wait'):
                    asyncio.run_coroutine_threadsafe(
                        socket_manager.broadcast({
                            "type": "signal",
                            "data": {
                                "symbol": self.symbol,
                                "signal": signal,
                                "score": score,
                                "price": current_price,
                                "timestamp": time.time()
                            }
                        }, user_id=self.user_id),
                        loop=self.main_loop
                    )
                
                # 4. Periodic subscription check
                if self.sub_checker.should_check_now():
                    if not self.risk_mgr.check_subscription_active():
                        should_exit = self.sub_checker.handle_expired_subscription(self.client, self.symbol, position)
                        if should_exit:
                            break
                
                # 5. Trading logic
                if position_size == 0 and signal in ['long', 'short']:
                    self._handle_entry_signal(signal, current_price)
                elif position_size > 0:
                    self._handle_open_position(position, signal, current_price)
                
                # Sleep
                logger.info(f"😴 Sleeping {self.loop_delay}s...")
                time.sleep(self.loop_delay)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._handle_error(e)
    
    def _calculate_required_limit(self):
        """Calculate required OHLCV data points based on strategy params"""
        required_limit = 100
        for param_key, param_value in self.strategy_params.items():
            if isinstance(param_value, (int, float)) and 'period' in param_key.lower():
                needed = int(param_value) + 50
                if needed > required_limit:
                    required_limit = needed
        return min(required_limit, 1000)
    
    def _handle_entry_signal(self, signal, current_price):
        """Handle entry signal when no position is open"""
        # Check subscription
        if not self.risk_mgr.check_subscription_active():
            logger.warning(f"⚠️ User {self.user_id} subscription inactive - skipping new trade")
            return
        
        # Run risk checks
        allowed, reason = self.risk_mgr.check_can_open_position(self.amount_usdt, self.client)
        if not allowed:
            logger.info(f"😴 Sleeping {self.loop_delay}s...")
            time.sleep(self.loop_delay)
            return
        
        # Execute entry order
        success, entry_price = self.order_exec.execute_entry_order(
            self.symbol, signal, self.amount_usdt, current_price,
            self.strategy_name, self.take_profit_pct, self.stop_loss_pct
        )
        
        if success:
            self.position_mgr.update_state(position_start_time=time.time())
            
            # Emit Trade Event
            if self.main_loop:
                asyncio.run_coroutine_threadsafe(
                    socket_manager.broadcast({
                        "type": "trade",
                        "data": {
                            "symbol": self.symbol,
                            "side": signal, # 'long' or 'short'
                            "entry_price": entry_price,
                            "amount": self.amount_usdt, # approx
                            "timestamp": time.time()
                        }
                    }, user_id=self.user_id),
                    loop=self.main_loop
                )
    
    def _handle_open_position(self, position, signal, current_price):
        """Handle monitoring and potential exit of open position"""
        position_side = position.get('side')
        position_size = position.get('size', 0.0)
        
        # Check for exit signal
        if (position_side == 'long' and signal == 'short') or (position_side == 'short' and signal == 'long'):
            success, pnl = self.order_exec.execute_exit_order(self.symbol, position, current_price, self.strategy_name)
            if success:
                self.position_mgr.update_state(position_start_time=None)
                # Emit Exit Event
                if self.main_loop:
                    asyncio.run_coroutine_threadsafe(
                        socket_manager.broadcast({
                            "type": "trade_closed",
                            "data": {
                                "symbol": self.symbol,
                                "pnl": pnl, # approx
                                "exit_price": current_price,
                                "timestamp": time.time()
                            }
                        }, user_id=self.user_id),
                        loop=self.main_loop
                    )
        else:
            # Monitor position
            unrealized_pnl, pnl_pct = self.position_mgr.calculate_unrealized_pnl(
                position, current_price, self.amount_usdt, self.leverage
            )
            
            # Calculate TP/SL prices
            entry_p = float(position.get('entry_price', current_price))
            tp_price = entry_p * (1 + self.take_profit_pct) if self.take_profit_pct and position_side == 'Buy' else entry_p * (1 - self.take_profit_pct) if self.take_profit_pct else 0
            sl_price = entry_p * (1 - self.stop_loss_pct) if self.stop_loss_pct and position_side == 'Buy' else entry_p * (1 + self.stop_loss_pct) if self.stop_loss_pct else 0
            
            tp_str = f"${tp_price:.2f}" if tp_price else "N/A"
            sl_str = f"${sl_price:.2f}" if sl_price else "N/A"
            
            # Calculate duration
            duration_str = "?"
            if self.position_mgr.position_start_time:
                dur = (time.time() - self.position_mgr.position_start_time) / 60
                duration_str = f"{dur:.1f}m"
            
            logger.info(f"5. 👁️ Monitoring | PnL: {pnl_pct*100:+.2f}% (${unrealized_pnl:+.2f}) | TP: {tp_str} | SL: {sl_str} | Dur: {duration_str}")
            
            # Update runtime state
            if self.runtime_state is not None:
                self.runtime_state['pnl'] = unrealized_pnl
                self.runtime_state['roi'] = pnl_pct * 100
                self.runtime_state['current_price'] = current_price
                self.runtime_state['tp_price'] = tp_price
                self.runtime_state['sl_price'] = sl_price
    
    def _handle_error(self, e):
        """Handle errors with smart backoff and notifications"""
        current_time = time.time()
        self.error_count += 1
        
        # Check for fatal errors
        if isinstance(e, (NameError, SyntaxError, TypeError, AttributeError, ImportError)):
            logger.critical(f"❌ FATAL ERROR for User {self.user_id}: {type(e).__name__}: {e}")
            self.notifier.send_error(f"🛑 *Fatal Bot Error*\\nUser: {self.user_id}\\nType: `{type(e).__name__}`\\nError: `{str(e)}`\\n\\nBot has been stopped.")
            self.running_event.clear()
            raise
        
        # Calculate backoff
        backoff_delay = min(300, 10 * (2 ** (self.error_count - 1)))
        logger.error(f"User {self.user_id} bot error (Count: {self.error_count}): {e}")
        
        # Notification suppression
        should_notify = (self.error_count == 1) or (self.error_count % 5 == 0)
        if should_notify:
            self.notifier.send_message(f"⚠️ *Bot Error (x{self.error_count})*\\n`{str(e)[:200]}`\\nWaiting {backoff_delay}s...")
        
        # Reset error count if last error was long ago
        if current_time - self.last_error_time > 600:
            self.error_count = 1
        
        self.last_error_time = current_time
        time.sleep(backoff_delay)
