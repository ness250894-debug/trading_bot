import logging
import asyncio
from ..database import db
from ..exchange import ExchangeClient
from .. import config

logger = logging.getLogger("Core.PriceAlertService")

class PriceAlertService:
    def __init__(self):
        self.db = db
        
    async def check_alerts(self):
        """
        Check all active price alerts against current market prices.
        """
        try:
            alerts = self.db.dashboard_repo.get_all_active_alerts()
            if not alerts:
                return

            # Group unique symbols to minimize API calls
            symbols = list(set(a['symbol'] for a in alerts))
            
            # Fetch prices
            client = ExchangeClient(config.API_KEY, config.API_SECRET)
            current_prices = {}
            
            # Fetch in chunks or one by one? 
            # If supported_symbols is huge, we might need a bulk fetch. 
            # For now, iterate (simple). client.fetch_ticker is cached/rate-limited?
            for symbol in symbols:
                try:
                    ticker = client.fetch_ticker(symbol)
                    if ticker and ticker.get('last'):
                        current_prices[symbol] = ticker['last']
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {symbol}: {e}")
            
            # Check conditions
            for alert in alerts:
                symbol = alert['symbol']
                price = current_prices.get(symbol)
                
                if price is None:
                    continue
                    
                triggered = False
                target = alert['price_target']
                
                if alert['condition'] == 'above' and price > target:
                    triggered = True
                elif alert['condition'] == 'below' and price < target:
                    triggered = True
                    
                if triggered:
                    logger.info(f"🚨 ALERT TRIGGERED: {symbol} is {alert['condition']} {target} (Current: {price})")
                    self.db.dashboard_repo.trigger_alert(alert['id'])
                    # TODO: Send WebSocket notification to user
                    
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")

price_alert_service = PriceAlertService()
