import config
import logging
import time
from exchange.client import ExchangeClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("test_output.log"), logging.StreamHandler()])
logger = logging.getLogger("TestOrderLifecycle")

def test_lifecycle():
    try:
        logger.info("Starting Order Lifecycle Test on ByBit Demo...")
        
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        symbol = config.SYMBOL
        amount = 0.001  # Small amount for testing
        
        # Check Balance
        logger.info("Checking Balance...")
        balance = client.fetch_balance()
        logger.info(f"Balance: {balance}")

        # 1. Check Initial Position
        logger.info(f"1. Checking initial position for {symbol}...")
        initial_pos = client.fetch_position(symbol)
        logger.info(f"Initial Position: {initial_pos}")
        
        if initial_pos['size'] > 0:
            logger.warning("WARNING: You already have an open position! This test might mess it up.")
            # Optional: Close it first? Or just abort?
            # For safety in a test script, maybe we should abort or ask user?
            # Since this is an automated agent task, I'll proceed but log heavily.
            # Actually, if I buy more, I just increase position. If I sell, I reduce it.
            # To be clean, let's try to close it if it exists? 
            # No, that's dangerous if it's a real trade.
            # I will just proceed and note the delta.
        
        # 2. Place BUY Order
        logger.info(f"2. Placing MARKET BUY order for {amount} {symbol}...")
        order = client.create_order(symbol, 'market', 'buy', amount)
        
        if order:
            logger.info(f"Order placed successfully: {order.get('id')}")
        else:
            logger.error("Failed to place order. Aborting.")
            return

        # Wait for order to fill/propagate
        time.sleep(5)
        
        # 3. Check Position After Buy
        logger.info("3. Checking position after BUY...")
        after_buy_pos = client.fetch_position(symbol)
        logger.info(f"Position after BUY: {after_buy_pos}")
        
        # Verify size increased
        expected_size = initial_pos['size'] + amount
        # Allow small float diffs
        if abs(after_buy_pos['size'] - expected_size) < 0.0001:
            logger.info("SUCCESS: Position size increased as expected.")
        else:
            logger.error(f"FAILURE: Position size mismatch. Expected ~{expected_size}, got {after_buy_pos['size']}")
        
        # 4. Close Position (Sell the same amount)
        logger.info(f"4. Placing MARKET SELL order for {amount} {symbol} to close...")
        close_order = client.create_order(symbol, 'market', 'sell', amount)
        
        if close_order:
            logger.info(f"Close order placed successfully: {close_order.get('id')}")
        else:
            logger.error("Failed to place close order.")
            return
            
        # Wait
        time.sleep(5)
        
        # 5. Check Final Position
        logger.info("5. Checking final position...")
        final_pos = client.fetch_position(symbol)
        logger.info(f"Final Position: {final_pos}")
        
        if abs(final_pos['size'] - initial_pos['size']) < 0.0001:
            logger.info("SUCCESS: Position returned to initial size.")
        else:
            logger.error(f"FAILURE: Final position size mismatch. Expected ~{initial_pos['size']}, got {final_pos['size']}")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lifecycle()
