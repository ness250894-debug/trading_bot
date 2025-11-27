from fastapi import APIRouter, HTTPException
from ..core.database import DuckDBHandler
import logging

router = APIRouter()
logger = logging.getLogger("API.Trades")
db = DuckDBHandler()

@router.get("/trades")
async def get_trades(limit: int = 50):
    try:
        df = db.get_trades(limit=limit)
        if df.empty:
            return []
        
        # Convert to list of dicts
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trades")
async def clear_trades():
    try:
        success = db.clear_trades()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear trades")
        return {"status": "success", "message": "Trade history cleared"}
    except Exception as e:
        logger.error(f"Error clearing trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
