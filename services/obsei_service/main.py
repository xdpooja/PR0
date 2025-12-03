"""
FastAPI-based Obsei Crisis Detection Service
Exposes HTTP endpoints for alert management and monitoring
"""
import os
import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import threading
import time

from obsei_pipeline import ObseiCrisisPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Obsei Crisis Detection Service", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key authentication
OBSEI_API_KEY = os.environ.get("OBSEI_API_KEY")

# Initialize Obsei pipeline
pipeline = ObseiCrisisPipeline(db_path="alerts.db")

# Background monitor state
MONITOR_RUNNING = False
MONITOR_KEYWORDS = ["crisis", "issue", "complaint"]
MONITOR_INTERVAL = 300  # 5 minutes


def _validate_api_key(request: Request) -> bool:
    """Validate x-api-key header if OBSEI_API_KEY is set."""
    if not OBSEI_API_KEY:
        return True
    header = request.headers.get("x-api-key")
    return header == OBSEI_API_KEY


def _background_monitor():
    """Background thread that runs monitor cycles."""
    global MONITOR_RUNNING
    logger.info(f"Background monitor started (interval={MONITOR_INTERVAL}s, keywords={MONITOR_KEYWORDS})")
    
    while MONITOR_RUNNING:
        try:
            new_alerts = pipeline.run_monitor(keywords=MONITOR_KEYWORDS, max_results=10)
            logger.info(f"Monitor cycle complete: {new_alerts} new alerts")
        except Exception as e:
            logger.exception(f"Monitor cycle error: {e}")
        
        time.sleep(MONITOR_INTERVAL)


@app.on_event("startup")
async def startup_event():
    """Start background monitor on app startup."""
    global MONITOR_RUNNING
    MONITOR_RUNNING = True
    monitor_thread = threading.Thread(target=_background_monitor, daemon=True)
    monitor_thread.start()
    logger.info("Obsei Crisis Detection Service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global MONITOR_RUNNING
    MONITOR_RUNNING = False
    logger.info("Obsei Crisis Detection Service stopped")


# ============= API Endpoints =============

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "obsei-crisis-detection",
        "monitor_running": MONITOR_RUNNING,
        "monitor_keywords": MONITOR_KEYWORDS,
    }


@app.get("/alerts")
async def get_alerts(request: Request, limit: int = 50, hours: int = 24):
    """
    Retrieve recent alerts.
    Optional: Requires x-api-key header if OBSEI_API_KEY is set.
    """
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        alerts = pipeline.get_recent_alerts(limit=limit, hours=hours)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.exception("Failed to retrieve alerts")
        raise HTTPException(status_code=500, detail=str(e))


class MonitorConfig(BaseModel):
    """Monitor configuration model."""
    keywords: List[str]
    interval_seconds: Optional[int] = 300


@app.post("/monitor/start")
async def start_monitor(request: Request, config: MonitorConfig):
    """
    Start or reconfigure the background monitor.
    Optional: Requires x-api-key header if OBSEI_API_KEY is set.
    """
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    global MONITOR_RUNNING, MONITOR_KEYWORDS, MONITOR_INTERVAL
    
    if config.keywords:
        MONITOR_KEYWORDS = config.keywords
    if config.interval_seconds:
        MONITOR_INTERVAL = config.interval_seconds
    
    MONITOR_RUNNING = True
    
    return {
        "status": "monitor_started",
        "keywords": MONITOR_KEYWORDS,
        "interval_seconds": MONITOR_INTERVAL,
    }


@app.post("/monitor/stop")
async def stop_monitor(request: Request):
    """
    Stop the background monitor.
    Optional: Requires x-api-key header if OBSEI_API_KEY is set.
    """
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    global MONITOR_RUNNING
    MONITOR_RUNNING = False
    
    return {"status": "monitor_stopped"}


@app.post("/monitor/cycle")
async def run_monitor_cycle(request: Request, keywords: Optional[List[str]] = None):
    """
    Manually trigger a monitor cycle (useful for testing).
    Optional: Requires x-api-key header if OBSEI_API_KEY is set.
    """
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        kw = keywords or MONITOR_KEYWORDS
        new_alerts = pipeline.run_monitor(keywords=kw, max_results=10)
        return {"status": "cycle_complete", "new_alerts": new_alerts}
    except Exception as e:
        logger.exception("Monitor cycle failed")
        raise HTTPException(status_code=500, detail=str(e))


# ============= CLI Entry Point =============

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5001"))
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.environ.get("RELOAD", "false").lower() == "true",
    )
