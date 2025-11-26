import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')
DEMO = os.getenv('BYBIT_DEMO', 'True').lower() == 'true'

# Trading Settings
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
AMOUNT_USDT = 10.0
LEVERAGE = 10

# Risk Management
TAKE_PROFIT_PCT = 0.01 # 1%
STOP_LOSS_PCT = 0.005 # 0.5%
TRAILING_STOP_PCT = 0.002 # 0.2%
TAKER_FEE_PCT = 0.0006 # 0.06% Taker Fee (ByBit Standard)
POSITION_SIZES = {1: 0.01, 2: 0.02, 3: 0.05} # Risk % per trade based on score

# Strategy Settings
STRATEGY = 'mean_reversion'
HIGHER_TIMEFRAME = '5m' # For Trend Filter

# Mode
DRY_RUN = True

# Bot Settings
LOOP_DELAY_SECONDS = 30  # Delay between trading loop iterations
