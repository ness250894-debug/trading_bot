from fastapi import APIRouter, HTTPException, Request
from ..core.database import DuckDBHandler
import logging

from ..core import auth
from fastapi import Depends
from ..core.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger("API.Trades")
from ..core.database import db

@router.get("/trades")
@limiter.limit("10/minute")
async def get_trades(request: Request, limit: int = 50, current_user: dict = Depends(auth.get_current_user)):
    try:
        trades = db.get_trades(limit=limit, user_id=current_user['id'])
        return trades
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trades")

@router.delete("/trades")
@limiter.limit("10/minute")
async def clear_trades(request: Request, current_user: dict = Depends(auth.get_current_user)):
    try:
        success = db.clear_trades(user_id=current_user['id'])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear trades")
        return {"status": "success", "message": "Trade history cleared"}
    except Exception as e:
        logger.error(f"Error clearing trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear trades")
