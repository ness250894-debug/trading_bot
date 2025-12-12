"""
Indicator Cache
Caches calculated technical indicators between trading loops
Only recalculates when new candles arrive
"""
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger("IndicatorCache")


class IndicatorCache:
    """
    Caches calculated indicators to avoid redundant computations.
    Invalidates when new candle data arrives.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0
        }
    
    def _get_data_hash(self, df: pd.DataFrame) -> str:
        """Generate a hash from DataFrame to detect changes"""
        if df is None or df.empty:
            return ""
        
        # Use last few rows and key columns for fast hashing
        key_data = df.tail(5)[['open', 'high', 'low', 'close', 'volume']].to_string()
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _get_cache_key(self, symbol: str, timeframe: str, strategy_name: str) -> str:
        """Generate cache key for symbol/timeframe/strategy combination"""
        return f"{symbol}:{timeframe}:{strategy_name}"
    
    def get(self, symbol: str, timeframe: str, strategy_name: str, 
            current_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Get cached indicators if data hasn't changed.
        
        Returns:
            Cached indicators dict or None if cache miss
        """
        cache_key = self._get_cache_key(symbol, timeframe, strategy_name)
        current_hash = self._get_data_hash(current_df)
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached.get("data_hash") == current_hash:
                self._stats["hits"] += 1
                logger.debug(f"Cache HIT: {cache_key}")
                return cached.get("indicators")
        
        self._stats["misses"] += 1
        logger.debug(f"Cache MISS: {cache_key}")
        return None
    
    def set(self, symbol: str, timeframe: str, strategy_name: str,
            df: pd.DataFrame, indicators: Dict[str, Any]):
        """
        Store calculated indicators in cache.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            strategy_name: Strategy name
            df: Current OHLCV DataFrame
            indicators: Calculated indicator values
        """
        cache_key = self._get_cache_key(symbol, timeframe, strategy_name)
        data_hash = self._get_data_hash(df)
        
        self._cache[cache_key] = {
            "data_hash": data_hash,
            "indicators": indicators,
            "cached_at": datetime.now().isoformat(),
            "candle_count": len(df) if df is not None else 0
        }
        
        self._stats["saves"] += 1
        logger.debug(f"Cached indicators for {cache_key}")
    
    def invalidate(self, symbol: str = None, timeframe: str = None, 
                   strategy_name: str = None):
        """
        Invalidate cache entries.
        
        Args:
            symbol: Optional - invalidate for specific symbol
            timeframe: Optional - invalidate for specific timeframe
            strategy_name: Optional - invalidate for specific strategy
        """
        if symbol and timeframe and strategy_name:
            cache_key = self._get_cache_key(symbol, timeframe, strategy_name)
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Invalidated cache: {cache_key}")
        elif symbol:
            keys_to_delete = [k for k in self._cache if k.startswith(f"{symbol}:")]
            for k in keys_to_delete:
                del self._cache[k]
            logger.debug(f"Invalidated {len(keys_to_delete)} cache entries for {symbol}")
        else:
            self._cache.clear()
            logger.debug("Cleared entire indicator cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "entries": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "saves": self._stats["saves"],
            "hit_rate": f"{hit_rate:.1f}%"
        }
    
    def clear(self):
        """Clear all cached indicators"""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "saves": 0}


# Global singleton instance
indicator_cache = IndicatorCache()
