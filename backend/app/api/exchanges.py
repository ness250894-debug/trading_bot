"""
API endpoints for exchange management.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from ..core.exchange.exchange_factory import ExchangeFactory
from ..core.database import DuckDBHandler

router = APIRouter()
db = DuckDBHandler()


@router.get("/exchanges", tags=["exchanges"])
async def get_supported_exchanges() -> Dict:
    """
    Get list of supported exchanges with their capabilities.
    
    Returns:
        Dictionary with exchanges list and count
    """
    try:
        # Always use ExchangeFactory as the authoritative source
        # This ensures consistency with the API keys whitelist and available exchange clients
        exchanges = ExchangeFactory.get_exchange_info()
        
        return {
            "exchanges": exchanges,
            "count": len(exchanges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchanges/{exchange_name}", tags=["exchanges"])
async def get_exchange_info(exchange_name: str) -> Dict:
    """
    Get information about a specific exchange.
    
    Args:
        exchange_name: Name of the exchange
        
    Returns:
        Exchange information
    """
    try:
        if not ExchangeFactory.is_supported(exchange_name):
            raise HTTPException(
                status_code=404,
                detail=f"Exchange '{exchange_name}' is not supported"
            )
        
        # Get full list and filter
        all_exchanges = ExchangeFactory.get_exchange_info()
        exchange_info = next(
            (ex for ex in all_exchanges if ex['name'] == exchange_name.lower()),
            None
        )
        
        if not exchange_info:
            raise HTTPException(
                status_code=404,
                detail=f"Exchange '{exchange_name}' not found"
            )
        
        return exchange_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
