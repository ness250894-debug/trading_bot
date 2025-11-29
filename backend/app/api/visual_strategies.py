"""
API endpoints for visual strategy builder.
Manages JSON-based trading strategies.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from ..core.strategies.json_strategy import JSONStrategyExecutor
from ..core.strategies.indicators import IndicatorLibrary
from ..core.strategies.conditions import ConditionEvaluator
from .auth import get_current_user


router = APIRouter()


# Pydantic models for request/response
class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    json_config: Dict[str, Any]


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    json_config: Optional[Dict[str, Any]] = None


class StrategyResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    json_config: Dict[str, Any]
    created_at: str
    updated_at: str
    is_active: bool


@router.get("/indicators", tags=["visual-strategies"])
async def get_available_indicators() -> Dict[str, Any]:
    """
    Get list of available indicators for strategy building.
    
    Returns:
        Dictionary of indicator metadata
    """
    try:
        indicators = IndicatorLibrary.get_available_indicators()
        return {
            "indicators": indicators,
            "count": len(indicators)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conditions", tags=["visual-strategies"])
async def get_available_conditions() -> Dict[str, Any]:
    """
    Get list of available condition operators.
    
    Returns:
        Dictionary of operator metadata
    """
    try:
        operators = ConditionEvaluator.get_available_operators()
        return {
            "operators": operators
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-strategies/validate", tags=["visual-strategies"])
async def validate_strategy(strategy: StrategyCreate) -> Dict[str, Any]:
    """
    Validate a JSON strategy configuration.
    
    Args:
        strategy: Strategy configuration to validate
        
    Returns:
        Validation result
    """
    try:
        # Try to create executor to validate
        executor = JSONStrategyExecutor(strategy.json_config)
        info = executor.get_info()
        
        return {
            "valid": True,
            "message": "Strategy is valid",
            "info": info
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e),
            "errors": [str(e)]
        }


@router.get("/visual-strategies", tags=["visual-strategies"])
async def list_strategies(
    user_id: int = Depends(get_current_user)
) -> Dict[str, List[StrategyResponse]]:
    """
    List all visual strategies for current user.
    
    Args:
        user_id: Current user ID
        
    Returns:
        List of strategies
    """
    try:
        from ..core.database import DuckDBHandler
        
        db = DuckDBHandler()
        
        # Query visual strategies for user
        result = db.conn.execute("""
            SELECT id, user_id, name, description, json_config, 
                   created_at, updated_at, is_active
            FROM visual_strategies
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, [user_id]).fetchall()
        
        strategies = []
        for row in result:
            strategies.append({
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "description": row[3],
                "json_config": json.loads(row[4]),
                "created_at": row[5],
                "updated_at": row[6],
                "is_active": bool(row[7])
            })
        
        return {"strategies": strategies, "count": len(strategies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-strategies", tags=["visual-strategies"])
async def create_strategy(
    strategy: StrategyCreate,
    user_id: int = Depends(get_current_user)
) -> StrategyResponse:
    """
    Create a new visual strategy.
    
    Args:
        strategy: Strategy data
        user_id: Current user ID
        
    Returns:
        Created strategy
    """
    try:
        # Validate strategy first
        executor = JSONStrategyExecutor(strategy.json_config)
        
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        # Insert into database
        now = datetime.utcnow().isoformat()
        result = db.conn.execute("""
            INSERT INTO visual_strategies 
            (user_id, name, description, json_config, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """, [
            user_id,
            strategy.name,
            strategy.description,
            json.dumps(strategy.json_config),
            now,
            now,
            False
        ]).fetchone()
        
        strategy_id = result[0]
        
        return {
            "id": strategy_id,
            "user_id": user_id,
            "name": strategy.name,
            "description": strategy.description,
            "json_config": strategy.json_config,
            "created_at": now,
            "updated_at": now,
            "is_active": False
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-strategies/{strategy_id}", tags=["visual-strategies"])
async def get_strategy(
    strategy_id: int,
    user_id: int = Depends(get_current_user)
) -> StrategyResponse:
    """
    Get a specific visual strategy.
    
    Args:
        strategy_id: Strategy ID
        user_id: Current user ID
        
    Returns:
        Strategy data
    """
    try:
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        result = db.conn.execute("""
            SELECT id, user_id, name, description, json_config,
                   created_at, updated_at, is_active
            FROM visual_strategies
            WHERE id = ? AND user_id = ?
        """, [strategy_id, user_id]).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "id": result[0],
            "user_id": result[1],
            "name": result[2],
            "description": result[3],
            "json_config": json.loads(result[4]),
            "created_at": result[5],
            "updated_at": result[6],
            "is_active": bool(result[7])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/visual-strategies/{strategy_id}", tags=["visual-strategies"])
async def update_strategy(
    strategy_id: int,
    strategy: StrategyUpdate,
    user_id: int = Depends(get_current_user)
) -> StrategyResponse:
    """
    Update a visual strategy.
    
    Args:
        strategy_id: Strategy ID
        strategy: Updated strategy data
        user_id: Current user ID
        
    Returns:
        Updated strategy
    """
    try:
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        # Check if strategy exists
        existing = db.conn.execute("""
            SELECT id FROM visual_strategies
            WHERE id = ? AND user_id = ?
        """, [strategy_id, user_id]).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Build update query
        updates = []
        params = []
        
        if strategy.name is not None:
            updates.append("name = ?")
            params.append(strategy.name)
        
        if strategy.description is not None:
            updates.append("description = ?")
            params.append(strategy.description)
        
        if strategy.json_config is not None:
            # Validate new config
            executor = JSONStrategyExecutor(strategy.json_config)
            updates.append("json_config = ?")
            params.append(json.dumps(strategy.json_config))
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        now = datetime.utcnow().isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        
        params.extend([strategy_id, user_id])
        
        db.conn.execute(f"""
            UPDATE visual_strategies
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """, params)
        
        # Fetch updated strategy
        return await get_strategy(strategy_id, user_id)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/visual-strategies/{strategy_id}", tags=["visual-strategies"])
async def delete_strategy(
    strategy_id: int,
    user_id: int = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a visual strategy.
    
    Args:
        strategy_id: Strategy ID
        user_id: Current user ID
        
    Returns:
        Success message
    """
    try:
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        result = db.conn.execute("""
            DELETE FROM visual_strategies
            WHERE id = ? AND user_id = ?
        """, [strategy_id, user_id])
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {"message": "Strategy deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
