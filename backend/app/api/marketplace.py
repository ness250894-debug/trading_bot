"""
API endpoints for Social Trading / Strategy Marketplace.
Allows users to publish strategies, browse marketplace, and clone successful strategies.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timezone

from ..core.database import DuckDBHandler
from ..core.auth import get_current_user
from ..core.rate_limit import limiter


router = APIRouter()


class PublishStrategyRequest(BaseModel):
    strategy_id: int
    description: Optional[str] = ""


class RateStrategyRequest(BaseModel):
    rating: int  # 1-5 stars


@router.get("/marketplace/strategies", tags=["social-trading"])
@limiter.limit("20/minute")
async def get_marketplace_strategies(
    request: Request,
    sort_by: str = Query("rating", regex="^(rating|pnl|clones|recent)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Browse strategy marketplace.
    
    Args:
        sort_by: Sort method (rating, pnl, clones, recent)
        limit: Number of strategies to return
        
    Returns:
        List of public strategies with performance stats
    """
    try:
        db = DuckDBHandler()
        
        # Determine sort column
        sort_column = {
            'rating': 'rating DESC',
            'pnl': 'total_pnl DESC',
            'clones': 'clones_count DESC',
            'recent': 'created_at DESC'
        }.get(sort_by, 'rating DESC')
        
        result = db.conn.execute(f"""
            SELECT 
                ps.id,
                ps.user_id,
                ps.name,
                ps.description,
                ps.total_trades,
                ps.win_rate,
                ps.total_pnl,
                ps.clones_count,
                ps.rating,
                ps.created_at,
                u.email as author_email
            FROM public_strategies ps
            JOIN users u ON ps.user_id = u.id
            WHERE ps.is_active = 1
            ORDER BY {sort_column}
            LIMIT ?
        """, [limit]).fetchall()
        
        strategies = []
        for row in result:
            strategies.append({
                'id': row[0],
                'author_id': row[1],
                'name': row[2],
                'description': row[3],
                'total_trades': row[4],
                'win_rate': round(row[5], 2),
                'total_pnl': round(row[6], 2),
                'clones_count': row[7],
                'rating': round(row[8], 1),
                'created_at': row[9],
                'author': row[10].split('@')[0]  # Username from email
            })
        
        return {
            'strategies': strategies,
            'count': len(strategies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/strategies/{strategy_id}", tags=["social-trading"])
@limiter.limit("20/minute")
async def get_marketplace_strategy_detail(request: Request, strategy_id: int):
    """
    Get detailed information about a public strategy.
    
    Args:
        strategy_id: Public strategy ID
        
    Returns:
        Detailed strategy information
    """
    try:
        db = DuckDBHandler()
        
        result = db.conn.execute("""
            SELECT 
                ps.id,
                ps.user_id,
                ps.name,
                ps.description,
                ps.strategy_config,
                ps.performance_stats,
                ps.total_trades,
                ps.win_rate,
                ps.total_pnl,
                ps.clones_count,
                ps.rating,
                ps.created_at,
                u.email
            FROM public_strategies ps
            JOIN users u ON ps.user_id = u.id
            WHERE ps.id = ? AND ps.is_active = 1
        """, [strategy_id]).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            'id': result[0],
            'author_id': result[1],
            'name': result[2],
            'description': result[3],
            'config': json.loads(result[4]) if result[4] else {},
            'performance_stats': json.loads(result[5]) if result[5] else {},
            'total_trades': result[6],
            'win_rate': round(result[7], 2),
            'total_pnl': round(result[8], 2),
            'clones_count': result[9],
            'rating': round(result[10], 1),
            'created_at': result[11],
            'author': result[12].split('@')[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/publish", tags=["social-trading"])
@limiter.limit("5/minute")
async def publish_strategy(
    request: Request,
    publish_request: PublishStrategyRequest,
    user_id: int = Depends(get_current_user)
):
    """
    Publish a strategy to the marketplace.
    
    Args:
        request: Publish request with strategy_id
        user_id: Current user ID
        
    Returns:
        Published strategy info
    """
    try:
        db = DuckDBHandler()
        
        # Get strategy details
        strategy = db.get_user_strategy(user_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Check if already published
        existing = db.conn.execute("""
            SELECT id FROM public_strategies
            WHERE user_id = ? AND strategy_id = ?
        """, [user_id, request.strategy_id]).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Strategy already published")
        
        # Calculate performance stats from trades
        perf_result = db.conn.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE user_id = ? AND type = 'CLOSE'
        """, [user_id]).fetchone()
        
        total_trades = perf_result[0] or 0
        wins = perf_result[1] or 0
        total_pnl = perf_result[2] or 0
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Insert into public_strategies
        now = datetime.now(timezone.utc).isoformat()
        db.conn.execute("""
            INSERT INTO public_strategies 
            (user_id, strategy_id, name, description, strategy_config, 
             total_trades, win_rate, total_pnl, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            user_id,
            request.strategy_id,
            strategy.get('strategy', 'My Strategy'),
            request.description,
            json.dumps(strategy),
            total_trades,
            win_rate,
            total_pnl,
            now,
            now
        ])
        
        return {
            'message': 'Strategy published successfully',
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/clone/{strategy_id}", tags=["social-trading"])
@limiter.limit("10/minute")
async def clone_strategy(
    request: Request,
    strategy_id: int,
    user_id: int = Depends(get_current_user)
):
    """
    Clone a public strategy to user's account.
    
    Args:
        strategy_id: Public strategy ID to clone
        user_id: Current user ID
        
    Returns:
        Cloned strategy info
    """
    try:
        db = DuckDBHandler()
        
        # Get public strategy
        pub_strategy = db.conn.execute("""
            SELECT strategy_config FROM public_strategies
            WHERE id = ? AND is_active = 1
        """, [strategy_id]).fetchone()
        
        if not pub_strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        config = json.loads(pub_strategy[0])
        
        # Save to user's strategies
        db.save_user_strategy(user_id, config)
        
        # Track the clone
        db.conn.execute("""
            INSERT INTO strategy_clones (user_id, public_strategy_id, cloned_strategy_id)
            VALUES (?, ?, ?)
        """, [user_id, strategy_id, 0])  # cloned_strategy_id can be tracked if needed
        
        # Increment clone count
        db.conn.execute("""
            UPDATE public_strategies
            SET clones_count = clones_count + 1
            WHERE id = ?
        """, [strategy_id])
        
        return {
            'message': 'Strategy cloned successfully',
            'config': config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", tags=["social-trading"])
@limiter.limit("20/minute")
async def get_leaderboard(
    request: Request,
    period: str = Query("all", regex="^(day|week|month|all)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get strategy leaderboard.
    
    Args:
        period: Time period (day, week, month, all)
        limit: Number of entries
        
    Returns:
        Ranked list of strategies
    """
    try:
        db = DuckDBHandler()
        
        # Time filter based on period
        time_filter = {
            'day': "AND ps.updated_at >= datetime('now', '-1 day')",
            'week': "AND ps.updated_at >= datetime('now', '-7 days')",
            'month': "AND ps.updated_at >= datetime('now', '-30 days')",
            'all': ""
        }.get(period, "")
        
        result = db.conn.execute(f"""
            SELECT 
                ps.id,
                ps.name,
                ps.total_trades,
                ps.win_rate,
                ps.total_pnl,
                ps.clones_count,
                ps.rating,
                u.email
            FROM public_strategies ps
            JOIN users u ON ps.user_id = u.id
            WHERE ps.is_active = 1 {time_filter}
            ORDER BY ps.total_pnl DESC, ps.win_rate DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        leaderboard = []
        for idx, row in enumerate(result, 1):
            leaderboard.append({
                'rank': idx,
                'strategy_id': row[0],
                'name': row[1],
                'total_trades': row[2],
                'win_rate': round(row[3], 2),
                'total_pnl': round(row[4], 2),
                'clones': row[5],
                'rating': round(row[6], 1),
                'author': row[7].split('@')[0]
            })
        
        return {
            'period': period,
            'leaderboard': leaderboard
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-published-strategies", tags=["social-trading"])
@limiter.limit("20/minute")
async def get_my_published_strategies(request: Request, user_id: int = Depends(get_current_user)):
    """
    Get current user's published strategies.
    
    Args:
        user_id: Current user ID
        
    Returns:
        List of user's published strategies
    """
    try:
        db = DuckDBHandler()
        
        result = db.conn.execute("""
            SELECT 
                id, name, description, total_trades, win_rate, total_pnl,
                clones_count, rating, created_at
            FROM public_strategies
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, [user_id]).fetchall()
        
        strategies = []
        for row in result:
            strategies.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'total_trades': row[3],
                'win_rate': round(row[4], 2),
                'total_pnl': round(row[5], 2),
                'clones_count': row[6],
                'rating': round(row[7], 1),
                'created_at': row[8]
            })
        
        return {'strategies': strategies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
