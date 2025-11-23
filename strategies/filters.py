import logging
import pandas as pd

logger = logging.getLogger("TrendFilter")

class TrendFilter:
    def __init__(self, client, symbol, timeframe):
        self.client = client
        self.symbol = symbol
        self.timeframe = timeframe
        self.ema_period = 200

    def check_trend(self):
        """
        Fetches data and determines the trend based on EMA 200.
        Returns:
            tuple: (trend_status, current_price, ema_value)
            trend_status: 'UPTREND', 'DOWNTREND', or 'NEUTRAL'
        """
        try:
            df = self.client.fetch_ohlcv(self.symbol, self.timeframe)
            if df is not None and not df.empty:
                # Calculate EMA 200 manually
                df['ema_200'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
                
                ema_value = df.iloc[-1]['ema_200']
                current_price = df.iloc[-1]['close']
                
                if current_price > ema_value:
                    return 'UPTREND', current_price, ema_value
                else:
                    return 'DOWNTREND', current_price, ema_value
            
            return 'NEUTRAL', 0.0, 0.0
            
        except Exception as e:
            logger.error(f"Error checking trend: {e}")
            return 'NEUTRAL', 0.0, 0.0
