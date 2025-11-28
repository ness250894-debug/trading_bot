import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logger for config validation
logger = logging.getLogger("Config")

# API Keys - validate they exist
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

# Validate API keys are set (will be checked on bot startup)
if not API_KEY or not API_SECRET:
    logger.warning("⚠️ BYBIT_API_KEY or BYBIT_API_SECRET not set in environment!")
    logger.warning("⚠️ Bot will not be able to connect to exchange.")

DEMO = os.getenv('BYBIT_DEMO', 'True').lower() == 'true'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Trading Settings
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
AMOUNT_USDT = 10.0
LEVERAGE = 10

# Risk Management
TAKE_PROFIT_PCT = 0.01 # 1%
STOP_LOSS_PCT = 0.005 # 0.5%
TRAILING_STOP_PCT = 0.003 # 0.3% (Increased from 0.2%)
TRAILING_STOP_ACTIVATION_PCT = 0.005 # 0.5% (Only activate after 0.5% profit)
TAKER_FEE_PCT = 0.0006 # 0.06% Taker Fee (ByBit Standard)
POSITION_SIZES = {1: 0.01, 2: 0.02, 3: 0.05} # Risk % per trade based on score

# Strategy Settings
STRATEGY = 'mean_reversion'
STRATEGY_PARAMS = {'rsi_period': 20}
HIGHER_TIMEFRAME = '5m' # For Trend Filter

# Mode
DRY_RUN = True

# Bot Settings
LOOP_DELAY_SECONDS = 30  # Delay between trading loop iterations

# Smart ROI (Time-based Take Profit)
# Format: { minutes: profit_pct }
# Example: After 10 mins, accept 2%. After 30 mins, accept 1%.
SMART_ROI = {
    10: 0.02,
    30: 0.01,
    60: 0.005
}

# Order Execution Settings
ORDER_TYPE = 'limit' # 'market' or 'limit'
ORDER_TIMEOUT_SECONDS = 30 # Timeout for limit orders before converting to market

# Market Scanner Settings
SCANNER_ENABLED = True
SCANNER_INTERVAL_MINUTES = 60
SCANNER_TOP_N = 20 # Scan top 20 coins by volume

# Edge Positioning Settings (Advanced Market Filter)
EDGE_ENABLED = True
EDGE_WINDOW_TRADES = 10 # Calculate edge based on last 10 trades
EDGE_MIN_EXPECTANCY = 0.0 # Minimum expectancy to trade (0.0 = breakeven)

# Load Dynamic Config from JSON
import json
import logging

config_path = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            dynamic_config = json.load(f)
            
        # Override globals
        if 'SYMBOL' in dynamic_config: SYMBOL = dynamic_config['SYMBOL']
        if 'TIMEFRAME' in dynamic_config: TIMEFRAME = dynamic_config['TIMEFRAME']
        if 'AMOUNT_USDT' in dynamic_config: AMOUNT_USDT = dynamic_config['AMOUNT_USDT']
        if 'STRATEGY' in dynamic_config: STRATEGY = dynamic_config['STRATEGY']
        if 'STRATEGY_PARAMS' in dynamic_config: STRATEGY_PARAMS = dynamic_config['STRATEGY_PARAMS']
        if 'DRY_RUN' in dynamic_config: DRY_RUN = dynamic_config['DRY_RUN']
        if 'TAKE_PROFIT_PCT' in dynamic_config: TAKE_PROFIT_PCT = dynamic_config['TAKE_PROFIT_PCT']
        if 'STOP_LOSS_PCT' in dynamic_config: STOP_LOSS_PCT = dynamic_config['STOP_LOSS_PCT']
        
        # Log successful load (using print as logger might not be configured yet)
        print(f"Loaded dynamic config from {config_path}")
    except Exception as e:
        print(f"Failed to load config.json: {e}")
