"""
Market News API Endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional
import logging

from ..core.news_service import news_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/news")
async def get_market_news(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols (e.g., 'BTC,ETH')"),
    limit: int = Query(15, ge=1, le=50, description="Number of news items to return")
):
    """
    Get aggregated market news from multiple sources
    
    - **symbols**: Comma-separated list of trading symbols (default: BTC,ETH)
    - **limit**: Maximum number of news items to return (default: 15, max: 50)
    
    Returns news from:
    - CryptoCompare (FREE - no API key needed)
    - CoinDesk RSS (FREE - no API key needed) 
    - Alpha Vantage (if API key is configured)
    - Finnhub (if API key is configured)
    - Marketaux (if API key is configured)
    """
    try:
        news_items = news_service.get_aggregated_news(symbols=symbols, limit=limit)
        
        return {
            "success": True,
            "count": len(news_items),
            "news": news_items
        }
    
    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        return {
            "success": False,
            "error": str(e),
            "news": []
        }


@router.get("/news/sources")
async def get_news_sources():
    """
    Get information about available news sources
    """
    sources = [
        {
            "name": "CryptoCompare",
            "status": "active",
            "requires_api_key": False,
            "description": "Cryptocurrency news aggregator"
        },
        {
            "name": "CoinDesk RSS", 
            "status": "active",
            "requires_api_key": False,
            "description": "Leading cryptocurrency news outlet"
        },
        {
            "name": "Alpha Vantage",
            "status": "configured" if news_service.alpha_vantage_key else "not_configured",
            "requires_api_key": True,
            "description": "Financial market data and news with AI sentiment"
        },
        {
            "name": "Finnhub",
            "status": "configured" if news_service.finnhub_key else "not_configured",
            "requires_api_key": True,
            "description": "Real-time market news and data"
        },
        {
            "name": "Marketaux",
            "status": "configured" if news_service.marketaux_key else "not_configured",
            "requires_api_key": True,
            "description": "Global financial news with sentiment analysis"
        }
    ]
    
    return {
        "sources": sources,
        "active_count": sum(1 for s in sources if s["status"] == "active" or s["status"] == "configured")
    }
