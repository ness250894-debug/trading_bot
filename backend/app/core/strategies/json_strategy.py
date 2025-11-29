"""
JSON Strategy Executor - Interprets and executes JSON-based trading strategies.
Replaces Python-based strategies with secure, portable JSON configuration.
"""
import pandas as pd
import json
from typing import Dict, Any, Optional
from .base import Strategy
from .indicators import IndicatorLibrary
from .conditions import ConditionEvaluator


class JSONStrategyExecutor(Strategy):
    """
    Executes trading strategies defined in JSON format.
    Provides security by eliminating code execution risks.
    """
    
    def __init__(self, json_config: Dict[str, Any]):
        """
        Initialize JSON strategy executor.
        
        Args:
            json_config: Strategy configuration as dictionary
        """
        self.config = json_config
        self.name = json_config.get('name', 'Unnamed Strategy')
        self.description = json_config.get('description', '')
        self.version = json_config.get('version', '1.0.0')
        
        # Parse strategy components
        self.indicators = json_config.get('indicators', [])
        self.buy_conditions = json_config.get('conditions', {}).get('buy', {})
        self.sell_conditions = json_config.get('conditions', {}).get('sell', {})
        
        # Indicator library
        self.indicator_lib = IndicatorLibrary()
        self.condition_eval = ConditionEvaluator()
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate JSON strategy configuration."""
        if not self.config:
            raise ValueError("Empty strategy configuration")
        
        # Validate required fields
        if not self.indicators:
            raise ValueError("Strategy must have at least one indicator")
        
        if not self.buy_conditions and not self.sell_conditions:
            raise ValueError("Strategy must have at least buy or sell conditions")
        
        # Validate indicator types
        available_indicators = self.indicator_lib.get_available_indicators()
        for indicator in self.indicators:
            ind_type = indicator.get('type', '').lower()
            if ind_type not in available_indicators:
                raise ValueError(f"Unknown indicator type: {ind_type}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators defined in strategy.
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            DataFrame with all indicators calculated
        """
        if df is None or df.empty:
            return df
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Calculate each indicator
        for indicator in self.indicators:
            ind_id = indicator.get('id')
            ind_type = indicator.get('type', '').lower()
            params = indicator.get('params', {})
            
            # Call appropriate indicator calculation method
            if ind_type == 'sma':
                df = self.indicator_lib.calculate_sma(df, **params)
            elif ind_type == 'ema':
                df = self.indicator_lib.calculate_ema(df, **params)
            elif ind_type == 'rsi':
                df = self.indicator_lib.calculate_rsi(df, **params)
            elif ind_type == 'macd':
                df = self.indicator_lib.calculate_macd(df, **params)
            elif ind_type == 'bollinger_bands':
                df = self.indicator_lib.calculate_bollinger_bands(df, **params)
            elif ind_type == 'atr':
                df = self.indicator_lib.calculate_atr(df, **params)
            elif ind_type == 'stochastic':
                df = self.indicator_lib.calculate_stochastic(df, **params)
            elif ind_type == 'cci':
                df = self.indicator_lib.calculate_cci(df, **params)
            elif ind_type == 'obv':
                df = self.indicator_lib.calculate_obv(df)
        
        return df
    
    def check_signal(self, current_row, previous_row=None) -> Dict[str, Any]:
        """
        Check trading signal for current row.
        
        Args:
            current_row: Current data row (pd.Series)
            previous_row: Previous data row (optional)
            
        Returns:
            Signal dictionary with signal, score, and details
        """
        # Convert Series to DataFrame for evaluation
        if isinstance(current_row, pd.Series):
            # Create a mini dataframe with current and previous row
            if previous_row is not None and isinstance(previous_row, pd.Series):
                df = pd.DataFrame([previous_row, current_row])
                current_idx = 1
            else:
                df = pd.DataFrame([current_row])
                current_idx = 0
        else:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        signal = 'HOLD'
        score = 0
        details = {}
        
        # Evaluate buy conditions
        if self.buy_conditions:
            buy_signal = self.condition_eval.evaluate_logic(
                self.buy_conditions, df, current_idx
            )
            if buy_signal:
                signal = 'BUY'
                score = 3
                details['buy_triggered'] = True
        
        # Evaluate sell conditions
        if self.sell_conditions:
            sell_signal = self.condition_eval.evaluate_logic(
                self.sell_conditions, df, current_idx
            )
            if sell_signal:
                signal = 'SELL'
                score = 3
                details['sell_triggered'] = True
        
        # Add indicator values to details
        for indicator in self.indicators:
            ind_id = indicator.get('id')
            ind_type = indicator.get('type', '').lower()
            
            # Try to get indicator value from current row
            if ind_type == 'rsi':
                period = indicator.get('params', {}).get('period', 14)
                col_name = f'rsi_{period}'
                if col_name in current_row:
                    details[ind_id] = round(float(current_row[col_name]), 2)
            elif ind_type == 'macd':
                if 'macd' in current_row:
                    details['macd'] = round(float(current_row['macd']), 4)
                if 'macd_signal' in current_row:
                    details['macd_signal'] = round(float(current_row['macd_signal']), 4)
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }
    
    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal from dataframe.
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            Signal dictionary
        """
        if df is None or df.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        # Check signal on last row
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        return self.check_signal(last_row, prev_row)
    
    def populate_buy_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized buy signal generation.
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            DataFrame with 'buy' column populated
        """
        df['buy'] = 0
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Evaluate buy conditions for each row
        for i in range(len(df)):
            if i < 1:
                continue
            
            buy_signal = self.condition_eval.evaluate_logic(
                self.buy_conditions, df, i
            )
            if buy_signal:
                df.loc[df.index[i], 'buy'] = 1
        
        return df
    
    def populate_sell_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized sell signal generation.
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            DataFrame with 'sell' column populated
        """
        df['sell'] = 0
        
        # Calculate indicators (if not already done)
        if not any(col.startswith(('sma_', 'ema_', 'rsi_', 'macd')) for col in df.columns):
            df = self.calculate_indicators(df)
        
        # Evaluate sell conditions for each row
        for i in range(len(df)):
            if i < 1:
                continue
            
            sell_signal = self.condition_eval.evaluate_logic(
                self.sell_conditions, df, i
            )
            if sell_signal:
                df.loc[df.index[i], 'sell'] = 1
        
        return df
    
    def to_json(self) -> str:
        """
        Export strategy configuration as JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.config, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JSONStrategyExecutor':
        """
        Create strategy from JSON string.
        
        Args:
            json_str: JSON strategy configuration
            
        Returns:
            JSONStrategyExecutor instance
        """
        config = json.loads(json_str)
        return cls(config)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get strategy metadata.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'indicator_count': len(self.indicators),
            'has_buy_conditions': bool(self.buy_conditions),
            'has_sell_conditions': bool(self.sell_conditions)
        }
