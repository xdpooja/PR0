from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import time
import threading
import logging
from typing import Optional

# Obsei sources
try:
    from obsei.source.google_news_source import GoogleNewsConfig, GoogleNewsSource
except Exception:
    GoogleNewsConfig = None
    GoogleNewsSource = None

# Local sentiment analyzer (vader)
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:
    SentimentIntensityAnalyzer = None

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


def _validate_api_key(req: Request):
    """Validate x-api-key header when OBSEI_API_KEY env var is set."""
    expected = os.environ.get("OBSEI_API_KEY")
    if not expected:
        return True
    header = req.headers.get("x-api-key")
    return header == expected


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/alerts")
def get_alerts(request: Request, limit: int = 50):
    # Require API key if configured
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Return most recent alerts
    return {"alerts": list(reversed(ALERTS))[:limit]}


@app.post("/start-monitor")
def start_monitor(request: Request, cfg: MonitorConfig, background_tasks: BackgroundTasks):
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
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
            # Demo pipeline using Obsei GoogleNewsSource (no API key required) + Vader sentiment
            if GoogleNewsSource is None or SentimentIntensityAnalyzer is None:
                # If dependencies missing, fallback to simulated post
                sample_posts = [
                    {"text": f"Urgent issue about {keywords[0] if keywords else 'product'}", "source": "X", "created_at": time.time()},
                ]
                for p in sample_posts:
                    sentiment = -0.6
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
            else:
                # Build GoogleNews config using keywords
                query = ", ".join(keywords) if keywords else "breaking news"
                src = GoogleNewsSource()
                src_cfg = GoogleNewsConfig(query=query, max_results=10, fetch_article=True)
                source_response_list = []
                try:
                    source_response_list = src.lookup(src_cfg)
                except Exception as e:
                    logger.exception("GoogleNews lookup failed")

                # Use Vader for sentiment
                analyzer = SentimentIntensityAnalyzer()

                for sr in source_response_list:
                    # SourceResponse has 'text' (or 'title') fields. Use best available.
                    text = getattr(sr, 'text', None) or getattr(sr, 'title', None) or ''
                    if not text:
                        continue

                    try:
                        score = analyzer.polarity_scores(text)
                        compound = score.get('compound', 0.0)
                    except Exception:
                        compound = 0.0

                    # Negative sentiment threshold -> create alert
                    if compound < -0.45:
                        global ALERT_ID
                        with LOCK:
                            ALERT_ID += 1
                            alert = {
                                "id": ALERT_ID,
                                "client": "AutoMonitor",
                                "riskScore": int(min(max(abs(compound) * 100, 0), 100)),
                                "region": getattr(sr, 'source', 'Unknown'),
                                "language": getattr(sr, 'lang', 'Unknown'),
                                "topic": getattr(sr, 'title', '')[:120],
                                "triggerEvent": text[:1000],
                                "timeElapsed": "just now",
                                "sentiment": compound,
                                "keywords": keywords,
                                "sources": [{"type": getattr(sr, 'source', 'news'), "count": 1}],
                            }
                            ALERTS.append(alert)
                            logger.info(f"New alert from GoogleNews: {alert['topic']}")

            time.sleep(interval)
        except Exception as e:
            logger.exception("Monitor error, continuing")
            time.sleep(interval)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.obsei_service.main:app", host="127.0.0.1", port=5001, reload=True)
