#!/bin/bash
# 🚀 START HERE - Quick Launch Script
# Copy this file contents and run in terminal

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     ML Testing Platform - Complete Setup                       ║"
echo "║     On-Demand Question Generator with Web UI                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Set working directory
cd /home/narjess/Documents/summer_internship_july2026/code

echo "📋 System Status Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "✅ Python 3: $(python3 --version)"
else
    echo "❌ Python 3: Not found"
    exit 1
fi

# Check if FastAPI is installed
if python3 -c "import fastapi" 2>/dev/null; then
    echo "✅ FastAPI: Installed"
else
    echo "❌ FastAPI: Not installed - run: pip install -r requirements.txt"
    exit 1
fi

# Check if Groq is installed
if python3 -c "import groq" 2>/dev/null; then
    echo "✅ Groq SDK: Installed"
else
    echo "❌ Groq SDK: Not installed - run: pip install -r requirements.txt"
    exit 1
fi

# Check for web files
if [ -f "web_ui.html" ]; then
    echo "✅ Web UI: web_ui.html found"
else
    echo "❌ Web UI: web_ui.html not found"
    exit 1
fi

if [ -f "serve_ui.py" ]; then
    echo "✅ Server: serve_ui.py found"
else
    echo "❌ Server: serve_ui.py not found"
    exit 1
fi

# Check for API
if [ -d "src/api" ]; then
    echo "✅ API: src/api/ found"
else
    echo "❌ API: src/api/ not found"
    exit 1
fi

echo ""
echo "🚀 Starting Services:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📌 Tip: Open this in 2-3 separate terminals:"
echo ""
echo "  Terminal 1 (API Server):"
echo "  $ python -m uvicorn src.api.main:app --reload"
echo ""
echo "  Terminal 2 (Web UI Server):"
echo "  $ python serve_ui.py"
echo ""
echo "  Terminal 3 (Demo Script - Optional):"
echo "  $ python src/evaluation/api_demo.py"
echo ""

echo "📱 Once running, open browser:"
echo "  → http://localhost:8080"
echo ""

echo "📚 Documentation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. QUICK_START.md              ⚡ Fast setup instructions"
echo "  2. WEB_UI_GUIDE.md             📱 UI customization"
echo "  3. API_DOCUMENTATION.md        🔌 API reference"
echo "  4. ARCHITECTURE.md             🏗️  System design"
echo "  5. API_IMPLEMENTATION_SUMMARY  📊 Technical details"
echo ""

echo "🎯 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Read: QUICK_START.md"
echo "  2. Start API: python -m uvicorn src.api.main:app --reload"
echo "  3. Start UI: python serve_ui.py"
echo "  4. Open: http://localhost:8080"
echo "  5. Generate test and demo!"
echo ""

echo "✨ System Ready for Demo!"
echo ""
