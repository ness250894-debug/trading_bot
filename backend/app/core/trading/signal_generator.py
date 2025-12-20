"""
Signal Generator Module

Handles signal generation and parsing from strategies.
Extracted from bot.py for better modularity and testability.
"""
import logging

logger = logging.getLogger("TradingBot")


class SignalGenerator:
    """Generates and parses trading signals from strategies"""
    
    def __init__(self, strategy, user_id):
        """
        Initialize signal generator.
        
        Args:
            strategy: Strategy instance
            user_id: User ID for logging
        """
        self.strategy = strategy
        self.user_id = user_id
        self.logger = logger
    
    def generate_and_parse_signal(self, df, strategy_params=None):
        """
        Generate signal from strategy and parse result.
        
        Args:
            df: DataFrame with OHLCV data
            strategy_params: Strategy parameters for logging
            
        Returns:
            Tuple of (signal, score, details, log_message)
            - signal: 'long', 'short', or 'hold'
            - score: Signal strength score
            - details: Additional signal details dict
            - log_message: Formatted log message
        """
        try:
            signal_result = self.strategy.generate_signal(df)
            
            # Parse Signal Result (Handle dict vs string)
            if isinstance(signal_result, dict):
                raw_signal = signal_result.get('signal', 'HOLD').upper()
                score = signal_result.get('score', 0)
                details = signal_result.get('details', {})
            else:
                raw_signal = str(signal_result).upper()
                score = 0
                details = {}
            
            # Normalize to 'long'/'short' for internal logic
            if raw_signal == 'BUY':
                signal = 'long'
            elif raw_signal == 'SELL':
                signal = 'short'
            else:
                signal = 'hold'

            # Format Log Message for UI
            details_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
            log_msg = f"2. 📊 [User {self.user_id}] Signal: {raw_signal} (Score: {score})"
            if details_str:
                log_msg += f" | {details_str}"
            
            # Add current strategy params to log for full visibility
            if strategy_params:
                params_str = ", ".join([f"{k}={v}" for k, v in strategy_params.items()])
                log_msg += f" | Params: [{params_str}]"
            
            self.logger.info(log_msg)
            
            return signal, score, details, log_msg

        except Exception as e:
            self.logger.error(f"❌ User {self.user_id} signal generation failed: {type(e).__name__}: {e}")
            raise
