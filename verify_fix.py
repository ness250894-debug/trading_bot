import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.exchange.client import ExchangeClient
from app.core import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyFix")

def test_client():
    logger.info("Initializing ExchangeClient in Demo mode...")
    try:
        # Initialize with dummy keys if env vars are missing, but config should have them
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=True)
        
        logger.info(f"Exchange URLs: {client.exchange.urls['api']}")
        
        logger.info("Fetching OHLCV data...")
        df = client.fetch_ohlcv('BTC/USDT', '1m', limit=10)
        
        if df is not None and not df.empty:
            logger.info("Successfully fetched data:")
            print(df.head())
            logger.info("Fix Verified: Data fetch successful.")
        else:
            logger.error("Data fetch returned empty or None.")
            
    except Exception as e:
        logger.error(f"Test Failed: {e}")

if __name__ == "__main__":
    test_client()
