from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import time
import threading
import logging

app = FastAPI()
logger = logging.getLogger("obsei_service")
logger.setLevel(logging.INFO)

# Simple in-memory alert store for prototype
ALERTS: List[Dict[str, Any]] = []
ALERT_ID = 0
LOCK = threading.Lock()


class MonitorConfig(BaseModel):
    keywords: List[str]
    sources: List[str] = ["x"]
    interval_seconds: int = 60


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/alerts")
def get_alerts(limit: int = 50):
    # Return most recent alerts
    return {"alerts": list(reversed(ALERTS))[:limit]}


@app.post("/start-monitor")
def start_monitor(cfg: MonitorConfig, background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_monitor_loop, cfg.dict())
    return {"status": "monitor_started", "cfg": cfg}


def _run_monitor_loop(cfg: Dict):
    """
    Background monitor loop (prototype). Replace the pseudocode with Obsei connectors/analyzers.
    """
    keywords = cfg.get("keywords", [])
    interval = cfg.get("interval_seconds", 60)
    logger.info(f"Starting monitor for {keywords} every {interval}s")
    while True:
        try:
            # TODO: Integrate with Obsei connectors and analyzers here.
            # For now, this is a placeholder that simulates detecting negative sentiment posts.
            sample_posts = [
                {"text": f"Urgent issue about {keywords[0] if keywords else 'product'}", "source": "X", "created_at": time.time()},
            ]

            for p in sample_posts:
                sentiment = -0.6  # placeholder: you should use an analyzer to compute this
                if sentiment < -0.5:
                    global ALERT_ID
                    with LOCK:
                        ALERT_ID += 1
                        alert = {
                            "id": ALERT_ID,
                            "client": "AutoMonitor",
                            "riskScore": int(min(max(abs(sentiment) * 100, 0), 100)),
                            "region": "Unknown",
                            "language": "Unknown",
                            "topic": "auto-detected",
                            "triggerEvent": p.get("text"),
                            "timeElapsed": "just now",
                            "sentiment": sentiment,
                            "keywords": keywords,
                            "sources": [{"type": p.get("source"), "count": 1}],
                        }
                        ALERTS.append(alert)
                        logger.info(f"New alert: {alert}")

            time.sleep(interval)
        except Exception as e:
            logger.exception("Monitor error, continuing")
            time.sleep(interval)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.obsei_service.main:app", host="127.0.0.1", port=5001, reload=True)
