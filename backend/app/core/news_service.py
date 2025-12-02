"""
Market News Service
Aggregates financial news from multiple free APIs
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)

class NewsService:
    """Aggregate news from multiple free sources"""
    
    def __init__(self):
        # API Keys from environment (optional for free tiers)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY', '')
        self.marketaux_key = os.getenv('MARKETAUX_API_KEY', '')
        
        # Cache timeout in seconds (5 minutes)
        self.cache_timeout = 300
        
    def _format_time_ago(self, timestamp: str) -> str:
        """Convert timestamp to relative time (e.g., '2h ago')"""
        try:
            # Parse various timestamp formats
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            
            now = datetime.now(timezone.utc)
            diff = now - dt
            
            seconds = diff.total_seconds()
            if seconds < 60:
                return f"{int(seconds)}s ago"
            elif seconds < 3600:
                return f"{int(seconds / 60)}min ago"
            elif seconds < 86400:
                return f"{int(seconds / 3600)}h ago"
            else:
                return f"{int(seconds / 86400)}d ago"
        except Exception as e:
            logger.debug(f"Error formatting timestamp {timestamp}: {e}")
            return "Recently"
    
    def fetch_alpha_vantage_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict]:
        """Fetch news from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return []
        
        try:
            # Use default crypto symbols if none provided
            if not symbols:
                symbols = ['CRYPTO:BTC', 'CRYPTO:ETH']
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ','.join(symbols),
                'apikey': self.alpha_vantage_key,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for item in data.get('feed', [])[:limit]:
                news_items.append({
                    'title': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'source': item.get('source', 'Alpha Vantage'),
                    'url': item.get('url', ''),
                    'time': self._format_time_ago(item.get('time_published', '')),
                    'sentiment': item.get('overall_sentiment_label', 'Neutral'),
                    'providers': ['alpha_vantage']
                })
            
            logger.info(f"Fetched {len(news_items)} news items from Alpha Vantage")
            return news_items
            
        except Exception as e:
            logger.warning(f"Error fetching Alpha Vantage news: {e}")
            return []
    
    def fetch_finnhub_news(self, category: str = 'crypto', limit: int = 10) -> List[Dict]:
        """Fetch news from Finnhub (Company News or Market News)"""
        if not self.finnhub_key:
            return []
        
        try:
            url = "https://finnhub.io/api/v1/news"
            params = {
                'category': category,  # crypto, general, forex
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for item in data[:limit]:
                news_items.append({
                    'title': item.get('headline', ''),
                    'summary': item.get('summary', '')[:200] + '...',
                    'source': item.get('source', 'Finnhub'),
                    'url': item.get('url', ''),
                    'time': self._format_time_ago(str(item.get('datetime', ''))),
                    'sentiment': 'Neutral',
                    'providers': ['finnhub']
                })
            
            logger.info(f"Fetched {len(news_items)} news items from Finnhub")
            return news_items
            
        except Exception as e:
            logger.warning(f"Error fetching Finnhub news: {e}")
            return []
    
    def fetch_marketaux_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict]:
        """Fetch news from Marketaux"""
        if not self.marketaux_key:
            return []
        
        try:
            url = "https://api.marketaux.com/v1/news/all"
            params = {
                'api_token': self.marketaux_key,
                'symbols': ','.join(symbols) if symbols else 'BTC,ETH',
                'filter_entities': 'true',
                'language': 'en',
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for item in data.get('data', [])[:limit]:
                news_items.append({
                    'title': item.get('title', ''),
                    'summary': item.get('description', '')[:200] + '...',
                    'source': item.get('source', 'Marketaux'),
                    'url': item.get('url', ''),
                    'time': self._format_time_ago(item.get('published_at', '')),
                    'sentiment': item.get('entities', [{}])[0].get('sentiment_score', 'Neutral'),
                    'providers': ['marketaux']
                })
            
            logger.info(f"Fetched {len(news_items)} news items from Marketaux")
            return news_items
            
        except Exception as e:
            logger.warning(f"Error fetching Marketaux news: {e}")
            return []
    
    def fetch_cryptocompare_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from CryptoCompare (FREE - no API key required)"""
        try:
            url = "https://min-api.cryptocompare.com/data/v2/news/"
            params = {
                'lang': 'EN',
                'sortOrder': 'latest'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for item in data.get('Data', [])[:limit]:
                news_items.append({
                    'title': item.get('title', ''),
                    'summary': item.get('body', '')[:200] + '...',
                    'source': item.get('source', 'CryptoCompare'),
                    'url': item.get('url', ''),
                    'time': self._format_time_ago(str(item.get('published_on', ''))),
                    'sentiment': 'Neutral',
                    'providers': ['cryptocompare']
                })
            
            logger.info(f"Fetched {len(news_items)} news items from CryptoCompare")
            return news_items
            
        except Exception as e:
            logger.warning(f"Error fetching CryptoCompare news: {e}")
            return []
    
    def fetch_coindesk_rss(self, limit: int = 10) -> List[Dict]:
        """Fetch news from CoinDesk RSS feed (FREE - no API key required)"""
        try:
            import feedparser
            
            feed_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
            feed = feedparser.parse(feed_url)
            
            news_items = []
            for entry in feed.entries[:limit]:
                # Parse published time
                import time
                published_time = time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else None
                
                news_items.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', '')[:200] + '...',
                    'source': 'CoinDesk',
                    'url': entry.get('link', ''),
                    'time': self._format_time_ago(str(int(published_time))) if published_time else 'Recently',
                    'sentiment': 'Neutral',
                    'providers': ['coindesk']
                })
            
            logger.info(f"Fetched {len(news_items)} news items from CoinDesk RSS")
            return news_items
            
        except Exception as e:
            logger.warning(f"Error fetching CoinDesk RSS: {e}")
            return []
    
    @lru_cache(maxsize=1)
    def get_aggregated_news(self, symbols: Optional[str] = None, limit: int = 15) -> List[Dict]:
        """
        Aggregate news from all available sources
        This function is cached to avoid excessive API calls
        """
        all_news = []
        
        # Parse symbols
        symbol_list = symbols.split(',') if symbols else ['BTC', 'ETH']
        
        # Fetch from all sources (in order of preference for free tiers)
        # 1. CryptoCompare - FREE, no API key needed
        all_news.extend(self.fetch_cryptocompare_news(limit=5))
        
        # 2. CoinDesk RSS - FREE, no API key needed
        all_news.extend(self.fetch_coindesk_rss(limit=5))
        
        # 3. Alpha Vantage - if API key is set
        if self.alpha_vantage_key:
            all_news.extend(self.fetch_alpha_vantage_news(symbols=symbol_list, limit=5))
        
        # 4. Finnhub - if API key is set
        if self.finnhub_key:
            all_news.extend(self.fetch_finnhub_news(category='crypto', limit=5))
        
        # 5. Marketaux - if API key is set
        if self.marketaux_key:
            all_news.extend(self.fetch_marketaux_news(symbols=symbol_list, limit=5))
        
        # Remove duplicates based on title similarity
        unique_news = []
        seen_titles = set()
        
        for item in all_news:
            # Create a normalized title for comparison
            normalized_title = item['title'].lower().strip()[:50]
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_news.append(item)
        
        # Sort by recency (items with 'ago' in time first)
        unique_news.sort(key=lambda x: x['time'])
        
        logger.info(f"Aggregated {len(unique_news)} unique news items from {len(all_news)} total")
        return unique_news[:limit]


# Global instance
news_service = NewsService()
