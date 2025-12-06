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
from ..core.strategies.bollinger_breakout import BollingerBreakout
from ..core.strategies.momentum import Momentum
from ..core.strategies.dca_dip import DCADip
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
        elif backtest_data.strategy == "Bollinger Breakout":
            strategy_class = BollingerBreakout
        elif backtest_data.strategy == "Momentum":
            strategy_class = Momentum
        elif backtest_data.strategy == "DCA Dip":
            strategy_class = DCADip
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
                "final_balance": float(bt.balance),
                "total_return": float(total_return),
                "win_rate": float(win_rate),
                "total_trades": int(len(bt.trades))
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
        elif optimize_data.strategy == "Bollinger Breakout":
            strategy_class = BollingerBreakout
        elif optimize_data.strategy == "Momentum":
            strategy_class = Momentum
        elif optimize_data.strategy == "DCA Dip":
            strategy_class = DCADip
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
            
            # Authenticate User
            token = data.get("token")
            if not token:
                await websocket.send_json({"error": "Authentication required. Please refresh the page."})
                continue
            
            current_user = await auth.get_current_user_from_token(token)
            if not current_user:
                await websocket.send_json({"error": "Invalid session. Please login again."})
                continue

            if job_manager.status == "running":
                await websocket.send_json({"error": "Optimization already running"})
                continue
            
            # --- ULTIMATE OPTIMIZATION HANDLER ---
            if data.get("type") == "ultimate":
                tasks_data = data.get("tasks", [])
                if not tasks_data:
                    await websocket.send_json({"error": "No tasks provided for ultimate optimization"})
                    continue

                # Prepare tasks
                tasks = []
                total_trials = 0
                
                # Check subscription
                is_admin = current_user.get('is_admin', False)
                if not is_admin:
                    from ..core.database import DuckDBHandler
                    db = DuckDBHandler()
                    subscription = db.get_subscription(current_user['id'])
                    is_free_plan = True
                    if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
                        is_free_plan = False
                    
                    if is_free_plan:
                         await websocket.send_json({"error": "Ultimate Optimization is not available on the Free plan."})
                         continue

                for task_data in tasks_data:
                    try:
                        req = OptimizeRequest(**task_data)
                        tasks.append(req)
                        total_trials += req.n_trials or 50
                    except Exception as e:
                        logger.error(f"Invalid task data: {e}")
                        continue
                
                def run_ultimate_job(progress_callback):
                    all_results = []
                    current_global_trial = 0
                    
                    from ..core.database import DuckDBHandler
                    db = DuckDBHandler()
                    
                    for req in tasks:
                        # 1. Initialize Strategy
                        strategy_class = None
                        if req.strategy == "Mean Reversion": strategy_class = MeanReversion
                        elif req.strategy == "SMA Crossover": strategy_class = SMACrossover
                        elif req.strategy == "MACD": strategy_class = MACDStrategy
                        elif req.strategy == "RSI": strategy_class = RSIStrategy
                        elif req.strategy == "Bollinger Breakout": strategy_class = BollingerBreakout
                        elif req.strategy == "Momentum": strategy_class = Momentum
                        elif req.strategy == "DCA Dip": strategy_class = DCADip
                        else: continue # Skip unknown

                        # 2. Fetch Data
                        dummy_strategy = strategy_class()
                        bt = VectorizedBacktester(req.symbol, req.timeframe, dummy_strategy, days=req.days)
                        bt.fetch_data()
                        
                        if bt.df is None or bt.df.empty:
                            # Skip this strategy if no data, but increment progress
                            current_global_trial += (req.n_trials or 50)
                            progress_callback(current_global_trial, total_trials)
                            continue

                        # 3. Optimize
                        def strategy_progress(current, total, details=None):
                            # Map local progress to global progress
                            global_p = current_global_trial + current
                            progress_callback(global_p, total_trials, details)

                        optimizer = Hyperopt(req.symbol, req.timeframe, bt.df)
                        results_df = optimizer.optimize(req.param_ranges, strategy_class, n_trials=req.n_trials, progress_callback=strategy_progress)
                        
                        task_results = results_df.to_dict(orient="records")
                        valid_task_results = []

                        # 4. Process Results for this strategy
                        for result in task_results:
                            params = {k: v for k, v in result.items() if k not in ['return', 'strategy', 'number', 'state', 'datetime_start', 'datetime_complete', 'duration', 'win_rate', 'trades', 'final_balance']}
                            params['timeframe'] = req.timeframe
                            result['params'] = params
                            result['strategy'] = req.strategy # Set correct name
                            
                            result['win_rate'] = result.get('win_rate', 0)
                            result['trades'] = result.get('trades', 0)
                            result['final_balance'] = result.get('final_balance', 0)

                            if result.get('return', 0) > 0:
                                db.save_result(result, user_id=current_user['id'], timeframe=req.timeframe, symbol=req.symbol)
                                valid_task_results.append(result)
                        
                        all_results.extend(valid_task_results)
                        current_global_trial += (req.n_trials or 50)
                        
                        # 5. Send Partial Complete for this strategy
                        # We send the valid results specifically for this strategy to the frontend
                        progress_callback(current_global_trial, total_trials, details={
                            "type": "strategy_complete",
                            "strategy": req.strategy,
                            "results": valid_task_results
                        })
                    
                    return all_results

                await job_manager.start_job(run_ultimate_job)

            # --- SINGLE STRATEGY HANDLER ---
            elif "strategy" in data:
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
                elif request.strategy == "Bollinger Breakout":
                    strategy_class = BollingerBreakout
                elif request.strategy == "Momentum":
                    strategy_class = Momentum
                elif request.strategy == "DCA Dip":
                    strategy_class = DCADip
                else:
                    await websocket.send_json({"error": f"Unknown strategy: {request.strategy}"})
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
                await job_manager.start_job(run_opt)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        job_manager.unsubscribe(websocket)

