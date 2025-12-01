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
        Now includes volatility, spread, and volume filters.
        """
        try:
            logger.info("🔍 Scanning market for best trading pair...")
            
            # Fetch all tickers
            tickers = self.client.exchange.fetch_tickers()
            
            # Filter for USDT pairs with quality checks
            quality_pairs = []
            for symbol, data in tickers.items():
                if not symbol.endswith('/USDT') or symbol in self.blacklist:
                    continue
                    
                # Extract metrics
                volume = data.get('quoteVolume', 0)
                change_pct = data.get('percentage', 0)  # 24h % change
                bid = data.get('bid', 0)
                ask = data.get('ask', 0)
                
                # Volume filter: minimum $1M USDT
                if volume < 1_000_000:
                    continue
                    
                # Volatility filter: minimum 2% 24h change (absolute)
                if abs(change_pct) < 2.0:
                    continue
                    
                # Spread filter: max 0.5% spread
                if bid > 0 and ask > 0:
                    spread_pct = ((ask - bid) / bid) * 100
                    if spread_pct > 0.5:
                        continue
                
                quality_pairs.append({
                    'symbol': symbol,
                    'volume': volume,
                    'volatility': abs(change_pct),
                    'spread': spread_pct if bid > 0 and ask > 0 else 0
                })
            
            if not quality_pairs:
                logger.warning("⚠️ No pairs met quality criteria")
                return None
            
            # Sort by volume (descending)
            sorted_pairs = sorted(quality_pairs, key=lambda x: x['volume'], reverse=True)
            
            # Get top N pairs
            top_pairs = sorted_pairs[:config.SCANNER_TOP_N]
            
            # Return the highest volume pair that meets all criteria
            best_pair = top_pairs[0]
            
            logger.info(f"✅ Best pair: {best_pair['symbol']}")
            logger.info(f"   Volume: ${best_pair['volume']:,.0f} | Volatility: {best_pair['volatility']:.2f}% | Spread: {best_pair['spread']:.3f}%")
            return best_pair['symbol']

        except Exception as e:
            logger.error(f"❌ Market Scan failed: {e}")
            return None
