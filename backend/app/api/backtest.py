from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from ..core.rate_limit import limiter
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
import asyncio
from ..core.vectorized_backtest import VectorizedBacktester
from ..core.hyperopt import Hyperopt
from ..core.strategies.mean_reversion import MeanReversion
from ..core.strategies.sma_crossover import SMACrossover
from ..core.strategies.macd import MACDStrategy
from ..core.strategies.rsi import RSIStrategy

from ..core.strategies.rsi import RSIStrategy
from ..core import auth
from fastapi import Depends

router = APIRouter()
logger = logging.getLogger("API.Backtest")

class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    days: int = 5
    strategy: str
    params: Dict[str, Any] = {}
    
    @validator('days')
    def days_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('days must be positive')
        if v > 30:
            raise ValueError('days cannot exceed 30')
        return v
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v

@router.post("/backtest")
@limiter.limit("5/minute")
@limiter.limit("5/minute")
async def run_backtest(request: Request, backtest_data: BacktestRequest, current_user: dict = Depends(auth.get_current_user)):
    try:
        # Enforce Free Plan Limits
        is_admin = current_user.get('is_admin', False)
        if not is_admin:
            from ..core.database import DuckDBHandler
            db = DuckDBHandler()
            subscription = db.get_subscription(current_user['id'])
            is_free_plan = True
            if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
                is_free_plan = False
            
            if is_free_plan:
                 raise HTTPException(status_code=403, detail="Backtesting is not available on the Free plan. Please upgrade.")

        # Initialize Strategy
        strategy_class = None
        if backtest_data.strategy == "Mean Reversion":
            strategy_class = MeanReversion
        elif backtest_data.strategy == "SMA Crossover":
            strategy_class = SMACrossover
        elif backtest_data.strategy == "MACD":
            strategy_class = MACDStrategy
        elif backtest_data.strategy == "RSI":
            strategy_class = RSIStrategy
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {backtest_data.strategy}")
            
        # Create Strategy Instance with params
        try:
            strategy = strategy_class(**backtest_data.params)
        except TypeError as e:
             raise HTTPException(status_code=400, detail=f"Invalid parameters for {backtest_data.strategy}: {e}")

        # Run Backtest
        bt = VectorizedBacktester(backtest_data.symbol, backtest_data.timeframe, strategy, days=backtest_data.days)
        bt.fetch_data()
        
        if bt.df is None or bt.df.empty:
             raise HTTPException(status_code=404, detail="No data found for the specified parameters.")
             
        bt.run()
        
        # Format Results
        total_return = ((bt.balance - 1000) / 1000) * 100
        wins = [t for t in bt.trades if t['pnl'] > 0]
        win_rate = (len(wins) / len(bt.trades)) * 100 if bt.trades else 0
        
        # Chart Data (downsampled if needed, but for now full)
        # We need to convert timestamp to string or int for JSON
        chart_data = bt.df[['timestamp', 'open', 'high', 'low', 'close']].copy()
        chart_data['timestamp'] = chart_data['timestamp'].astype(str) # ISO format
        
        # Add indicators to chart data
        # This depends on the strategy. We can just dump all columns that are not OHLCV
        for col in bt.df.columns:
            if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
                chart_data[col] = bt.df[col].fillna(0) # Handle NaNs for JSON
        
        return {
            "metrics": {
                "final_balance": bt.balance,
                "total_return": total_return,
                "win_rate": win_rate,
                "total_trades": len(bt.trades)
            },
            "trades": bt.trades,
            "chart_data": chart_data.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class OptimizeRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    days: int = 5
    strategy: str
    param_ranges: Dict[str, List[Any]]
    n_trials: Optional[int] = 50
    
    @validator('days')
    def days_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('days must be positive')
        if v > 30:
            raise ValueError('days cannot exceed 30')
        return v
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v

@router.post("/optimize")
@limiter.limit("2/minute")
async def run_optimization(request: Request, optimize_data: OptimizeRequest, current_user: dict = Depends(auth.get_current_user)):
    try:
        # Enforce Free Plan Limits
        is_admin = current_user.get('is_admin', False)
        if not is_admin:
            from ..core.database import DuckDBHandler
            db = DuckDBHandler()
            subscription = db.get_subscription(current_user['id'])
            is_free_plan = True
            if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
                is_free_plan = False
            
            if is_free_plan:
                 raise HTTPException(status_code=403, detail="Optimization is not available on the Free plan. Please upgrade.")

        # Initialize Strategy Class
        strategy_class = None
        if optimize_data.strategy == "Mean Reversion":
            strategy_class = MeanReversion
        elif optimize_data.strategy == "SMA Crossover":
            strategy_class = SMACrossover
        elif optimize_data.strategy == "MACD":
            strategy_class = MACDStrategy
        elif optimize_data.strategy == "RSI":
            strategy_class = RSIStrategy
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {optimize_data.strategy}")
            
        # Fetch Data Once
        # We use a dummy strategy instance just to fetch data using Backtester
        dummy_strategy = strategy_class()
        bt = VectorizedBacktester(optimize_data.symbol, optimize_data.timeframe, dummy_strategy, days=optimize_data.days)
        bt.fetch_data()
        
        if bt.df is None or bt.df.empty:
             raise HTTPException(status_code=404, detail="No data found for the specified parameters.")
             
        # Run Optimization
        logger.info("Starting Hyperopt optimization...")
        optimizer = Hyperopt(optimize_data.symbol, optimize_data.timeframe, bt.df)
        logger.info(f"Optimizer initialized. Param ranges: {optimize_data.param_ranges}")
        
        results_df = optimizer.optimize(optimize_data.param_ranges, strategy_class, n_trials=optimize_data.n_trials)
        logger.info(f"Optimization complete. Result type: {type(results_df)}")
        
        # Save Successful Runs to DB
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        saved_count = 0
        results_list = results_df.to_dict(orient="records")
        
        # We need to manually filter for "successful" runs since optimize returns all trials
        for result in results_list:
            # Criteria: Positive Return
            if result.get('return', 0) > 0:
                # Add strategy name to result for DB
                result['strategy'] = optimize_data.strategy
                # Ensure params are stringified if needed or handled by DB
                # The DB expects 'parameters' as a string, but result has individual columns
                # We need to reconstruct params dict
                params = {k: v for k, v in result.items() if k not in ['return', 'strategy', 'number', 'state', 'datetime_start', 'datetime_complete', 'duration']}
                result['params'] = params
                # We need win_rate, trades, final_balance. 
                # Hyperopt currently only returns 'return'. 
                # We need to update Hyperopt to return more metrics or re-run best?
                # For now, let's just save what we have, filling missing with 0
                result['win_rate'] = 0
                result['trades'] = 0
                result['final_balance'] = 0
                
                db.save_result(result, user_id=current_user['id'], timeframe=optimize_data.timeframe, symbol=optimize_data.symbol)
                saved_count += 1
        
        if saved_count > 0:
            logger.info(f"Saved {saved_count} successful optimization runs to DB.")

        return {
            "results": results_list
        }
        
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.websocket("/ws/optimize")
async def websocket_optimize(websocket: WebSocket):
    await websocket.accept()
    from ..core.job_manager import job_manager
    
    # Subscribe to updates immediately
    await job_manager.subscribe(websocket)
    
    try:
        while True:
            # Wait for commands
            data = await websocket.receive_json()
            
            # If user wants to start a new optimization
            if "strategy" in data:
                if job_manager.status == "running":
                    await websocket.send_json({"error": "Optimization already running"})
                    continue

                request = OptimizeRequest(**data)
                
                # Initialize Strategy Class
                strategy_class = None
                if request.strategy == "Mean Reversion":
                    strategy_class = MeanReversion
                elif request.strategy == "SMA Crossover":
                    strategy_class = SMACrossover
                elif request.strategy == "MACD":
                    strategy_class = MACDStrategy
                elif request.strategy == "RSI":
                    strategy_class = RSIStrategy
                else:
                    await websocket.send_json({"error": f"Unknown strategy: {request.strategy}"})
                    continue

                # Authenticate User
                token = data.get("token")
                if not token:
                    await websocket.send_json({"error": "Authentication required. Please refresh the page."})
                    continue
                
                current_user = await auth.get_current_user_from_token(token)
                if not current_user:
                    await websocket.send_json({"error": "Invalid session. Please login again."})
                    continue

                # Fetch Data Once
                dummy_strategy = strategy_class()
                bt = VectorizedBacktester(request.symbol, request.timeframe, dummy_strategy, days=request.days)
                bt.fetch_data()
                
                if bt.df is None or bt.df.empty:
                     error_msg = bt.error if hasattr(bt, 'error') and bt.error else "No data found for the specified parameters."
                     await websocket.send_json({"error": error_msg})
                     continue

                # Define the job function
                def run_opt(progress_callback):
                    optimizer = Hyperopt(request.symbol, request.timeframe, bt.df)
                    results_df = optimizer.optimize(request.param_ranges, strategy_class, n_trials=request.n_trials, progress_callback=progress_callback)
                    
                    # Save Successful Runs to DB
                    from ..core.database import DuckDBHandler
                    db = DuckDBHandler()
                    
                    saved_count = 0
                    results_list = results_df.to_dict(orient="records")
                    
                    for result in results_list:
                        # Construct params for all results
                        params = {k: v for k, v in result.items() if k not in ['return', 'strategy', 'number', 'state', 'datetime_start', 'datetime_complete', 'duration', 'win_rate', 'trades', 'final_balance']}
                        params['timeframe'] = request.timeframe
                        result['params'] = params
                        
                        # Metrics are now in result from Hyperopt user_attrs
                        # Ensure they exist (fallback to 0 if something went wrong)
                        result['win_rate'] = result.get('win_rate', 0)
                        result['trades'] = result.get('trades', 0)
                        result['final_balance'] = result.get('final_balance', 0)

                        if result.get('return', 0) > 0:
                            result['strategy'] = request.strategy
                            db.save_result(result, user_id=current_user['id'], timeframe=request.timeframe, symbol=request.symbol)
                            saved_count += 1
                    
                    if saved_count > 0:
                        logger.info(f"Saved {saved_count} successful optimization runs to DB.")
                        
                    return results_list

                # Start the job via Manager
                # Note: run_opt is synchronous now because Hyperopt.optimize is blocking/synchronous
                # JobManager runs it in a thread, so it's fine.
                await job_manager.start_job(run_opt)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        job_manager.unsubscribe(websocket)

