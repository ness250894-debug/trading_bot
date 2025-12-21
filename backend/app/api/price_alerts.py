from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, validator
from typing import Optional
import logging
from ..core import auth
from ..core.database import DuckDBHandler
from ..core.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger("API.PriceAlerts")
db = DuckDBHandler()

class PriceAlertCreate(BaseModel):
    symbol: str
    condition: str
    price_target: float

    @validator('condition')
    def validate_condition(cls, v):
        if v not in ['above', 'below']:
            raise ValueError('Condition must be "above" or "below"')
        return v
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v:
            raise ValueError('Symbol cannot be empty')
        return v.upper()

@router.get("/alerts")
@limiter.limit("30/minute")
async def get_alerts(request: Request, active_only: bool = True, current_user: dict = Depends(auth.get_current_user)):
    """Get user's price alerts."""
    try:
        alerts = db.get_alerts(current_user['id'], active_only=active_only)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

@router.post("/alerts")
@limiter.limit("20/minute")
async def create_alert(request: Request, alert: PriceAlertCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a new price alert."""
    try:
        alert_id = db.create_alert(
            user_id=current_user['id'],
            symbol=alert.symbol,
            condition=alert.condition,
            price_target=alert.price_target
        )
        
        if not alert_id:
            raise HTTPException(status_code=500, detail="Failed to create alert")
            
        return {"status": "success", "alert_id": alert_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")

@router.delete("/alerts/{alert_id}")
@limiter.limit("30/minute")
async def delete_alert(request: Request, alert_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a price alert."""
    try:
        if db.delete_alert(current_user['id'], alert_id):
            return {"status": "success", "message": "Alert deleted"}
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")
