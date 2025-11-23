import config
import logging
from exchange.client import ExchangeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPosition")

def test_position():
    try:
        logger.info("Testing fetch_position on ByBit Demo...")
        
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        
        # Fetch position for BTC/USDT
        symbol = config.SYMBOL
        logger.info(f"Fetching position for {symbol}...")
        
        position = client.fetch_position(symbol)
        
        if position:
            logger.info("Position fetched successfully:")
            print(position)
        else:
            logger.error("Failed to fetch position.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_position()
