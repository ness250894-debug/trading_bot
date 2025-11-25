import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WSTest")

async def test_ws():
    uri = "ws://localhost:8000/api/ws/optimize"
    logger.info(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected!")
            
            # Send a dummy request
            req = {
                "symbol": "BTC/USDT",
                "timeframe": "1m",
                "days": 1,
                "strategy": "SMA Crossover",
                "param_ranges": {
                    "short_window": [10],
                    "long_window": [30]
                }
            }
            await websocket.send(json.dumps(req))
            logger.info("Request sent.")
            
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                    logger.info(f"Received: {msg}")
                    data = json.loads(msg)
                    if data.get("type") == "complete" or data.get("error"):
                        break
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for response.")
                    break
                    
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
