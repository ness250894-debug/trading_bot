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

# Import refactored trading components
from .trading.strategy_factory import create_strategy
from .trading.trading_engine import TradingEngine

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


def run_bot_instance(user_id: int, strategy_config: dict, running_event: threading.Event, runtime_state: dict = None):
    """
    Run a bot instance for a specific user.
    
    **REFACTORED**: This function now uses the modular TradingEngine architecture.
    All trading logic has been extracted into focused, testable modules in trading/.
    
    Args:
        user_id: The user ID this bot belongs to
        strategy_config: Dictionary containing strategy configuration
        running_event: Thread event to control pause/resume
        runtime_state: Dictionary to share runtime state (e.g. active_trades) with manager
    """
    engine = TradingEngine(user_id, strategy_config, running_event, runtime_state)
    engine.run()


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

    # Initialize Notifier
    from .notifier import TelegramNotifier
    notifier = TelegramNotifier(
        token=getattr(config, 'TELEGRAM_BOT_TOKEN', None),
        chat_id=getattr(config, 'TELEGRAM_CHAT_ID', None)
    )
    notifier.send_message(f"🚀 Bot Started\\nStrategy: {strategy_name}")

    # Main Loop (Legacy standalone mode - uses new TradingEngine internally)
    running_event = threading.Event()
    running_event.set()
    
    strategy_config = {
        'SYMBOL': config.SYMBOL,
        'TIMEFRAME': config.TIMEFRAME,
        'AMOUNT_USDT': getattr(config, 'AMOUNT_USDT', 100),
        'STRATEGY': strategy_name,
        'STRATEGY_PARAMS': strategy_params,
        'DRY_RUN': getattr(config, 'DRY_RUN', False),
        'EXCHANGE': getattr(config, 'EXCHANGE', 'bybit'),
        'LEVERAGE': config.LEVERAGE,
        'TAKE_PROFIT_PCT': getattr(config, 'TAKE_PROFIT_PCT', 0.01),
        'STOP_LOSS_PCT': getattr(config, 'STOP_LOSS_PCT', 0.01)
    }
    
    run_bot_instance(user_id, strategy_config, running_event)


if __name__ == "__main__":
    main()
