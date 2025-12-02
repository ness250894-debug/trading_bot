"""
Indicator calculation library for JSON-based strategies.
Provides standardized indicator calculations that can be referenced in JSON configs.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


class IndicatorLibrary:
    """Library of technical indicators for strategy building."""
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, source: str = 'close') -> pd.DataFrame:
        """
        Calculate Simple Moving Average.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            source: Column to calculate from
            
        Returns:
            DataFrame with SMA column added
        """
        column_name = f'sma_{period}'
        df[column_name] = df[source].rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, source: str = 'close') -> pd.DataFrame:
        """
        Calculate Exponential Moving Average.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            source: Column to calculate from
            
        Returns:
            DataFrame with EMA column added
        """
        column_name = f'ema_{period}'
        df[column_name] = df[source].ewm(span=period, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, source: str = 'close') -> pd.DataFrame:
        """
        Calculate Relative Strength Index.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            source: Column to calculate from
            
        Returns:
            DataFrame with RSI column added
        """
        column_name = f'rsi_{period}'
        
        delta = df[source].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df[column_name] = rsi.fillna(50)
        return df
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, source: str = 'close') -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            df: OHLCV dataframe
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            source: Column to calculate from
            
        Returns:
            DataFrame with MACD, Signal, and Histogram columns added
        """
        exp1 = df[source].ewm(span=fast, adjust=False).mean()
        exp2 = df[source].ewm(span=slow, adjust=False).mean()
        
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        df['macd'] = macd
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram
        
        return df
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, source: str = 'close') -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            std_dev: Standard deviation multiplier
            source: Column to calculate from
            
        Returns:
            DataFrame with BB upper, middle, lower columns added
        """
        sma = df[source].rolling(window=period).mean()
        std = df[source].rolling(window=period).std()
        
        df[f'bb_upper_{period}'] = sma + (std * std_dev)
        df[f'bb_middle_{period}'] = sma
        df[f'bb_lower_{period}'] = sma - (std * std_dev)
        
        return df
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average True Range.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            
        Returns:
            DataFrame with ATR column added
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        df[f'atr_{period}'] = true_range.rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            df: OHLCV dataframe
            k_period: %K period
            d_period: %D period (smoothing)
            
        Returns:
            DataFrame with Stochastic %K and %D columns added
        """
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        
        df['stoch_k'] = k
        df['stoch_d'] = d
        
        return df
    
    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Commodity Channel Index.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            
        Returns:
            DataFrame with CCI column added
        """
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        df[f'cci_{period}'] = (tp - sma_tp) / (0.015 * mad)
        return df
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate On-Balance Volume.
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            DataFrame with OBV column added
        """
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        df['obv'] = obv
        return df

    @staticmethod
    def calculate_roc(df: pd.DataFrame, period: int = 10, source: str = 'close') -> pd.DataFrame:
        """
        Calculate Rate of Change.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            source: Column to calculate from
            
        Returns:
            DataFrame with ROC column added
        """
        column_name = f'roc_{period}'
        df[column_name] = df[source].pct_change(periods=period) * 100
        return df

    @staticmethod
    def calculate_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Volume Moving Average.
        
        Args:
            df: OHLCV dataframe
            period: Lookback period
            
        Returns:
            DataFrame with Volume MA column added
        """
        column_name = f'volume_ma_{period}'
        df[column_name] = df['volume'].rolling(window=period).mean()
        return df
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about all available indicators.
        
        Returns:
            Dictionary of indicator metadata
        """
        return {
            'sma': {
                'name': 'Simple Moving Average',
                'category': 'trend',
                'params': {
                    'period': {'type': 'int', 'default': 20, 'min': 2, 'max': 200},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'ema': {
                'name': 'Exponential Moving Average',
                'category': 'trend',
                'params': {
                    'period': {'type': 'int', 'default': 20, 'min': 2, 'max': 200},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'rsi': {
                'name': 'Relative Strength Index',
                'category': 'momentum',
                'params': {
                    'period': {'type': 'int', 'default': 14, 'min': 2, 'max': 50},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'macd': {
                'name': 'MACD',
                'category': 'momentum',
                'params': {
                    'fast': {'type': 'int', 'default': 12, 'min': 2, 'max': 50},
                    'slow': {'type': 'int', 'default': 26, 'min': 5, 'max': 100},
                    'signal': {'type': 'int', 'default': 9, 'min': 2, 'max': 50},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'bollinger_bands': {
                'name': 'Bollinger Bands',
                'category': 'volatility',
                'params': {
                    'period': {'type': 'int', 'default': 20, 'min': 5, 'max': 100},
                    'std_dev': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 5.0, 'step': 0.1},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'atr': {
                'name': 'Average True Range',
                'category': 'volatility',
                'params': {
                    'period': {'type': 'int', 'default': 14, 'min': 2, 'max': 50}
                }
            },
            'stochastic': {
                'name': 'Stochastic Oscillator',
                'category': 'momentum',
                'params': {
                    'k_period': {'type': 'int', 'default': 14, 'min': 2, 'max': 50},
                    'd_period': {'type': 'int', 'default': 3, 'min': 2, 'max': 20}
                }
            },
            'cci': {
                'name': 'Commodity Channel Index',
                'category': 'momentum',
                'params': {
                    'period': {'type': 'int', 'default': 20, 'min': 2, 'max': 50}
                }
            },
            'obv': {
                'name': 'On-Balance Volume',
                'category': 'volume',
                'params': {}
            },
            'roc': {
                'name': 'Rate of Change',
                'category': 'momentum',
                'params': {
                    'period': {'type': 'int', 'default': 10, 'min': 1, 'max': 50},
                    'source': {'type': 'select', 'default': 'close', 'options': ['open', 'high', 'low', 'close']}
                }
            },
            'volume_ma': {
                'name': 'Volume Moving Average',
                'category': 'volume',
                'params': {
                    'period': {'type': 'int', 'default': 20, 'min': 2, 'max': 200}
                }
            }
        }
