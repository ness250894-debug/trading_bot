import config
import logging
from exchange.client import ExchangeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDemoConnection")

def test_demo_connection():
    try:
        logger.info("Testing connection to ByBit Demo Trading via ExchangeClient...")
        
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        
        logger.info("Fetching server time...")
        server_time = client.exchange.fetch_time()
        logger.info(f"Server Time: {server_time}")
        
        logger.info("Fetching balance via client.fetch_balance()...")
        balance = client.fetch_balance()
        
        if balance:
            logger.info("Balance fetched successfully.")
            print(balance)
        else:
            logger.error("Failed to fetch balance.")
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_demo_connection()
