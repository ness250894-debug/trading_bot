"""
Background scheduler for periodic tasks.
Uses asyncio to schedule and run tasks at intervals.
"""
import asyncio
import logging
from datetime import datetime
from typing import Callable

logger = logging.getLogger("Scheduler")

class BackgroundScheduler:
    """Simple background scheduler for periodic tasks."""
    
    def __init__(self):
        self.tasks = []
        self.running = False
        
    def schedule_daily(self, func: Callable, hour: int = 0, minute: int = 0):
        """
        Schedule a function to run daily at a specific time.
        
        Args:
            func: Function to run
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        self.tasks.append({
            'func': func,
            'interval': 'daily',
            'hour': hour,
            'minute': minute
        })
        logger.info(f"Scheduled {func.__name__} to run daily at {hour:02d}:{minute:02d}")
        
    async def _run_task(self, task):
        """Run a single task."""
        try:
            func = task['func']
            logger.info(f"Running scheduled task: {func.__name__}")
            
            # Run the task (supports both sync and async functions)
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
                
            logger.info(f"Completed task: {func.__name__}")
        except Exception as e:
            logger.error(f"Error running task {task['func'].__name__}: {e}")
    
    async def _calculate_delay_until_next_run(self, task):
        """Calculate seconds until next run time."""
        now = datetime.now()
        target_hour = task['hour']
        target_minute = task['minute']
        
        # Calculate target time today
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # If target time has passed today, schedule for tomorrow
        if now >= target:
            target = target.replace(day=target.day + 1)
        
        # Calculate delay in seconds
        delay = (target - now).total_seconds()
        return delay
    
    async def _task_loop(self, task):
        """Loop for running a task at intervals."""
        while self.running:
            # Calculate delay until next run
            delay = await self._calculate_delay_until_next_run(task)
            logger.info(f"Next run of {task['func'].__name__} in {delay/3600:.1f} hours")
            
            # Wait until next run time
            await asyncio.sleep(delay)
            
            # Run the task
            await self._run_task(task)
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        logger.info(f"Starting background scheduler with {len(self.tasks)} tasks")
        
        # Start all task loops
        loops = [self._task_loop(task) for task in self.tasks]
        await asyncio.gather(*loops, return_exceptions=True)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Stopping background scheduler")

# Global scheduler instance
scheduler = BackgroundScheduler()
