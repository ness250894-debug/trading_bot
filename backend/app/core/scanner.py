import logging
import ccxt
import pandas as pd
from . import config

logger = logging.getLogger("TradingBot")

class Scanner:
    def __init__(self, client):
        self.client = client
        self.blacklist = ['USDC/USDT', 'BUSD/USDT', 'TUSD/USDT', 'USDP/USDT', 'FDUSD/USDT']

    def get_best_pair(self):
        """
        Fetches top volume pairs and returns the best one for trading.
        """
        try:
            logger.info("🔍 Scanning market for best trading pair...")
            
            # Fetch all tickers
            tickers = self.client.exchange.fetch_tickers()
            
            # Filter for USDT pairs
            usdt_pairs = [
                {'symbol': symbol, 'volume': data['quoteVolume']}
                for symbol, data in tickers.items()
                if symbol.endswith('/USDT') and symbol not in self.blacklist
            ]
            
            # Sort by volume (descending)
            sorted_pairs = sorted(usdt_pairs, key=lambda x: x['volume'], reverse=True)
            
            # Get top N pairs
            top_pairs = sorted_pairs[:config.SCANNER_TOP_N]
            
            # For now, simply return the highest volume pair
            # In the future, we can add volatility checks here
            best_pair = top_pairs[0]['symbol']
            
            logger.info(f"✅ Best pair found: {best_pair} (Volume: {top_pairs[0]['volume']:,.0f} USDT)")
            return best_pair

        except Exception as e:
            logger.error(f"❌ Market Scan failed: {e}")
            return None
