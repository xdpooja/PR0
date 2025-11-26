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

## 🔧 Optional: Python Translation Service

The app works without the Python service (uses fallback translations). For real IndicTrans2 translations:

1. **Install Python dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the translation service**:
   ```bash
   python services/translation_service.py --http --host 127.0.0.1 --port 5000
   ```

   Or use the provided script:
   ```bash
   ./start_translation_service.sh
   ```

3. The translation service will run on `http://127.0.0.1:5000`

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

