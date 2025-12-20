import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.exchange.paper import PaperExchange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def test_paper_exchange():
    logger.info("Testing PaperExchange...")
    
    # Initialize
    client = PaperExchange(api_key="dummy", api_secret="dummy")
    
    # 1. Create Order
    logger.info("Creating Market Buy Order...")
    order = client.create_order('BTC/USDT', 'market', 'buy', 0.1, 50000.0)
    
    if not order or 'id' not in order:
        logger.error("Failed to create order")
        return False
        
    order_id = order['id']
    logger.info(f"Order Created: {order_id}")
    
    # 2. Fetch Order
    logger.info("Fetching Order...")
    fetched_order = client.fetch_order(order_id, 'BTC/USDT')
    
    if not fetched_order:
        logger.error("Failed to fetch order")
        return False
        
    if fetched_order['status'] != 'closed':
        logger.error(f"Order status mismatch. Expected 'closed', got {fetched_order['status']}")
        return False
        
    logger.info(f"Order Fetched: {fetched_order}")
    
    # 3. Fetch Trades
    logger.info("Fetching Trades...")
    trades = client.fetch_my_trades('BTC/USDT', limit=1)
    
    if not trades:
        logger.error("No trades found")
        return False
        
    last_trade = trades[0]
    if last_trade['order'] != order_id:
        logger.error(f"Trade order ID mismatch. Expected {order_id}, got {last_trade['order']}")
        return False
        
    logger.info(f"Trade Fetched: {last_trade}")
    
    logger.info("✅ PaperExchange Verification Passed!")
    return True

if __name__ == "__main__":
    try:
        if test_paper_exchange():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)
