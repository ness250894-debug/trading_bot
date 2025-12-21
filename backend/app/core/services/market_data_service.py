import logging
import asyncio
from ..database import DuckDBHandler
from ..exchange import ExchangeClient
from .. import config

logger = logging.getLogger("Core.MarketDataService")

class MarketDataService:
    def __init__(self):
        self.db = DuckDBHandler()
        
    async def sync_supported_symbols(self):
        """
        Fetch all available symbols from the default exchange (Bybit)
        and update the supported_symbols table.
        """
        logger.info("Starting supported symbols sync...")
        try:
            # Use default exchange client (Bybit)
            client = ExchangeClient(config.API_KEY, config.API_SECRET)
            
            # Run blocking call in executor
            loop = asyncio.get_running_loop()
            markets = await loop.run_in_executor(None, client.exchange.load_markets)
            
            if not markets:
                logger.warning("No markets found during sync!")
                return
            
            # Filter for valid pairs (e.g., USDT pairs, active)
            # Bybit/CCXT returns a dict of market objects
            symbols = []
            for symbol, market in markets.items():
                if market.get('active', True) and '/USDT' in symbol:
                    symbols.append(symbol)
            
            logger.info(f"Found {len(symbols)} active USDT pairs.")
            
            # Update DB
            added, removed = self.db.system_repo.update_supported_symbols(symbols)
            logger.info(f"Sync complete. Added: {added}, Removed/Marked Inactive: {removed}")
            
        except Exception as e:
            logger.error(f"Failed to sync supported symbols: {e}")

market_data_service = MarketDataService()
