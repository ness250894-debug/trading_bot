"""
Enhanced health check endpoint with system monitoring.
Provides comprehensive health status for load balancers and monitoring systems.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import logging
import psutil

router = APIRouter()
logger = logging.getLogger("Health")

@router.get("/health")
async def health_check():
    """
    Enhanced health check with system dependencies.
    
    Checks:
    - Database connectivity
    - Disk space (warns if < 1GB free)
    - Memory usage (warns if > 90% used)
    
    Returns 200 if healthy, 503 if any component is unhealthy.
    """
    try:

        
        # Check database connectivity
        db_healthy = True
        db_error = None
        try:

            result = db.conn.execute("SELECT 1").fetchone()
            db_healthy = result[0] == 1
        except Exception as e:
            db_healthy = False
            db_error = str(e)
            logger.error(f"Database health check failed: {e}")
        
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        disk_healthy = disk_free_gb > 1.0
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90
        
        # Overall health
        overall_healthy = db_healthy and disk_healthy and memory_healthy
        
        response = {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": {
                    "status": "pass" if db_healthy else "fail",
                    "error": db_error
                },
                "disk": {
                    "status": "pass" if disk_healthy else "warn",
                    "free_gb": round(disk_free_gb, 2),
                    "used_percent": disk.percent
                },
                "memory": {
                    "status": "pass" if memory_healthy else "warn",
                    "used_percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            }
        }
        
        # Return 503 for load balancer health checks
        if not overall_healthy:
            raise HTTPException(status_code=503, detail=response)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check for monitoring (existing functionality preserved).
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    # Check database
    try:

        db.conn.execute("SELECT 1").fetchone()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "duckdb"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
