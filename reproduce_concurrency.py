
import asyncio
import time
from backend.app.core.job_manager import JobManager

# Synchronous blocking job (like Hyperopt)
def blocking_job(progress_callback=None):
    print("   [Job] Starting blocking job...")
    time.sleep(2) # Block for 2 seconds
    if progress_callback:
        # Call the async callback from sync code? 
        # This is another issue: update_progress is async!
        # Calling async function from sync code requires a loop.
        pass
    print("   [Job] Finished blocking job.")
    return "Success"

async def main():
    print("🚀 Testing JobManager with blocking sync job...")
    jm = JobManager()
    
    try:
        # This should fail with TypeError because start_job awaits the sync function
        task = await jm.start_job(blocking_job)
        print("   [Main] Job started. Waiting for completion...")
        await task
        print("✅ Job completed successfully (Unexpected if logic is broken)")
    except TypeError as e:
        print(f"✅ Caught expected TypeError: {e}")
    except Exception as e:
        print(f"❌ Caught unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
