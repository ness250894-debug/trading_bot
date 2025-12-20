"""Quick API key test"""
import sys, os
os.chdir(r'c:\Users\Павло\.gemini\antigravity\scratch\trading_bot\backend')
sys.path.insert(0, r'c:\Users\Павло\.gemini\antigravity\scratch\trading_bot\backend')

from dotenv import load_dotenv
load_dotenv(r'c:\Users\Павло\.gemini\antigravity\scratch\trading_bot\.env')

print('=== API KEY TEST ===')

api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

has_key = api_key and len(api_key) > 5
print(f'API Key loaded: {"Yes" if has_key else "No"}')
if api_key:
    print(f'API Key preview: {api_key[:8]}...')

# Test exchange connection
from app.core.exchange.paper import PaperExchange
p = PaperExchange(api_key or 'k', api_secret or 's', initial_balance=1000)

# Try to fetch ticker
ticker = p.fetch_ticker('BTC/USDT')
if ticker:
    print(f'Ticker fetched! BTC/USDT price: ${ticker.get("last", "N/A")}')
    print('API KEYS WORKING!')
else:
    print('Ticker fetch failed - API keys may be invalid')
