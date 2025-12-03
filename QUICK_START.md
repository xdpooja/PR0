# Quick Start Guide - Running The Chorus Bot Locally

## ✅ Step 1: Install Dependencies (Already Done!)

Dependencies have been installed. If you need to reinstall:
```bash
npm install
```

## ✅ Step 2: Start the Development Server

The development server is starting. Once it's ready, you'll see:
```
✓ Ready in [time]
○ Local:        http://localhost:3000
```

### To start manually:
```bash
npm run dev
```

## 🌐 Step 3: Open in Browser

Once the server is running, open your browser and go to:
**http://localhost:3000**

## 📱 Available Pages

- **Home**: http://localhost:3000
- **Regional Narrative Engine**: http://localhost:3000/regional-narrative
- **Conversion Attribution**: http://localhost:3000/conversion-attribution
- **Relationship Agent**: http://localhost:3000/relationship-agent
- **Crisis Predictor**: http://localhost:3000/crisis-predictor

## 🔧 Optional: Google Translate API (Recommended)

The app ships with Google Cloud Translation support for high-quality Indic language output. To enable it:

1. **Create a Google Cloud API key** with the Cloud Translation API enabled.
2. **Add the key to `.env.local`:**
   ```env
   GOOGLE_TRANSLATE_API_KEY=your_api_key_here
   ```
3. **Restart** `npm run dev` so the server picks up the new environment variable.

When the key is missing or the quota is exceeded, the app falls back to the free MyMemory API (limited to ~500 characters per request).

## 🛑 Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.

## 🐛 Troubleshooting

### Port 3000 already in use
```bash
# Kill the process using port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use a different port
npm run dev -- -p 3001
```

### Dependencies issues
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build for production
```bash
npm run build
npm start
```

## 📝 Notes

- The app uses **mock data** by default, so it works without a backend
- Translation features will use cloud API fallback if Python service is not running
- All pages are statically generated for optimal performance

---

**Your app should now be running at http://localhost:3000** 🚀

