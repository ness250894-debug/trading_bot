from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
from ..core import auth
from ..core.database import DuckDBHandler
from ..core.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger("API.TradingGoals")
from ..core.database import db

class TradingGoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_amount: float
    target_date: Optional[str] = None  # ISO format date string

class TradingGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    current_progress: Optional[float] = None
    target_date: Optional[str] = None
    is_completed: Optional[bool] = None

@router.get("/trading-goals")
@limiter.limit("30/minute")
async def get_trading_goals(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get all trading goals for the current user."""
    try:
        user_id = current_user['id']
        goals = db.get_trading_goals(user_id)
        return {"goals": goals}
    except Exception as e:
        logger.error(f"Error fetching trading goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trading goals")

@router.get("/trading-goals/{goal_id}")
@limiter.limit("30/minute")
async def get_trading_goal(
    goal_id: int,
    request: Request,
    current_user: dict = Depends(auth.get_current_user)
):
    """Get a specific trading goal."""
    try:
        user_id = current_user['id']
        goal = db.get_trading_goal(user_id, goal_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Trading goal not found")
        
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trading goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trading goal")

@router.post("/trading-goals")
@limiter.limit("20/minute")
async def create_trading_goal(
    goal_data: TradingGoalCreate,
    request: Request,
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a new trading goal."""
    try:
        user_id = current_user['id']
        
        # Parse target_date if provided
        target_date = None
        if goal_data.target_date:
            try:
                target_date = datetime.fromisoformat(goal_data.target_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid target_date format. Use ISO format.")
        
        goal_id = db.create_trading_goal(
            user_id=user_id,
            title=goal_data.title,
            target_amount=goal_data.target_amount,
            description=goal_data.description,
            target_date=target_date
        )
        
        if not goal_id:
            raise HTTPException(status_code=500, detail="Failed to create trading goal")
        
        # Fetch and return the created goal
        goal = db.get_trading_goal(user_id, goal_id)
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trading goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trading goal")

@router.put("/trading-goals/{goal_id}")
@limiter.limit("20/minute")
async def update_trading_goal(
    goal_id: int,
    goal_data: TradingGoalUpdate,
    request: Request,
    current_user: dict = Depends(auth.get_current_user)
):
    """Update a trading goal."""
    try:
        user_id = current_user['id']
        
        # Build update data dict
        update_data = {}
        if goal_data.title is not None:
            update_data['title'] = goal_data.title
        if goal_data.description is not None:
            update_data['description'] = goal_data.description
        if goal_data.target_amount is not None:
            update_data['target_amount'] = goal_data.target_amount
        if goal_data.current_progress is not None:
            update_data['current_progress'] = goal_data.current_progress
        if goal_data.is_completed is not None:
            update_data['is_completed'] = goal_data.is_completed
        if goal_data.target_date is not None:
            try:
                target_date = datetime.fromisoformat(goal_data.target_date.replace('Z', '+00:00'))
                update_data['target_date'] = target_date
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid target_date format. Use ISO format.")
        
        success = db.update_trading_goal(user_id, goal_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Trading goal not found or update failed")
        
        # Fetch and return the updated goal
        goal = db.get_trading_goal(user_id, goal_id)
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trading goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to update trading goal")

@router.delete("/trading-goals/{goal_id}")
@limiter.limit("20/minute")
async def delete_trading_goal(
    goal_id: int,
    request: Request,
    current_user: dict = Depends(auth.get_current_user)
):
    """Delete a trading goal."""
    try:
        user_id = current_user['id']
        success = db.delete_trading_goal(user_id, goal_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Trading goal not found")
        
        return {"status": "success", "message": "Trading goal deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trading goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete trading goal")

@router.post("/trading-goals/{goal_id}/complete")
@limiter.limit("20/minute")
async def complete_trading_goal(
    goal_id: int,
    request: Request,
    current_user: dict = Depends(auth.get_current_user)
):
    """Mark a trading goal as completed."""
    try:
        user_id = current_user['id']
        success = db.complete_trading_goal(user_id, goal_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Trading goal not found")
        
        # Fetch and return the updated goal
        goal = db.get_trading_goal(user_id, goal_id)
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing trading goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete trading goal")
