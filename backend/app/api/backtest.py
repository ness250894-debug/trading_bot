from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from ..core.backtest import Backtester
from ..core.optimizer import Optimizer
from ..core.strategies.mean_reversion import MeanReversion
from ..core.strategies.sma_crossover import SMACrossover
from ..core.strategies.macd import MACDStrategy
from ..core.strategies.rsi import RSIStrategy

router = APIRouter()
logger = logging.getLogger("API.Backtest")

class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    days: int = 5
    strategy: str
    params: Dict[str, Any] = {}

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        # Initialize Strategy
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
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")
            
        # Create Strategy Instance with params
        try:
            strategy = strategy_class(**request.params)
        except TypeError as e:
             raise HTTPException(status_code=400, detail=f"Invalid parameters for {request.strategy}: {e}")

        # Run Backtest
        bt = Backtester(request.symbol, request.timeframe, strategy, days=request.days)
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
        raise HTTPException(status_code=500, detail=str(e))

class OptimizeRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    days: int = 5
    strategy: str
    param_ranges: Dict[str, List[Any]]

@router.post("/optimize")
async def run_optimization(request: OptimizeRequest):
    try:
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
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")
            
        # Fetch Data Once
        # We use a dummy strategy instance just to fetch data using Backtester
        dummy_strategy = strategy_class()
        bt = Backtester(request.symbol, request.timeframe, dummy_strategy, days=request.days)
        bt.fetch_data()
        
        if bt.df is None or bt.df.empty:
             raise HTTPException(status_code=404, detail="No data found for the specified parameters.")
             
        # Run Optimization
        optimizer = Optimizer(request.symbol, request.timeframe, strategy_class, bt.df)
        results_df = await optimizer.optimize(request.param_ranges)
        
        # Save Successful Runs to DB
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        saved_count = 0
        for result in optimizer.results:
            # Criteria: Positive Return OR High Win Rate (> 50%)
            if result['return'] > 0 or result['win_rate'] > 50:
                # Add strategy name to result for DB
                result['strategy'] = request.strategy
                db.save_result(result)
                saved_count += 1
        
        if saved_count > 0:
            logger.info(f"Saved {saved_count} successful optimization runs to DB.")

        return {
            "results": results_df.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/optimize")
async def websocket_optimize(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
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
            return

        # Fetch Data Once
        dummy_strategy = strategy_class()
        bt = Backtester(request.symbol, request.timeframe, dummy_strategy, days=request.days)
        bt.fetch_data()
        
        if bt.df is None or bt.df.empty:
             error_msg = bt.error if bt.error else "No data found for the specified parameters."
             await websocket.send_json({"error": error_msg})
             return

        # Progress Callback
        async def progress(current, total):
            await websocket.send_json({
                "type": "progress",
                "current": current,
                "total": total
            })

        # Run Optimization
        optimizer = Optimizer(request.symbol, request.timeframe, strategy_class, bt.df)
        results_df = await optimizer.optimize(request.param_ranges, progress_callback=progress)
        
        # Save Successful Runs to DB
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        
        saved_count = 0
        for result in optimizer.results:
            if result['return'] > 0 or result['win_rate'] > 50:
                result['strategy'] = request.strategy
                db.save_result(result)
                saved_count += 1
        
        if saved_count > 0:
            logger.info(f"Saved {saved_count} successful optimization runs to DB.")

        await websocket.send_json({
            "type": "complete",
            "results": results_df.to_dict(orient="records")
        })
        
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
