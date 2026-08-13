# 🎓 Course Test Generator - Web UI

A beautiful, interactive web interface for on-demand test generation and student assessment. Perfect for supervisors to demo the system!

## 🚀 Quick Start

### Step 1: Start the API Server (if not already running)

```bash
cd /home/narjess/Documents/summer_internship_july2026/code
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: `http://localhost:8000`

### Step 2: Open the Web UI

Simply open `web_ui.html` in your browser:

**Option A: Direct File**
```bash
# On Linux
xdg-open /home/narjess/Documents/summer_internship_july2026/code/web_ui.html

# On macOS
open /home/narjess/Documents/summer_internship_july2026/code/web_ui.html

# On Windows
start /home/narjess/Documents/summer_internship_july2026/code/web_ui.html
```

**Option B: From VS Code**
- Right-click `web_ui.html` → Open with Live Server
- Or just double-click to open in default browser

**Option C: Type in Browser**
```
file:///home/narjess/Documents/summer_internship_july2026/code/web_ui.html
```

## 📱 Features

### For Students
✅ **Enter Name** - Student identification  
✅ **Configure Test** - Choose topic, question count, and MCQ ratio  
✅ **Take Test** - Clean interface with progress tracking  
✅ **Instant Feedback** - See correct answer immediately  
✅ **Results** - Detailed score breakdown with all answers  

### For Supervisors
✅ **Demo-Ready** - Polished UI impresses stakeholders  
✅ **Real Questions** - Generated fresh via Groq LLM each time  
✅ **Instant Grading** - No waiting for results  
✅ **Detailed Analytics** - See exactly what students got right/wrong  

## 🎨 UI Walkthrough

### 1. Welcome Screen
- Enter student name
- Choose course name (e.g., "Introduction to Biology", "Modern History")
- Set number of questions (5-50)
- Adjust MCQ ratio (0.0 = all yes/no, 1.0 = all MCQ)

### 2. Test Screen
- Beautiful question display
- Multiple choice options
- Progress bar at top
- Can cancel anytime
- Disabled submit until answer is selected

### 3. Results Screen
- Large score display
- Color-coded results (green = correct, red = incorrect)
- Detailed answer table
- Option to take another test

## 🔧 Customization

### Change Server URL
If your API is running on a different host/port, edit line 305 in `web_ui.html`:
```javascript
const API_URL = 'http://localhost:8000/api/testing';
// Change to:
const API_URL = 'http://192.168.1.100:8000/api/testing';
```

### Change Colors
Edit the CSS gradient colors (line 24):
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 📊 Demo Scenarios

### Quick Demo (2 min)
1. Start API server
2. Open web_ui.html
3. Name: "Demo Student"
4. Topic: "machine learning"
5. Questions: 3
6. Answer 3 questions
7. Show results

### Full Demo (5 min)
1. Start with 10 questions
2. Answer first 5
3. Cancel and start new test
4. Complete full test
5. Show results to supervisor

### Multi-Student Demo (10 min)
1. Generate test with 5 questions
2. Student 1 takes test
3. Show results
4. Same student takes another test (fresh questions!)
5. Show how questions change each time

## 🐛 Troubleshooting

### "Loading..." spinner forever?
- Check API server is running: `http://localhost:8000/docs`
- Check browser console (F12) for CORS errors
- Verify firewall isn't blocking port 8000

### "Failed to generate test" error?
- Check API server logs for error messages
- Verify topic is valid (e.g., "machine learning")
- Try reducing number of questions

### UI looks weird?
- Clear browser cache: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
- Try a different browser
- Make sure JavaScript is enabled

## 📲 Mobile Support

The UI is fully responsive! Works on:
- Desktop (best experience)
- Tablet (good layout)
- Mobile (vertical layout)

## 🎬 What Happens Behind the Scenes

1. **Generate Test** - Calls Groq API to create fresh questions
2. **Show Question** - Displays one question at a time
3. **Submit Answer** - Immediately checks if correct/incorrect
4. **Show Results** - Aggregates all answers and calculates score
5. **Beautiful UI** - All rendered client-side for speed

## 📝 Technical Stack

- **Frontend**: Vanilla JavaScript (no frameworks!)
- **Backend**: FastAPI (already running)
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Storage**: In-memory (server session)

## 🚀 Deployment

For production, you could:
1. Host on AWS S3 + CloudFront
2. Deploy FastAPI to Heroku/Railway
3. Add authentication layer
4. Replace in-memory storage with database
5. Add test analytics dashboard

## 💡 Tips for Supervisor Demo

1. **Pre-generate a test** - Have it ready before demo
2. **Use simple topics** - "machine learning", "deep learning"
3. **Small test size** - 5 questions for quick demo (3 min)
4. **Show scoring** - Demonstrate 50% correct gets 50% score
5. **Highlight real questions** - Explain Groq generates them fresh
6. **Future features** - Mention analytics, authentication, etc.

## 📧 Support

Questions about the API? See: `API_DOCUMENTATION.md`  
Questions about the web UI? Check the code comments above!

---

**Ready for demo!** 🎉 Open the UI, generate a test, and show your supervisor the power of on-demand question generation!
