"""
AI-Powered Sentiment Analysis Service
Uses Google Gemini API (free tier) to analyze crypto market sentiment from news/social media.
"""
import os
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from .config import GEMINI_API_KEY, CRYPTOPANIC_API_KEY
from .news_service import news_service

logger = logging.getLogger("SentimentAnalyzer")


class SentimentAnalyzer:
    """Analyzes market sentiment using AI and news sources."""
    
    # Rate limiting: 50 calls per day (UTC reset)
    MAX_DAILY_CALLS = 50
    
    def __init__(self):
        """Initialize sentiment analyzer with Gemini API."""
        self.gemini_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
        self.cryptopanic_key = CRYPTOPANIC_API_KEY or os.getenv('CRYPTOPANIC_API_KEY')
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
            self.enabled = True
            logger.info("Gemini AI Sentiment Analyzer initialized")
        else:
            self.enabled = False
            logger.warning("Gemini API key not found - sentiment analysis disabled")
        
        if not self.cryptopanic_key:
            logger.warning("CryptoPanic API key not found - news fetching disabled")

        # Cache for sentiment results (avoid re-analyzing same data)
        self.cache = {}
        self.cache_duration = timedelta(hours=1) # Cache for 1 hour
        
        # Rate limiting state
        self.daily_requests = 0
        self.last_reset_date = datetime.now(timezone.utc).date()
        self._load_rate_limit_state()
    
    def _load_rate_limit_state(self):
        """Load rate limiting state from file."""
        import json
        state_file = os.path.join(os.path.dirname(__file__), '.gemini_rate_limit.json')
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    saved_date_str = data.get('last_reset_date')
                    
                    if saved_date_str:
                        saved_date = datetime.fromisoformat(saved_date_str).date()
                        current_date = datetime.now(timezone.utc).date()
                        
                        if saved_date == current_date:
                            self.daily_requests = data.get('daily_requests', 0)
                            self.last_reset_date = saved_date
                        else:
                            # New day, reset counter
                            self.daily_requests = 0
                            self.last_reset_date = current_date
                            self._save_rate_limit_state() # Save reset immediately
                    
                    logger.debug(f"Loaded rate limit state: {self.daily_requests}/{self.MAX_DAILY_CALLS} used today")
        except Exception as e:
            logger.warning(f"Could not load rate limit state: {e}")
    
    def _save_rate_limit_state(self):
        """Save rate limiting state to file."""
        import json
        state_file = os.path.join(os.path.dirname(__file__), '.gemini_rate_limit.json')
        try:
            data = {
                'daily_requests': self.daily_requests,
                'last_reset_date': self.last_reset_date.isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Could not save rate limit state: {e}")
    
    def _can_call_api(self) -> tuple:
        """
        Check if we can make a Gemini API call based on daily rate limiting.
        
        Returns:
            Tuple of (can_call: bool, message: str)
        """
        # Check for day reset
        current_date = datetime.now(timezone.utc).date()
        if current_date > self.last_reset_date:
            self.daily_requests = 0
            self.last_reset_date = current_date
            self._save_rate_limit_state()
            
        if self.daily_requests >= self.MAX_DAILY_CALLS:
            return False, f"Daily limit reached ({self.daily_requests}/{self.MAX_DAILY_CALLS})"
        
        return True, "OK"
    
    def _record_api_call(self):
        """Record that an API call was made."""
        self.daily_requests += 1
        self._save_rate_limit_state()
    
    def fetch_cryptopanic_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch latest news from CryptoPanic.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            limit: Number of news items to fetch
            
        Returns:
            List of news items
        """
        if not self.cryptopanic_key:
            return []

        try:
            # CryptoPanic API
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': self.cryptopanic_key,
                'currencies': symbol,
                'kind': 'news',
                'filter': 'hot'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])[:limit]
                
                news = []
                for item in results:
                    news.append({
                        'title': item.get('title', ''),
                        'published': item.get('published_at', ''),
                        'source': item.get('source', {}).get('title', 'Unknown'),
                        'url': item.get('url', '')
                    })
                
                logger.info(f"Fetched {len(news)} news items for {symbol}")
                return news
            else:
                logger.error(f"CryptoPanic API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            return []
    
    def fetch_reddit_sentiment(self, symbol: str) -> List[str]:
        """
        Fetch recent Reddit posts about a cryptocurrency.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            List of post titles/text
        """
        try:
            # Use Reddit JSON API (no auth needed for read-only)
            subreddit = 'cryptocurrency'
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                'q': f'{symbol} OR ${symbol}',
                'sort': 'hot',
                'limit': 10,
                't': 'day'
            }
            
            headers = {'User-Agent': 'TradingBot/1.0'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                titles = []
                for post in posts:
                    post_data = post.get('data', {})
                    titles.append(post_data.get('title', ''))
                
                logger.info(f"Fetched {len(titles)} Reddit posts for {symbol}")
                return titles
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {e}")
            return []
    
    def analyze_with_gemini(self, symbol: str, news_items: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment using Google Gemini AI.
        
        Args:
            symbol: Crypto symbol
            news_items: List of news titles/text
            
        Returns:
            Sentiment analysis result
        """
        if not self.enabled:
            return {
                'sentiment': 'neutral',
                'score': 50,
                'confidence': 0,
                'summary': 'AI analysis unavailable'
            }
        
        # Check rate limiting
        # Check rate limiting
        can_call, message = self._can_call_api()
        if not can_call:
            logger.debug(f"Rate limited: {message}")
            # Return neutral analysis silently - no visible message to users
            return {
                'sentiment': 'neutral',
                'score': 50,
                'confidence': 50,
                'summary': message,
                'signal_strength': 'moderate',
                'topics': ['Market Analysis', 'Daily Limit Reached']
            }
        
        try:
            # Prepare prompt for Gemini
            news_text = "\n".join([f"- {item}" for item in news_items[:15]])
            
            prompt = f"""
Analyze the market sentiment for {symbol} cryptocurrency based on the following recent news and social media posts:

{news_text}

Please provide a detailed analysis in JSON format with the following fields:
1. "sentiment": "bullish", "bearish", or "neutral"
2. "score": 0-100 (0=bearish, 100=bullish)
3. "confidence": 0-100
4. "summary": Brief 1-sentence summary
5. "signal_strength": "strong", "moderate", or "weak"
6. "topics": List of top 3 key topics or drivers (e.g., ["ETF Approval", "Regulatory Concerns", "Tech Upgrade"])

Output ONLY valid JSON.
"""
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Record successful API call for rate limiting
            self._record_api_call()
            
            # Clean up response to ensure valid JSON
            text = text.replace('```json', '').replace('```', '').strip()
            
            import json
            try:
                data = json.loads(text)
                sentiment = data.get('sentiment', 'neutral').lower()
                score = int(data.get('score', 50))
                confidence = int(data.get('confidence', 50))
                summary = data.get('summary', 'No summary available')
                signal_strength = data.get('signal_strength', 'moderate')
                topics = data.get('topics', [])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Gemini JSON response: {text}")
                # Fallback parsing
                sentiment = 'neutral'
                score = 50
                confidence = 0
                summary = "Failed to parse AI response"
                signal_strength = "weak"
                topics = []

            # Ensure score is in valid range
            score = max(0, min(100, score))
            confidence = max(0, min(100, confidence))
            
            result = {
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence,
                'summary': summary,
                'signal_strength': signal_strength,
                'topics': topics,
                'analyzed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Gemini analysis for {symbol}: {sentiment} (score: {score})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing with Gemini: {e}")
            return {
                'sentiment': 'neutral',
                'score': 50,
                'confidence': 0,
                'summary': f'Analysis error: {str(e)}',
                'signal_strength': 'weak',
                'topics': []
            }
    
    def get_sentiment(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive sentiment analysis for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with sentiment analysis
        """
        # Check cache
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H')}"
        if use_cache and cache_key in self.cache:
            logger.info(f"Using cached sentiment for {symbol}")
            return self.cache[cache_key]
        
        logger.info(f"Analyzing sentiment for {symbol}")
        
        # Combine all news items with timestamps
        all_candidates = []
        
        # 1. CryptoPanic
        for item in cryptopanic_news:
            # Parse timestamp if possible, else use current time
            ts = datetime.now().timestamp()
            try:
                if item.get('published'):
                    # CryptoPanic format usually ISO
                    ts = datetime.fromisoformat(item['published'].replace('Z', '+00:00')).timestamp()
            except:
                pass
            
            all_candidates.append({
                'title': item.get('title'),
                'source': item.get('source', 'CryptoPanic'),
                'timestamp': ts,
                'summary': '',
                'url': item.get('url', '')
            })
            
        # 2. Reddit
        for title in reddit_posts:
            all_candidates.append({
                'title': title,
                'source': 'Reddit',
                'timestamp': datetime.now().timestamp(), # Approximate
                'summary': '',
                'url': ''
            })
            
        # 3. Aggregated News (Service)
        try:
            aggregated_news = news_service.get_aggregated_news(symbols=symbol, limit=20)
            for item in aggregated_news:
                all_candidates.append({
                    'title': item.get('title'),
                    'source': item.get('source', 'NewsAPI'),
                    'timestamp': item.get('timestamp', datetime.now().timestamp()),
                    'summary': item.get('summary', ''),
                    'url': item.get('url', '')
                })
        except Exception as e:
            logger.error(f"Error fetching aggregated news: {e}")

        # Unique by title
        unique_candidates = []
        seen = set()
        for item in all_candidates:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_candidates.append(item)
                
        # Sort by timestamp descending
        unique_candidates.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Prepare for Gemini
        news_items_text = []
        for item in unique_candidates[:20]:
            text = item['title']
            if item['summary']:
                text += f": {item['summary']}"
            news_items_text.append(text)
            
        if not news_items_text:
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'score': 50,
                'confidence': 0,
                'summary': 'No recent news found',
                'news_count': 0,
                'sources': []
            }
        
        # Analyze with Gemini
        analysis = self.analyze_with_gemini(symbol, news_items_text)
        
        # Identify sources used
        used_sources = sorted(list(set(item['source'] for item in unique_candidates[:20])))
        
        # Display News (CryptoPanic format)
        display_news = []
        for item in unique_candidates[:10]:
            display_news.append({
                'title': item['title'],
                'published': datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M'),
                'source': item['source'],
                'url': item['url']
            })

        # Build complete result
        result = {
            'symbol': symbol,
            'sentiment': analysis['sentiment'],
            'score': analysis['score'],
            'confidence': analysis['confidence'],
            'summary': analysis['summary'],
            'signal_strength': analysis.get('signal_strength', 'moderate'),
            'topics': analysis.get('topics', []),
            'news_count': len(unique_candidates),
            'recent_news': display_news,
            'analyzed_at': datetime.now().isoformat()
        }
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def get_sentiment_emoji(self, score: int) -> str:
        """
        Get emoji representation of sentiment score.
        
        Args:
            score: Sentiment score (0-100)
            
        Returns:
            Emoji string
        """
        if score >= 70:
            return "🚀 Extremely Bullish"
        elif score >= 60:
            return "📈 Bullish"
        elif score >= 45:
            return "➡️ Slightly Bullish"
        elif score >= 40:
            return "😐 Neutral"
        elif score >= 30:
            return "⬅️ Slightly Bearish"
        elif score >= 20:
            return "📉 Bearish"
        else:
            return "💀 Extremely Bearish"
