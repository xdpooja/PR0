"""
FastAPI-based Crisis Detection Service (no Obsei dependency)
Twitter-only (Reddit code included but commented out for future use)
- Monitors Twitter (X) Recent Search
- Analyzes sentiment
- Exposes alerts via HTTP
Enable Reddit later: search for "REDDIT-ENABLE" markers and uncomment blocks.
"""
import os
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------- Sentiment (VADER) ----------------
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except Exception:
    VADER_AVAILABLE = False

# ---------------- Reddit (disabled right now) ----------------
# To enable Reddit later:
# 1) pip install praw feedparser (if you want RSS fallback)  <-- optional
# 2) Uncomment the imports and the helper + fetch blocks marked with REDDIT-ENABLE
# import praw                         # REDDIT-ENABLE: uncomment
# import feedparser                  # REDDIT-ENABLE: uncomment

# ---------------- Constants & Logging ----------------
NEGATIVE_THRESHOLD = -0.3  # alert if compound sentiment is below this

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("crisis-service")

# ---------------- FastAPI App ----------------
app = FastAPI(title="Crisis Detection Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Protect endpoints (optional)
OBSEI_API_KEY = os.environ.get("OBSEI_API_KEY")

# In-memory store
ALERTS: List[Dict[str, Any]] = []
ALERT_ID = 0
LOCK = threading.Lock()

# ---------------- Models ----------------
class MonitorConfig(BaseModel):
    keywords: List[str]
    client: str = "AutoMonitor"
    interval_seconds: int = 300  # 5 minutes

# ---------------- Helpers ----------------
def _validate_api_key(req: Request) -> bool:
    """Validate x-api-key when OBSEI_API_KEY is set."""
    if not OBSEI_API_KEY:
        return True
    return req.headers.get("x-api-key") == OBSEI_API_KEY

def _twitter_search(query: str, bearer: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Twitter Recent Search v2 (requires TWITTER_BEARER_TOKEN)."""
    if not bearer:
        return []
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"({query}) -is:retweet",
        "max_results": str(min(max_results, 100)),
        "tweet.fields": "created_at,lang,public_metrics",
    }
    r = requests.get(url, params=params,
                     headers={"Authorization": f"Bearer {bearer}"},
                     timeout=20)
    r.raise_for_status()
    return r.json().get("data", []) or []

# ---------------- Reddit helpers (commented) ----------------
# REDDIT-ENABLE: PRAW OAuth client from env
# def _reddit_client_from_env():
#     rid = os.environ.get("REDDIT_CLIENT_ID")
#     rsecret = os.environ.get("REDDIT_CLIENT_SECRET")
#     ruser = os.environ.get("REDDIT_USERNAME")
#     rpass = os.environ.get("REDDIT_PASSWORD")
#     ragent = os.environ.get("REDDIT_USER_AGENT", "mavericks-obsei/1.0")
#     if not all([rid, rsecret, ruser, rpass]):
#         return None
#     return praw.Reddit(
#         client_id=rid,
#         client_secret=rsecret,
#         username=ruser,
#         password=rpass,
#         user_agent=ragent,
#     )

# REDDIT-ENABLE: Search submissions via PRAW
# def _reddit_search_submissions(reddit, subreddits: List[str], query: str, limit: int = 50):
#     if reddit is None:
#         return []
#     results = []
#     for sr in subreddits:
#         sr = sr.strip()
#         if not sr:
#             continue
#         try:
#             for post in reddit.subreddit(sr).search(query, sort="new", time_filter="day", limit=limit):
#                 results.append(post)
#         except Exception:
#             continue
#     return results

# REDDIT-ENABLE: RSS fallback (no OAuth)
# def _reddit_search_rss(subreddits: List[str], query: str, limit_per_sub: int = 30):
#     items = []
#     for sr in [s.strip() for s in subreddits if s.strip()]:
#         rss_url = f"https://www.reddit.com/r/{sr}/search.rss?q={requests.utils.quote(query)}&restrict_sr=on&sort=new"
#         feed = feedparser.parse(rss_url)
#         items.extend(feed.entries[:limit_per_sub])
#     return items

# ---------------- HTTP Endpoints ----------------
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
    global ALERTS, ALERT_ID
    if not _validate_api_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # reset alerts for fresh session
    with LOCK:
        ALERTS = []
        ALERT_ID = 0

    background_tasks.add_task(_run_monitor_loop, cfg.dict())
    return {"status": "monitor_started", "cfg": cfg}

# ---------------- Background loop ----------------
def _run_monitor_loop(cfg: Dict[str, Any]):
    keywords: List[str] = cfg.get("keywords", [])
    client: str = cfg.get("client", "AutoMonitor")
    interval: int = cfg.get("interval_seconds", 300)

    analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
    bearer = os.environ.get("TWITTER_BEARER_TOKEN")

    # REDDIT-ENABLE: env-configurable subreddits
    # DEFAULT_SUBREDDITS = os.environ.get("REDDIT_SUBREDDITS", "india,technology,IndianStreetBets").split(",")

    cycle = 0
    while True:
        cycle += 1
        try:
            keywords_str = " ".join(keywords) if keywords else "breaking"
            alerts_created = 0

            # -------- Twitter --------
            try:
                tweets = _twitter_search(keywords_str, bearer, max_results=50)
            except Exception as e:
                logger.warning(f"Twitter fetch failed: {e}")
                tweets = []

            for t in tweets:
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
                    negatives = ("crisis","disaster","emergency","urgent","critical","issue","problem","fail")
                    sentiment = -0.5 if any(w in text.lower() for w in negatives) else 0.1

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
                        ALERTS.append({
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
                        })
                        alerts_created += 1

            # -------- Reddit via PRAW (disabled) --------
            # REDDIT-ENABLE: Uncomment this block and ensure PRAW creds are set.
            # try:
            #     reddit = _reddit_client_from_env()
            #     rd_posts = _reddit_search_submissions(reddit, DEFAULT_SUBREDDITS, keywords_str, limit=30)
            # except Exception as e:
            #     logger.warning(f"Reddit (PRAW) fetch failed: {e}")
            #     rd_posts = []
            #
            # for p in rd_posts:
            #     title = getattr(p, "title", "") or ""
            #     body = getattr(p, "selftext", "") or ""
            #     text = (title + "\n" + body).strip()
            #     if not text:
            #         continue
            #
            #     if analyzer:
            #         try:
            #             sentiment = analyzer.polarity_scores(text).get("compound", 0.0)
            #         except Exception:
            #             sentiment = 0.0
            #     else:
            #         negatives = ("crisis","disaster","emergency","urgent","critical","issue","problem","fail")
            #         sentiment = -0.5 if any(w in text.lower() for w in negatives) else 0.1
            #
            #     if sentiment < NEGATIVE_THRESHOLD:
            #         try:
            #             dt = datetime.fromtimestamp(getattr(p, "created_utc", time.time()), tz=timezone.utc)
            #         except Exception:
            #             dt = datetime.now(timezone.utc)
            #         link = f"https://www.reddit.com{getattr(p, 'permalink', '')}"
            #
            #         with LOCK:
            #             ALERT_ID += 1
            #             ALERTS.append({
            #                 "id": ALERT_ID,
            #                 "client": client,
            #                 "riskScore": min(100, int(abs(sentiment) * 100)),
            #                 "region": "Reddit",
            #                 "language": "en",
            #                 "topic": title[:120] or text[:120],
            #                 "triggerEvent": text[:1000],
            #                 "timeElapsed": dt.isoformat(),
            #                 "sentiment": sentiment,
            #                 "keywords": keywords,
            #                 "sources": [{"type": "Reddit", "count": 1}],
            #                 "link": link,
            #             })
            #             alerts_created += 1

            # -------- Reddit via RSS (disabled) --------
            # REDDIT-ENABLE: Uncomment this block for a non-OAuth fallback (keep volumes modest).
            # try:
            #     rss_entries = _reddit_search_rss(DEFAULT_SUBREDDITS, keywords_str, limit_per_sub=30)
            # except Exception as e:
            #     logger.warning(f"Reddit (RSS) fetch failed: {e}")
            #     rss_entries = []
            #
            # for entry in rss_entries:
            #     title = entry.get("title", "")
            #     summary = entry.get("summary", "")
            #     link = entry.get("link", "")
            #     published = entry.get("published", datetime.now(timezone.utc).isoformat())
            #     text = f"{title}\n{summary}".strip()
            #     if not text:
            #         continue
            #
            #     if analyzer:
            #         try:
            #             sentiment = analyzer.polarity_scores(text).get("compound", 0.0)
            #         except Exception:
            #             sentiment = 0.0
            #     else:
            #         negatives = ("crisis","disaster","emergency","urgent","critical","issue","problem","fail")
            #         sentiment = -0.5 if any(w in text.lower() for w in negatives) else 0.1
            #
            #     if sentiment < NEGATIVE_THRESHOLD:
            #         with LOCK:
            #             ALERT_ID += 1
            #             ALERTS.append({
            #                 "id": ALERT_ID,
            #                 "client": client,
            #                 "riskScore": min(100, int(abs(sentiment) * 100)),
            #                 "region": "Reddit",
            #                 "language": "en",
            #                 "topic": title[:120] or text[:120],
            #                 "triggerEvent": text[:1000],
            #                 "timeElapsed": published,
            #                 "sentiment": sentiment,
            #                 "keywords": keywords,
            #                 "sources": [{"type": "Reddit (RSS)", "count": 1}],
            #                 "link": link,
            #             })
            #             alerts_created += 1

            logger.info(f"[Cycle {cycle}] Created {alerts_created} alerts | Total: {len(ALERTS)}")
        except Exception as e:
            logger.exception(f"Monitor error: {e}")

        time.sleep(interval)

# ---------------- Entrypoint ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
