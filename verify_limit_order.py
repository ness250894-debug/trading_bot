import time
import logging
from unittest.mock import MagicMock
from backend.app.core import config

# Mock Config
config.ORDER_TYPE = 'limit'
config.ORDER_TIMEOUT_SECONDS = 2
config.SYMBOL = 'BTC/USDT'
config.AMOUNT_USDT = 100
config.TAKE_PROFIT_PCT = 0.01
config.STOP_LOSS_PCT = 0.005
config.TAKER_FEE_PCT = 0.0006

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestLimitOrder")

def verify_limit_logic():
    print("--- Testing Limit Order Logic ---")
    
    # Mock Client
    client = MagicMock()
    client.fetch_ticker.return_value = {'bid': 50000, 'ask': 50001, 'last': 50000}
    client.create_order.side_effect = [
        {'id': 'limit_order_1', 'status': 'open'}, # Limit Order
        {'id': 'market_order_1', 'status': 'filled'} # Market Order (after timeout)
    ]
    
    # 1. Place Limit Order
    print("\n1. Placing Limit Order...")
    ticker = client.fetch_ticker(config.SYMBOL)
    price = ticker['bid']
    
    order = client.create_order(
        symbol=config.SYMBOL,
        side='Buy',
        amount=config.AMOUNT_USDT / price,
        order_type='limit',
        price=price
    )
    print(f"Order Placed: {order}")
    
    open_order = {
        'id': order['id'],
        'time': time.time(),
        'side': 'Buy',
        'type': 'limit'
    }
    
    # 2. Simulate Wait (Timeout)
    print(f"\n2. Waiting for timeout ({config.ORDER_TIMEOUT_SECONDS}s)...")
    time.sleep(config.ORDER_TIMEOUT_SECONDS + 1)
    
    # 3. Check Timeout Logic
    print("\n3. Checking Timeout Logic...")
    if time.time() - open_order['time'] > config.ORDER_TIMEOUT_SECONDS:
        print("   ✅ Timeout detected!")
        
        # Cancel
        client.cancel_order(open_order['id'], config.SYMBOL)
        print("   ✅ Limit Order Cancelled")
        
        # Force Market
        current_price = 50005 # Price moved
        client.fetch_ticker.return_value = {'last': current_price}
        
        market_order = client.create_order(
            symbol=config.SYMBOL,
            side=open_order['side'],
            amount=config.AMOUNT_USDT / current_price,
            order_type='market'
        )
        print(f"   ✅ Market Order Placed: {market_order}")
    else:
        print("   ❌ Timeout NOT detected!")

if __name__ == "__main__":
    verify_limit_logic()
