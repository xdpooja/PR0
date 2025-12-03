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
from urllib.parse import quote

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

class MonitorConfig(BaseModel):
    keywords: List[str]
    client: str = "AutoMonitor"
    interval_seconds: int = 300

def _validate_api_key(req: Request) -> bool:
    """Validate x-api-key header when OBSEI_API_KEY env var is set."""
    print(f"🔍 [DEBUG] Validating API key...")
    if not OBSEI_API_KEY:
        print(f"✓ [DEBUG] No API key required (OBSEI_API_KEY not set)")
        return True
    header = req.headers.get("x-api-key")
    is_valid = header == OBSEI_API_KEY
    print(f"{'✓' if is_valid else '✗'} [DEBUG] API key validation: {'PASSED' if is_valid else 'FAILED'}")
    return is_valid

@app.get("/health")
def health():
    print(f"🏥 [DEBUG] Health check requested")
    result = {"status": "healthy", "alerts_count": len(ALERTS)}
    print(f"✓ [DEBUG] Health response: {result}")
    return result

@app.get("/alerts")
def get_alerts(request: Request, limit: int = 50):
    print(f"📋 [DEBUG] Fetching alerts (limit={limit})")
    if not _validate_api_key(request):
        print(f"✗ [DEBUG] Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    alerts_list = list(reversed(ALERTS))[:limit]
    print(f"✓ [DEBUG] Returning {len(alerts_list)} alerts")
    return {"alerts": alerts_list}

@app.delete("/alerts")
def clear_alerts(request: Request):
    global ALERTS, ALERT_ID
    print(f"🗑️  [DEBUG] Clear alerts requested")
    if not _validate_api_key(request):
        print(f"✗ [DEBUG] Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    with LOCK:
        count = len(ALERTS)
        ALERTS = []
        ALERT_ID = 0
    print(f"✓ [DEBUG] Cleared {count} alerts, reset ID counter")
    return {"status": "cleared", "alerts_cleared": count}

@app.post("/start-monitor")
def start_monitor(request: Request, cfg: MonitorConfig, background_tasks: BackgroundTasks):
    global CURRENT_CLIENT, CURRENT_KEYWORDS, ALERTS, ALERT_ID
    
    print(f"🚀 [DEBUG] Start monitor requested")
    print(f"   Keywords: {cfg.keywords}")
    print(f"   Client: {cfg.client}")
    print(f"   Interval: {cfg.interval_seconds}s")
    
    if not _validate_api_key(request):
        print(f"✗ [DEBUG] Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    print(f"✓ [DEBUG] API key valid, stopping old monitor and starting new one...")
    
    # Clear old alerts and reset for new client
    with LOCK:
        ALERTS = []
        ALERT_ID = 0
        CURRENT_CLIENT = cfg.client
        CURRENT_KEYWORDS = cfg.keywords
    
    print(f"✓ [DEBUG] Alerts cleared, monitoring session reset for: {cfg.client}")
    
    # Start background monitoring for this specific client
    background_tasks.add_task(_run_monitor_loop, cfg.dict())
    result = {"status": "monitor_started", "cfg": cfg}
    print(f"✓ [DEBUG] Background task added, returning: {result}")
    return result

def _run_monitor_loop(cfg: Dict):
    """Background monitor loop that fetches news and analyzes sentiment."""
    keywords = cfg.get("keywords", [])
    client = cfg.get("client", "AutoMonitor")
    interval = cfg.get("interval_seconds", 300)
    print(f"\n{'='*60}")
    print(f"🔄 [DEBUG] Monitor Loop Started")
    print(f"   Keywords: {keywords}")
    print(f"   Client: {client}")
    print(f"   Interval: {interval}s")
    print(f"{'='*60}\n")
    
    # Initialize sentiment analyzer if available
    analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
    print(f"{'✓' if analyzer else '✗'} [DEBUG] Sentiment analyzer: {'AVAILABLE' if analyzer else 'NOT AVAILABLE (using fallback)'}")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n📡 [CYCLE {cycle}] Starting monitoring cycle...")
        try:
            # Fetch news from Google News RSS (no auth required)
            # Properly URL-encode keywords
            keywords_str = " ".join(keywords) if keywords else "breaking news"
            query = quote(keywords_str)
            rss_url = f"https://news.google.com/rss/search?q={query}"
            
            print(f"   📰 Fetching RSS: {rss_url}")
            
            try:
                feed = feedparser.parse(rss_url)
                print(f"   ✓ RSS fetched successfully")
            except Exception as e:
                print(f"   ✗ Failed to fetch RSS: {e}")
                time.sleep(interval)
                continue
            
            entries_count = len(feed.entries)
            print(f"   📊 Found {entries_count} entries")
            
            if not feed.entries:
                print(f"   ℹ️  No entries found for query: {query}")
                time.sleep(interval)
                continue
            
            # Process entries
            alerts_created = 0
            for idx, entry in enumerate(feed.entries[:10], 1):  # Limit to 10 per fetch
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
                        print(f"   [{idx}/10] Title: {title[:50]}...")
                        print(f"           Sentiment score: {sentiment:.3f}")
                    except Exception as e:
                        print(f"   [{idx}/10] Sentiment analysis failed: {e}")
                        sentiment = 0.0
                else:
                    # Fallback: simple heuristic if analyzer unavailable
                    negative_words = ["crisis", "disaster", "emergency", "urgent", "critical", "issue", "problem", "fail"]
                    sentiment = -0.5 if any(w in text.lower() for w in negative_words) else 0.1
                    print(f"   [{idx}/10] Using fallback sentiment: {sentiment:.3f}")
                
                # Create alert for negative sentiment
                if sentiment < -0.3:
                    global ALERT_ID
                    with LOCK:
                        ALERT_ID += 1
                        alert = {
                            "id": ALERT_ID,
                            "client": client,
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
                        alerts_created += 1
                        print(f"           🚨 ALERT CREATED (ID: {ALERT_ID}, Risk: {alert['riskScore']}/100)")
                else:
                    print(f"           ✓ No alert (sentiment {sentiment:.3f} >= -0.3 threshold)")
            
            print(f"   📈 Cycle {cycle} complete: {alerts_created} alerts created, {len(ALERTS)} total alerts stored")
            print(f"   ⏰ Waiting {interval}s until next cycle...\n")
            time.sleep(interval)
        except Exception as e:
            print(f"   ✗ Monitor error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(interval)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
