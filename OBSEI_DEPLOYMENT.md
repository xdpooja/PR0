# Obsei Crisis Detection - Deployment Guide

This guide walks you through deploying the Chorus Bot Crisis Predictor with Obsei crisis detection to Vercel + Render.

## Architecture

```
Vercel (Next.js Frontend)
  ↓
Next.js API Route (/api/alerts)
  ↓
Render (Obsei Service)
  ├─ GoogleNewsSource (monitors news)
  ├─ VaderSentimentAnalyzer (analyzes sentiment)
  └─ SQLite DB (stores alerts)
```

## Prerequisites

- GitHub account with the PR0 repo
- Vercel account (free tier works)
- Render account (free tier works)
- Google Translate API key (optional, for translation features)

## Step 1: Deploy Obsei Service to Render

### Option A: One-Click Render Deploy (Recommended)

1. Go to https://render.com/deploy
2. Connect your GitHub account
3. Use the `render.yaml` file in the repo:
   - Select your fork of the PR0 repository
   - Render will auto-detect the `render.yaml`
   - Set environment variable:
     - `OBSEI_API_KEY`: Choose a strong secret (e.g., `obsei-key-abc123xyz`)
4. Click "Deploy"
5. Wait 5-10 minutes for the build to complete
6. Once deployed, note the service URL (e.g., `https://obsei-crisis-detection.onrender.com`)

### Option B: Manual Render Setup

1. Create a new "Web Service" on Render.com
2. Connect your GitHub repository
3. Configuration:
   - **Name**: `obsei-crisis-detection`
   - **Environment**: Docker
   - **Build Command**: `pip install -r services/obsei_service/requirements-obsei.txt`
   - **Start Command**: `cd services/obsei_service && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (startup tier)
4. Add Environment Variables:
   - `OBSEI_API_KEY`: Your chosen secret
   - `PORT`: `5001`
5. Deploy

## Step 2: Deploy Frontend to Vercel

1. Go to https://vercel.com/new
2. Import the PR0 GitHub repository
3. Configuration:
   - **Framework**: Next.js
   - **Root Directory**: `./` (or leave default)
4. Add Environment Variables:
   - `GOOGLE_TRANSLATE_API_KEY`: Your Google Translate API key (if you have one)
   - `OBSEI_SERVICE_URL`: The Render service URL from Step 1 (e.g., `https://obsei-crisis-detection.onrender.com`)
   - `OBSEI_API_KEY`: Same secret from Step 1
5. Click "Deploy"

## Step 3: Test Locally (Optional)

Before deploying, test locally:

```powershell
# Terminal 1: Start Obsei service
cd "D:\New folder\PR0"
python -m venv .venv-obsei
.\.venv-obsei\Scripts\Activate.ps1
pip install -r services/obsei_service/requirements-obsei.txt
$env:OBSEI_API_KEY='test-secret'
cd services/obsei_service
uvicorn main:app --host 127.0.0.1 --port 5001 --reload
```

```powershell
# Terminal 2: Start Next.js dev server
cd "D:\New folder\PR0"
$env:OBSEI_SERVICE_URL='http://127.0.0.1:5001'
$env:OBSEI_API_KEY='test-secret'
$env:GOOGLE_TRANSLATE_API_KEY='your_key_here'
npm run dev
```

3. Open http://localhost:3002/crisis-predictor (or your dev port)
4. You should see alerts updating every 15 seconds (polls from Obsei service)

## How It Works

### Frontend (Vercel)

- **Crisis Predictor Page** (`app/crisis-predictor/page.tsx`)
  - Polls `/api/alerts` every 15 seconds
  - Displays live alerts in a real-time dashboard
  - Shows alert details, sentiment, and recommended actions

- **API Proxy** (`app/api/alerts/route.ts`)
  - Proxies requests to Obsei service
  - Sends `OBSEI_API_KEY` in headers for authentication
  - Handles fallback if service unavailable

### Backend (Render)

- **Obsei Service** (`services/obsei_service/main.py`)
  - Runs a background monitor every 5 minutes
  - Fetches news articles from Google News
  - Analyzes sentiment using Vader
  - Stores alerts in SQLite database
  - Exposes REST API:
    - `GET /health` - Health check
    - `GET /alerts` - Retrieve alerts
    - `POST /monitor/start` - Start/reconfigure monitor
    - `POST /monitor/stop` - Stop monitor
    - `POST /monitor/cycle` - Manually trigger monitoring

- **Obsei Pipeline** (`services/obsei_service/obsei_pipeline.py`)
  - Manages Obsei source/analyzer workflow
  - Handles SQLite persistence
  - Supports simulation mode if Obsei unavailable

## Monitoring & Logs

### Render Logs

In the Render dashboard, check the "Logs" tab to see:
- Monitor cycles running
- Alerts being created
- Any errors

Example log output:
```
2025-12-03 10:15:23,456 - obsei_pipeline - INFO - Running monitor for: crisis, issue, complaint
2025-12-03 10:15:25,123 - obsei_pipeline - INFO - Fetched 10 articles from Google News
2025-12-03 10:15:27,456 - obsei_pipeline - INFO - Alert created (ID=5): Negative sentiment article
```

### Vercel Logs

In the Vercel dashboard, check "Logs" → "Function Logs" to see:
- API requests to `/api/alerts`
- Proxy calls to Obsei service
- Any errors in the integration

## Troubleshooting

### Obsei service not responding

**Symptom**: Crisis Predictor shows static alerts, no live updates

1. Check Render logs for the Obsei service
2. Verify `OBSEI_SERVICE_URL` is correct in Vercel env vars
3. Verify `OBSEI_API_KEY` matches between Render and Vercel
4. Test health endpoint:
   ```powershell
   Invoke-RestMethod -Uri "https://your-render-service.onrender.com/health" -Headers @{"x-api-key"="your-key"}
   ```

### Alerts not being created

**Symptom**: Health check OK but `/alerts` returns empty

1. Check Render logs for monitor cycles
2. Ensure Google News is accessible (not geoblocked)
3. Manually trigger a monitor cycle:
   ```powershell
   $headers = @{"x-api-key"="your-key"; "Content-Type"="application/json"}
   $body = '{"keywords":["crisis","issue"]}'
   Invoke-RestMethod -Uri "https://your-render-service.onrender.com/monitor/cycle" -Method Post -Headers $headers -Body $body
   ```

### Sentiment analysis not working

**Symptom**: Alerts have sentiment = 0

1. Ensure `vaderSentiment` is installed in Obsei venv
2. Check logs for "Sentiment analysis failed" errors
3. Verify Obsei analyzers are being called correctly

### Rate limiting (Google News)

**Note**: Google News has rate limits. If you see decreased alert volume:
- Increase `MONITOR_INTERVAL` to space out requests
- Rotate monitor keywords to distribute load
- Use different news sources (Obsei supports Reddit, RSS, etc.)

## Customization

### Change Monitor Keywords

Update keywords by calling the `/monitor/start` endpoint:

```powershell
$headers = @{"x-api-key"="your-key"; "Content-Type"="application/json"}
$body = '{"keywords":["product","service","delay"],"interval_seconds":600}'
Invoke-RestMethod -Uri "https://your-render-service.onrender.com/monitor/start" -Method Post -Headers $headers -Body $body
```

Or set environment variable in Render:
```
OBSEI_MONITOR_KEYWORDS=product,service,delay
```

### Add More Analyzers

Edit `services/obsei_service/obsei_pipeline.py` to add:
- Obsei ClassificationAnalyzer for topic classification
- NER for entity extraction
- Custom scoring logic

### Use Different News Sources

Edit `obsei_pipeline.py` to use:
- RedditSource (via API or scraper)
- TwitterSource (requires API key)
- TwitterScrapperSource (no API key)
- FacebookSource (requires API key)
- RSS feeds via generic source

See Obsei docs for source configuration.

## Production Hardening Checklist

- [ ] Use strong `OBSEI_API_KEY` (32+ random chars)
- [ ] Enable Vercel preview deployments for testing
- [ ] Set up alerts in Render for service downtime
- [ ] Monitor database growth (SQLite alert limits)
- [ ] Implement alert cleanup/archival
- [ ] Add rate limiting to API endpoints
- [ ] Use Vercel environment secrets for all API keys
- [ ] Enable CORS restrictions (currently permissive)
- [ ] Set up log aggregation (e.g., Sentry)
- [ ] Test failover/recovery scenarios

## Next Steps

1. **Real-time Updates**: Replace polling with WebSockets/SSE for true real-time alerts
2. **Persistent Storage**: Migrate SQLite to Postgres for production scale
3. **More Analyzers**: Add classification, NER, translation analyzers
4. **Custom Rules**: Implement alert filtering, deduplication, escalation rules
5. **Integrations**: Send alerts to Slack, Jira, email, etc. (Obsei sinks)
6. **Dashboard**: Build admin UI to manage monitors and view analytics

## Support

For issues or questions:
- Check Render logs for service errors
- Check Vercel logs for integration errors
- Review Obsei documentation: https://obsei.github.io/obsei/
- Contact: [Your email/contact]
