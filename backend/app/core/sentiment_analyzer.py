"""
AI-Powered Sentiment Analysis Service
Uses Google Gemini API (free tier) to analyze crypto market sentiment from news/social media.
"""
import os
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from .config import GEMINI_API_KEY, CRYPTOPANIC_API_KEY

logger = logging.getLogger("SentimentAnalyzer")


class SentimentAnalyzer:
    """Analyzes market sentiment using AI and news sources."""
    
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
        self.cache_duration = timedelta(hours=1)
    
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
        
        # Gather news from multiple sources
        news_items = []
        
        # CryptoPanic news
        cryptopanic_news = self.fetch_cryptopanic_news(symbol)
        news_items.extend([item['title'] for item in cryptopanic_news])
        
        # Reddit posts
        reddit_posts = self.fetch_reddit_sentiment(symbol)
        news_items.extend(reddit_posts)
        
        if not news_items:
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
        analysis = self.analyze_with_gemini(symbol, news_items)
        
        # Build complete result
        # Build complete result
        result = {
            'symbol': symbol,
            'sentiment': analysis['sentiment'],
            'score': analysis['score'],
            'confidence': analysis['confidence'],
            'summary': analysis['summary'],
            'signal_strength': analysis.get('signal_strength', 'moderate'),
            'topics': analysis.get('topics', []),
            'news_count': len(news_items),
            'sources': ['CryptoPanic', 'Reddit'],
            'recent_news': cryptopanic_news[:5],  # Top 5 news items
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
