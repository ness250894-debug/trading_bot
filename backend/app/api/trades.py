from fastapi import APIRouter, HTTPException
from ..core.database import DuckDBHandler
import logging

from ..core import auth
from fastapi import Depends

router = APIRouter()
logger = logging.getLogger("API.Trades")
db = DuckDBHandler()

@router.get("/trades")
async def get_trades(limit: int = 50, current_user: dict = Depends(auth.get_current_user)):
    try:
        df = db.get_trades(limit=limit)  # TODO: Filter by user_id when multi-tenant is implemented
        if df.empty:
            return []
        
        # Convert to list of dicts
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trades")

@router.delete("/trades")
async def clear_trades(current_user: dict = Depends(auth.get_current_user)):
    try:
        success = db.clear_trades()  # TODO: Filter by user_id when multi-tenant is implemented
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear trades")
        return {"status": "success", "message": "Trade history cleared"}
    except Exception as e:
        logger.error(f"Error clearing trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear trades")
