import logging
import sys
import config
from exchange.paper import PaperExchange

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("VerifyDryRun")

def verify():
    logger.info("Verifying Dry Run Mode...")
    
    # Ensure config is set to Dry Run
    if not config.DRY_RUN:
        logger.error("Config DRY_RUN is False! Please set it to True in config.py")
        return

    # Initialize Paper Exchange
    client = PaperExchange(config.API_KEY, config.API_SECRET)
    
    # Check Balance
    balance = client.fetch_balance()
    logger.info(f"Initial Balance: {balance['total']['USDT']}")
    
    # Fetch Price
    price = client.get_market_price(config.SYMBOL)
    logger.info(f"Current Price of {config.SYMBOL}: {price}")
    
    if not price:
        logger.error("Failed to fetch price.")
        return

    # Place Order
    amount = 0.001
    logger.info(f"Placing Buy Order for {amount} {config.SYMBOL}...")
    order = client.create_order(config.SYMBOL, 'market', 'buy', amount)
    
    if order:
        logger.info(f"Order Placed: {order}")
        
        # Check Position
        pos = client.fetch_position(config.SYMBOL)
        logger.info(f"Position after Buy: {pos}")
        
        if pos['size'] == amount:
            logger.info("✅ Verification SUCCESS: Position updated correctly.")
        else:
            logger.error("❌ Verification FAILED: Position size mismatch.")
    else:
        logger.error("❌ Verification FAILED: Order creation failed.")

if __name__ == "__main__":
    verify()
