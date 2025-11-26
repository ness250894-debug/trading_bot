import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("JobManager")

class JobManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        self.current_job: Optional[asyncio.Task] = None
        self.job_id: Optional[str] = None
        self.status: str = "idle" # idle, running, completed, failed
        self.progress: Dict[str, int] = {"current": 0, "total": 0}
        self.results: List[Dict[str, Any]] = []
        self.error: Optional[str] = None
        self.subscribers: List[Any] = [] # List of websocket queues or callbacks

    async def start_job(self, job_func, *args, **kwargs):
        if self.status == "running":
            raise Exception("A job is already running")

        self.status = "running"
        self.progress = {"current": 0, "total": 0}
        self.results = []
        self.error = None
        
        # Create a wrapper to handle completion/failure
        async def job_wrapper():
            try:
                logger.info("Starting optimization job...")
                self.results = await job_func(*args, **kwargs, progress_callback=self.update_progress)
                self.status = "completed"
                await self.notify_subscribers({"type": "complete", "results": self.results})
                logger.info("Optimization job completed.")
            except Exception as e:
                logger.error(f"Optimization job failed: {e}")
                self.status = "failed"
                self.error = str(e)
                await self.notify_subscribers({"type": "error", "error": str(e)})
            finally:
                self.current_job = None

        # Schedule the task
        self.current_job = asyncio.create_task(job_wrapper())
        return self.current_job

    async def update_progress(self, current, total):
        self.progress = {"current": current, "total": total}
        await self.notify_subscribers({
            "type": "progress",
            "current": current,
            "total": total
        })

    async def subscribe(self, websocket):
        self.subscribers.append(websocket)
        # Send current state immediately
        if self.status == "running":
            await websocket.send_json({
                "type": "progress",
                "current": self.progress["current"],
                "total": self.progress["total"]
            })
        elif self.status == "completed":
            await websocket.send_json({
                "type": "complete",
                "results": self.results
            })
        elif self.status == "failed":
            await websocket.send_json({
                "type": "error",
                "error": self.error
            })

    def unsubscribe(self, websocket):
        if websocket in self.subscribers:
            self.subscribers.remove(websocket)

    async def notify_subscribers(self, message):
        to_remove = []
        for ws in self.subscribers:
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.append(ws)
        
        for ws in to_remove:
            self.unsubscribe(ws)

job_manager = JobManager()
