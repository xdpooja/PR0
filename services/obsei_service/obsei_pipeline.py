"""
Obsei-based Crisis Detection Pipeline
Monitors news sources for negative sentiment and creates alerts
"""
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Obsei imports
try:
    from obsei.source.google_news_source import GoogleNewsConfig, GoogleNewsSource
    from obsei.analyzer.sentiment_analyzer import VaderSentimentAnalyzer
    OBSEI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Obsei not fully available: {e}. Using simulation mode.")
    OBSEI_AVAILABLE = False
    GoogleNewsConfig = None
    GoogleNewsSource = None
    VaderSentimentAnalyzer = None


class AlertDatabase:
    """SQLite-based alert storage."""
    
    def __init__(self, db_path: str = "alerts.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client TEXT,
                    riskScore INTEGER,
                    region TEXT,
                    language TEXT,
                    topic TEXT,
                    triggerEvent TEXT,
                    sentiment REAL,
                    keywords TEXT,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_alert(self, alert: Dict[str, Any]) -> int:
        """Add an alert to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO alerts 
                (client, riskScore, region, language, topic, triggerEvent, sentiment, keywords, sources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.get("client"),
                alert.get("riskScore"),
                alert.get("region"),
                alert.get("language"),
                alert.get("topic"),
                alert.get("triggerEvent"),
                alert.get("sentiment"),
                json.dumps(alert.get("keywords", [])),
                json.dumps(alert.get("sources", [])),
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_alerts(self, limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts (last N hours)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM alerts
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (cutoff_time, limit)).fetchall()
            
            alerts = []
            for row in rows:
                alert = dict(row)
                alert["keywords"] = json.loads(alert.get("keywords", "[]"))
                alert["sources"] = json.loads(alert.get("sources", "[]"))
                # Compute timeElapsed
                created = datetime.fromisoformat(alert["created_at"])
                delta = datetime.utcnow() - created
                if delta.total_seconds() < 60:
                    alert["timeElapsed"] = "just now"
                elif delta.total_seconds() < 3600:
                    mins = int(delta.total_seconds() / 60)
                    alert["timeElapsed"] = f"{mins} min{'s' if mins > 1 else ''} ago"
                else:
                    hours = int(delta.total_seconds() / 3600)
                    alert["timeElapsed"] = f"{hours} hour{'s' if hours > 1 else ''} ago"
                alerts.append(alert)
            return alerts
    
    def clear_old_alerts(self, hours: int = 72):
        """Clean up alerts older than N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff_time,))
            conn.commit()


class ObseiCrisisPipeline:
    """
    Obsei-based crisis detection pipeline.
    Monitors news sources, analyzes sentiment, and stores alerts.
    """
    
    def __init__(self, db_path: str = "alerts.db"):
        self.db = AlertDatabase(db_path)
        self.source = None
        self.analyzer = None
        self._setup_obsei()
    
    def _setup_obsei(self):
        """Initialize Obsei source and analyzer."""
        if not OBSEI_AVAILABLE:
            logger.info("Obsei not available, using simulation mode")
            return
        
        try:
            self.source = GoogleNewsSource()
            self.analyzer = VaderSentimentAnalyzer()
            logger.info("Obsei pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Obsei: {e}")
            self.source = None
            self.analyzer = None
    
    def run_monitor(self, keywords: List[str], max_results: int = 10) -> int:
        """
        Run a single monitor cycle.
        Returns number of new alerts created.
        """
        if not keywords:
            keywords = ["crisis", "issue", "problem"]
        
        new_alerts = 0
        query = ", ".join(keywords)
        
        logger.info(f"Running monitor for: {query}")
        
        if self.source is None or self.analyzer is None:
            # Simulation mode
            logger.info("Running in simulation mode")
            new_alerts = self._simulate_monitor(keywords)
        else:
            # Real Obsei mode
            try:
                src_config = GoogleNewsConfig(query=query, max_results=max_results, fetch_article=True)
                source_responses = self.source.lookup(src_config)
                logger.info(f"Fetched {len(source_responses)} articles from Google News")
                
                for sr in source_responses:
                    # Extract text from source response
                    text = getattr(sr, 'text', None) or getattr(sr, 'title', None) or ""
                    if not text:
                        continue
                    
                    # Analyze sentiment
                    try:
                        analyzed = self.analyzer.analyze_input([sr])
                        if analyzed and len(analyzed) > 0:
                            ar = analyzed[0]
                            # Extract sentiment from analyzer response
                            sentiment_score = getattr(ar, 'sentiment', {})
                            if isinstance(sentiment_score, dict):
                                compound = sentiment_score.get('compound', 0.0)
                            else:
                                compound = float(sentiment_score) if sentiment_score else 0.0
                        else:
                            compound = 0.0
                    except Exception as e:
                        logger.warning(f"Sentiment analysis failed: {e}")
                        compound = 0.0
                    
                    # Create alert if negative sentiment
                    if compound < -0.4:
                        alert = {
                            "client": "News Monitor",
                            "riskScore": min(100, int(abs(compound) * 100)),
                            "region": getattr(sr, 'source', 'News'),
                            "language": getattr(sr, 'lang', 'en'),
                            "topic": getattr(sr, 'title', '')[:120],
                            "triggerEvent": text[:500],
                            "sentiment": compound,
                            "keywords": keywords,
                            "sources": [{"type": "Google News", "count": 1}],
                        }
                        alert_id = self.db.add_alert(alert)
                        new_alerts += 1
                        logger.info(f"Alert created (ID={alert_id}): {alert['topic']}")
            
            except Exception as e:
                logger.exception(f"Monitor cycle failed: {e}")
        
        # Cleanup old alerts
        self.db.clear_old_alerts(hours=72)
        
        return new_alerts
    
    def _simulate_monitor(self, keywords: List[str]) -> int:
        """Simulate monitor in case Obsei unavailable (for testing)."""
        # Simulate 1-2 alerts per cycle
        import random
        num_alerts = random.randint(0, 2)
        for _ in range(num_alerts):
            alert = {
                "client": "Simulated Monitor",
                "riskScore": random.randint(60, 95),
                "region": random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai"]),
                "language": random.choice(["Hindi", "English", "Tamil", "Telugu"]),
                "topic": f"Simulated issue related to {random.choice(keywords)}",
                "triggerEvent": "This is a simulated crisis alert for testing purposes",
                "sentiment": random.uniform(-1.0, -0.4),
                "keywords": keywords,
                "sources": [{"type": "Simulation", "count": 1}],
            }
            self.db.add_alert(alert)
        return num_alerts
    
    def get_recent_alerts(self, limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        """Retrieve recent alerts from database."""
        return self.db.get_alerts(limit=limit, hours=hours)
