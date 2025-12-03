"""
FastAPI-based Crisis Detection Service (no Obsei dependency)
Monitors news sources, analyzes sentiment, and exposes alerts via HTTP
"""
import os
import logging
import time
import threading
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import feedparser

# Sentiment analyzer
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except Exception:
    VADER_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Crisis Detection Service", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OBSEI_API_KEY = os.environ.get("OBSEI_API_KEY")

# In-memory alert store
ALERTS: List[Dict[str, Any]] = []
ALERT_ID = 0
LOCK = threading.Lock()

class MonitorConfig(BaseModel):
    keywords: List[str]
    interval_seconds: int = 300

def _validate_api_key(req: Request) -> bool:
    """Validate x-api-key header when OBSEI_API_KEY env var is set."""
    if not OBSEI_API_KEY:
        return True
    header = req.headers.get("x-api-key")
    return header == OBSEI_API_KEY

@app.get("/health")
def health():
    return {"status": "healthy", "alerts_count": len(ALERTS)}

@app.get("/alerts")
def get_alerts(request: Request, limit: int = 50):
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"alerts": list(reversed(ALERTS))[:limit]}

@app.post("/start-monitor")
def start_monitor(request: Request, cfg: MonitorConfig, background_tasks: BackgroundTasks):
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    background_tasks.add_task(_run_monitor_loop, cfg.dict())
    return {"status": "monitor_started", "cfg": cfg}

def _run_monitor_loop(cfg: Dict):
    """Background monitor loop that fetches news and analyzes sentiment."""
    keywords = cfg.get("keywords", [])
    interval = cfg.get("interval_seconds", 300)
    logger.info(f"Starting monitor for {keywords} every {interval}s")
    
    # Initialize sentiment analyzer if available
    analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
    
    while True:
        try:
            # Fetch news from Google News RSS (no auth required)
            query = "+".join(keywords) if keywords else "breaking+news"
            rss_url = f"https://news.google.com/rss/search?q={query}"
            
            logger.info(f"Fetching news for: {query}")
            
            try:
                feed = feedparser.parse(rss_url)
            except Exception as e:
                logger.error(f"Failed to fetch RSS: {e}")
                time.sleep(interval)
                continue
            
            if not feed.entries:
                logger.info(f"No entries found for {query}")
                time.sleep(interval)
                continue
            
            # Process entries
            for entry in feed.entries[:10]:  # Limit to 10 per fetch
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                published = entry.get("published", "just now")
                link = entry.get("link", "")
                
                # Combine title and summary for analysis
                text = f"{title}. {summary}"
                
                # Analyze sentiment
                if analyzer:
                    try:
                        score = analyzer.polarity_scores(text)
                        sentiment = score.get("compound", 0.0)
                    except Exception:
                        sentiment = 0.0
                else:
                    # Fallback: simple heuristic if analyzer unavailable
                    negative_words = ["crisis", "disaster", "emergency", "urgent", "critical", "issue", "problem", "fail"]
                    sentiment = -0.5 if any(w in text.lower() for w in negative_words) else 0.1
                
                # Create alert for negative sentiment
                if sentiment < -0.3:
                    global ALERT_ID
                    with LOCK:
                        ALERT_ID += 1
                        alert = {
                            "id": ALERT_ID,
                            "client": "AutoMonitor",
                            "riskScore": int(min(max(abs(sentiment) * 100, 0), 100)),
                            "region": "Global",
                            "language": "en",
                            "topic": title[:120],
                            "triggerEvent": text[:1000],
                            "timeElapsed": published,
                            "sentiment": sentiment,
                            "keywords": keywords,
                            "sources": [{"type": "Google News", "count": 1}],
                            "link": link,
                        }
                        ALERTS.append(alert)
                        logger.info(f"New alert: {title[:80]}")
            
            time.sleep(interval)
        except Exception as e:
            logger.exception(f"Monitor error: {e}")
            time.sleep(interval)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
