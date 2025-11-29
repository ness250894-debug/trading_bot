"""
API endpoints for AI-powered sentiment analysis.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..core.sentiment_analyzer import SentimentAnalyzer

router = APIRouter()

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalyzer()


@router.get("/sentiment/{symbol}", tags=["ai-insights"])
async def get_sentiment_analysis(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get AI-powered sentiment analysis for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')
        use_cache: Whether to use cached results (faster, default: True)
        
    Returns:
        Sentiment analysis with score, confidence, and recent news
    """
    try:
        # Normalize symbol (remove common suffixes)
        symbol = symbol.upper().replace('USDT', '').replace('USD', '').replace('/','')
        
        result = sentiment_analyzer.get_sentiment(symbol, use_cache=use_cache)
        
        # Add emoji representation
        result['emoji'] = sentiment_analyzer.get_sentiment_emoji(result['score'])
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@router.get("/sentiment/{symbol}/simple", tags=["ai-insights"])
async def get_simple_sentiment(symbol: str):
    """
    Get simplified sentiment (just the score and emoji) for quick display.
    
    Args:
        symbol: Cryptocurrency symbol
        
    Returns:
        Simple sentiment object
    """
    try:
        symbol = symbol.upper().replace('USDT', '').replace('USD', '').replace('/','')
        
        result = sentiment_analyzer.get_sentiment(symbol, use_cache=True)
        
        return {
            'symbol': symbol,
            'sentiment': result['sentiment'],
            'score': result['score'],
            'emoji': sentiment_analyzer.get_sentiment_emoji(result['score']),
            'confidence': result['confidence']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/news/{symbol}", tags=["ai-insights"])
async def get_crypto_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50, description="Number of news items")
):
    """
    Get latest news for a cryptocurrency from multiple sources.
    
    Args:
        symbol: Cryptocurrency symbol
        limit: Number of news items to return
        
    Returns:
        List of news items with title, source, and URL
    """
    try:
        symbol = symbol.upper().replace('USDT', '').replace('USD', '').replace('/','')
        
        news = sentiment_analyzer.fetch_cryptopanic_news(symbol, limit=limit)
        
        return {
            'symbol': symbol,
            'count': len(news),
            'news': news
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )


@router.post("/sentiment/analyze", tags=["ai-insights"])
async def manual_sentiment_analysis(data: dict):
    """
    Manually trigger sentiment analysis with custom text.
    
    Args:
        data: Dictionary with 'symbol' and 'texts' (list of strings)
        
    Returns:
        Sentiment analysis result
    """
    try:
        symbol = data.get('symbol', 'CRYPTO')
        texts = data.get('texts', [])
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        analysis = sentiment_analyzer.analyze_with_gemini(symbol, texts)
        
        return {
            'symbol': symbol,
            **analysis,
            'emoji': sentiment_analyzer.get_sentiment_emoji(analysis['score'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
