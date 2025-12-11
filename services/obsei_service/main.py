"""
FastAPI-based Crisis Detection Service (no Obsei dependency)
Monitors Reddit & Twitter, analyzes sentiment, and exposes alerts via HTTP
"""
import os
import logging
import time
import threading
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import praw
from datetime import datetime, timezone

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

# Current monitoring session
CURRENT_CLIENT = None
CURRENT_KEYWORDS = []
MONITOR_THREAD = None

# ----- Tunables -----
NEGATIVE_THRESHOLD = -0.3
DEFAULT_SUBREDDITS = os.environ.get("REDDIT_SUBREDDITS", "india,technology,IndianStreetBets").split(",")

class MonitorConfig(BaseModel):
    keywords: List[str]
    client: str = "AutoMonitor"
    interval_seconds: int = 300


def _twitter_search(query: str, bearer: str, max_results: int = 50):
    """Twitter Recent Search (v2). Requires TWITTER_BEARER_TOKEN."""
    if not bearer:
        return []
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"({query}) -is:retweet",
        "max_results": str(min(max_results, 100)),
        "tweet.fields": "created_at,lang,public_metrics",
    }
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {bearer}"}, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])


def _reddit_client_from_env():
    """Create a PRAW client from env vars."""
    rid = os.environ.get("REDDIT_CLIENT_ID")
    rsecret = os.environ.get("REDDIT_CLIENT_SECRET")
    ruser = os.environ.get("REDDIT_USERNAME")
    rpass = os.environ.get("REDDIT_PASSWORD")
    ragent = os.environ.get("REDDIT_USER_AGENT", "mavericks-obsei/1.0")
    if not all([rid, rsecret, ruser, rpass]):
        return None
    return praw.Reddit(
        client_id=rid,
        client_secret=rsecret,
        username=ruser,
        password=rpass,
        user_agent=ragent,
    )


def _reddit_search_submissions(reddit, subreddits: List[str], query: str, limit: int = 50):
    """Search recent subreddit submissions for a query."""
    if reddit is None:
        return []
    results = []
    for sr in subreddits:
        sr = sr.strip()
        if not sr:
            continue
        try:
            for post in reddit.subreddit(sr).search(query, sort="new", time_filter="day", limit=limit):
                results.append(post)
        except Exception:
            continue
    return results


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


@app.delete("/alerts")
def clear_alerts(request: Request):
    global ALERTS, ALERT_ID
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    with LOCK:
        count = len(ALERTS)
        ALERTS = []
        ALERT_ID = 0
    return {"status": "cleared", "alerts_cleared": count}


@app.post("/start-monitor")
def start_monitor(request: Request, cfg: MonitorConfig, background_tasks: BackgroundTasks):
    global CURRENT_CLIENT, CURRENT_KEYWORDS, ALERTS, ALERT_ID
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Reset state for new client session
    with LOCK:
        ALERTS = []
        ALERT_ID = 0
        CURRENT_CLIENT = cfg.client
        CURRENT_KEYWORDS = cfg.keywords

    # Start background monitoring
    background_tasks.add_task(_run_monitor_loop, cfg.dict())
    return {"status": "monitor_started", "cfg": cfg}


def _run_monitor_loop(cfg: Dict):
    """Background monitor loop that fetches Reddit + Twitter and analyzes sentiment."""
    keywords = cfg.get("keywords", [])
    client = cfg.get("client", "AutoMonitor")
    interval = cfg.get("interval_seconds", 300)

    analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None

    cycle = 0
    while True:
        cycle += 1
        try:
            keywords_str = " ".join(keywords) if keywords else "breaking"
            alerts_created = 0

            # -------------------- Twitter --------------------
            try:
                bearer = os.environ.get("TWITTER_BEARER_TOKEN")
                tw_data = _twitter_search(keywords_str, bearer, max_results=50)
            except Exception as e:
                logger.warning(f"Twitter fetch failed: {e}")
                tw_data = []

            for t in tw_data:
                text = t.get("text") or ""
                if not text:
                    continue

                # Sentiment
                if analyzer:
                    try:
                        sentiment = analyzer.polarity_scores(text).get("compound", 0.0)
                    except Exception:
                        sentiment = 0.0
                else:
                    sentiment = -0.5 if any(w in text.lower() for w in ["crisis","disaster","emergency","urgent","critical","issue","problem","fail"]) else 0.1

                if sentiment < NEGATIVE_THRESHOLD:
                    created_at = t.get("created_at")
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else datetime.now(timezone.utc)
                    except Exception:
                        dt = datetime.now(timezone.utc)
                    link = f"https://twitter.com/i/web/status/{t.get('id')}"

                    with LOCK:
                        global ALERT_ID
                        ALERT_ID += 1
                        alert = {
                            "id": ALERT_ID,
                            "client": client,
                            "riskScore": min(100, int(abs(sentiment) * 100)),
                            "region": "Twitter",
                            "language": t.get("lang", "en"),
                            "topic": text[:120],
                            "triggerEvent": text[:1000],
                            "timeElapsed": dt.isoformat(),
                            "sentiment": sentiment,
                            "keywords": keywords,
                            "sources": [{"type": "Twitter", "count": 1}],
                            "link": link,
                        }
                        ALERTS.append(alert)
                        alerts_created += 1

            # -------------------- Reddit --------------------
            try:
                reddit = _reddit_client_from_env()
                rd_posts = _reddit_search_submissions(reddit, DEFAULT_SUBREDDITS, keywords_str, limit=30)
            except Exception as e:
                logger.warning(f"Reddit fetch failed: {e}")
                rd_posts = []

            for p in rd_posts:
                title = getattr(p, "title", "") or ""
                body = getattr(p, "selftext", "") or ""
                text = (title + "\n" + body).strip()
                if not text:
                    continue

                # Sentiment
                if analyzer:
                    try:
                        sentiment = analyzer.polarity_scores(text).get("compound", 0.0)
                    except Exception:
                        sentiment = 0.0
                else:
                    sentiment = -0.5 if any(w in text.lower() for w in ["crisis","disaster","emergency","urgent","critical","issue","problem","fail"]) else 0.1

                if sentiment < NEGATIVE_THRESHOLD:
                    try:
                        dt = datetime.fromtimestamp(getattr(p, "created_utc", time.time()), tz=timezone.utc)
                    except Exception:
                        dt = datetime.now(timezone.utc)
                    link = f"https://www.reddit.com{getattr(p, 'permalink', '')}"

                    with LOCK:
                        ALERT_ID += 1
                        alert = {
                            "id": ALERT_ID,
                            "client": client,
                            "riskScore": min(100, int(abs(sentiment) * 100)),
                            "region": "Reddit",
                            "language": "en",
                            "topic": title[:120] or text[:120],
                            "triggerEvent": text[:1000],
                            "timeElapsed": dt.isoformat(),
                            "sentiment": sentiment,
                            "keywords": keywords,
                            "sources": [{"type": "Reddit", "count": 1}],
                            "link": link,
                        }
                        ALERTS.append(alert)
                        alerts_created += 1

            logger.info(f"[Cycle {cycle}] Created {alerts_created} alerts | Total stored: {len(ALERTS)}")
            time.sleep(interval)

        except Exception as e:
            logger.exception(f"Monitor error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
