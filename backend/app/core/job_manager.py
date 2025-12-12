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

    async def start_job(self, job_func, job_type="standard", *args, **kwargs):
        if self.status == "running":
            raise Exception("A job is already running")

        self.status = "running"
        self.job_type = job_type
        self.progress = {"current": 0, "total": 0}
        self.results = []
        self.error = None
        
        loop = asyncio.get_running_loop()

        # Wrapper to run in thread
        def threaded_job_wrapper():
            # Define a sync callback that schedules the async update_progress on the main loop
            def sync_progress_callback(current, total, details=None):
                asyncio.run_coroutine_threadsafe(
                    self.update_progress(current, total, details),
                    loop
                )
            
            # Call the synchronous job function
            return job_func(*args, **kwargs, progress_callback=sync_progress_callback)

        # Async wrapper to manage the thread execution and state
        async def job_lifecycle_wrapper():
            try:
                logger.info(f"Starting {self.job_type} optimization job in background thread...")
                # Run the blocking job in the default executor
                self.results = await loop.run_in_executor(None, threaded_job_wrapper)
                
                self.status = "completed"
                await self.notify_subscribers({"type": "complete", "job_type": self.job_type, "results": self.results})
                logger.info("Optimization job completed.")
            except Exception as e:
                logger.error(f"Optimization job failed: {e}")
                self.status = "failed"
                self.error = str(e)
                await self.notify_subscribers({"type": "error", "job_type": self.job_type, "error": str(e)})
            finally:
                self.current_job = None

        # Schedule the lifecycle task
        self.current_job = asyncio.create_task(job_lifecycle_wrapper())
        return self.current_job

    async def update_progress(self, current, total, details=None):
        self.progress = {"current": current, "total": total}
        message = {
            "type": "progress",
            "job_type": self.job_type,
            "current": current,
            "total": total
        }
        if details:
            message["details"] = details
            
        await self.notify_subscribers(message)

    async def subscribe(self, websocket):
        self.subscribers.append(websocket)
        # Send current state immediately
        if self.status == "running":
            await websocket.send_json({
                "type": "progress",
                "job_type": self.job_type,
                "current": self.progress["current"],
                "total": self.progress["total"]
            })
        elif self.status == "completed":
            await websocket.send_json({
                "type": "complete",
                "job_type": self.job_type,
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
