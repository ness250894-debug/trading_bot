import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')
DEMO = os.getenv('BYBIT_DEMO', 'True').lower() == 'true'

# Trading Settings
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m' # 1m for scalping
AMOUNT_USDT = 10 # Amount to trade per order in USDT
LEVERAGE = 10

# Risk Management
TAKE_PROFIT_PCT = 0.01 # 1%
STOP_LOSS_PCT = 0.005 # 0.5%
TRAILING_STOP_PCT = 0.002 # 0.2%
TAKER_FEE_PCT = 0.0006 # 0.06% Taker Fee (ByBit Standard)

# Strategy Settings
STRATEGY = 'mean_reversion' # Options: 'mean_reversion', 'sma_crossover', 'macd', 'rsi', 'combined'
HIGHER_TIMEFRAME = '5m' # For Trend Filter

# Mode
DRY_RUN = True # Set to False for Real Trading
