from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
import logging
from ..core import auth
from ..core.database import DuckDBHandler
from ..core.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger("API.User")
from ..core.database import db

@router.get("/user/me")
@limiter.limit("20/minute")
async def get_current_user_info(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get current user information including subscription status."""
    try:
        user_id = current_user['id']
        subscription = db.get_subscription(user_id)
        
        return {
            "id": user_id,
            "email": current_user.get('email'),
            "is_admin": current_user.get('is_admin', False),
            "subscription": {
                "plan_id": subscription.get('plan_id') if subscription else None,
                "status": subscription.get('status') if subscription else None,
                "expires_at": subscription.get('expires_at') if subscription else None
            } if subscription else None
        }
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user information")

class TelegramSettingsUpdate(BaseModel):
    chat_id: Optional[str] = None

@router.get("/user/telegram")
@limiter.limit("10/minute")
async def get_telegram_settings(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get user's Telegram notification settings."""
    try:
        user = db.get_user_by_id(current_user['id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "has_telegram": bool(user.get('telegram_chat_id')),
            "chat_id_set": bool(user.get('telegram_chat_id'))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Telegram settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Telegram settings")

@router.post("/user/telegram")
@limiter.limit("10/minute")
async def update_telegram_settings(
    request: Request,
    settings: TelegramSettingsUpdate,
    current_user: dict = Depends(auth.get_current_user)
):
    """Update user's Telegram notification settings."""
    try:
        success = db.update_telegram_settings(
            current_user['id'],
            None, # bot_token is now None (global)
            settings.chat_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update Telegram settings")
        
        return {
            "status": "success",
            "message": "Telegram settings updated successfully" if settings.chat_id else "Telegram settings cleared"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Telegram settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Telegram settings")
