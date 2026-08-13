# 🚀 Web UI - Quick Start Guide

## The Fastest Way to Demo

### Terminal 1: Start API Server
```bash
cd /home/narjess/Documents/summer_internship_july2026/code
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ Server is now ready at: http://localhost:8000

---

### Terminal 2: Serve the Web UI

**Option A: Using Python server (Recommended)**
```bash
cd /home/narjess/Documents/summer_internship_july2026/code
python serve_ui.py
```

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║          Course Test Generator - Web UI Server               ║
╚════════════════════════════════════════════════════════════════╝

✓ Server started on port 8080
✓ Open your browser to: http://localhost:8080
```

✅ Web UI is now ready at: http://localhost:8080

**Option B: Direct file (no server needed)**
```bash
# Just open the file directly in your browser:
file:///home/narjess/Documents/summer_internship_july2026/code/web_ui.html
```

---

## Now: Open Your Browser! 🌐

Click: **http://localhost:8080**

You should see the beautiful login screen!

---

## 5-Minute Demo Workflow

### Step 1: Fill in Test Details
- **Name**: "Alice" (or any student name)
- **Course name**: "Introduction to Biology"
- **Questions**: 5 (for quick demo)
- **MCQ Ratio**: 0.5 (50/50 mix)

### Step 2: Click "Generate Test"
- Watch spinner for 2-3 seconds
- Test appears with fresh Groq-generated questions

### Step 3: Answer Questions
- Click each answer option
- Click "Next Question"
- See 5 questions total

### Step 4: View Results
- Beautiful score display
- Detailed breakdown of all answers
- Option to "Take Another Test"

---

## What You're Showing Your Supervisor

✅ **Fresh Questions Each Time** - Groq generates new questions  
✅ **Instant Grading** - No manual scoring  
✅ **Professional UI** - Polished, ready for production  
✅ **Real Integration** - Works with existing API  
✅ **Multiple Question Types** - MCQ and Yes/No mixed  

---

## If Something Goes Wrong

### Error: "Failed to generate test"
→ Check Terminal 1: Is API server still running?  
→ Try generating again in browser  

### Error: "Failed to connect"
→ Open http://localhost:8000/docs  
→ If it loads, API is fine  
→ If not, restart Terminal 1  

### Web UI loads but no styling
→ Try: Ctrl+Shift+R (hard refresh)  
→ Check browser console (F12)  

### Can't see the UI at all
→ Try opening file directly: file:///home/narjess/Documents/summer_internship_july2026/code/web_ui.html  
→ Or use different browser  

---

## Running Both at Once (Easiest)

```bash
# Terminal 1: Start both servers
cd /home/narjess/Documents/summer_internship_july2026/code

# Start API server in background
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &

# Start Web UI server
python serve_ui.py
```

Then just visit: **http://localhost:8080**

---

## Files Created

| File | Purpose |
|------|---------|
| `web_ui.html` | Beautiful interactive web interface |
| `serve_ui.py` | Simple HTTP server to serve web_ui.html |
| `WEB_UI_GUIDE.md` | Detailed customization guide |
| `API_DOCUMENTATION.md` | Complete API reference |
| `API_IMPLEMENTATION_SUMMARY.md` | System overview |

---

## Customizing the UI

**Change server URL:**
Edit line 305 in `web_ui.html`:
```javascript
const API_URL = 'http://localhost:8000/api/testing';
```

**Change colors:**
Edit lines 24, 45, etc. in `web_ui.html`

**More customization:**
See `WEB_UI_GUIDE.md` for detailed options

---

## Browser Compatibility

✅ Chrome/Edge (best)  
✅ Firefox  
✅ Safari  
✅ Mobile browsers  

**Recommended**: Chrome or Edge

---

## Pro Tips for Demo

1. **Pre-load the page** - Open http://localhost:8080 before demo starts
2. **Use small test** - 5 questions = 2-3 minute demo
3. **Simple course name** - Use "Introduction to Biology" or "Modern History"
4. **Practice once** - Take the test yourself first
5. **Highlight real questions** - "Notice these are generated fresh by Groq"
6. **Show progress** - Point out the progress bar
7. **Show scoring** - "Instant feedback, no manual grading!"

---

## Next Level: Production Deployment

Ready to deploy to real servers?

1. Deploy FastAPI to: Heroku, Railway, AWS, or DigitalOcean
2. Deploy web_ui.html to: AWS S3, Netlify, or GitHub Pages
3. Add authentication layer
4. Replace in-memory storage with database
5. Add test analytics dashboard

See `API_DOCUMENTATION.md` for deployment details.

---

## Support

- **API Issues?** → See `API_DOCUMENTATION.md`
- **UI Issues?** → See `WEB_UI_GUIDE.md`
- **System Overview?** → See `API_IMPLEMENTATION_SUMMARY.md`

---

## 🎉 You're All Set!

**Now go run:**
```bash
python -m uvicorn src.api.main:app --reload &
python serve_ui.py
```

**Then visit:** http://localhost:8080

**And demo the system to your supervisor!** 🚀

---

*Made with ❤️ for your internship project*
