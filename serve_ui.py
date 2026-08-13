#!/usr/bin/env python3
"""
Simple HTTP server for serving the Web UI.
Run this to serve the web_ui.html on port 8080.

Usage:
    python serve_ui.py
    
Then visit: http://localhost:8080
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
SCRIPT_DIR = Path(__file__).parent

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers."""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_GET(self):
        # Serve web_ui.html for root path
        if self.path == '/' or self.path == '/index.html':
            self.path = '/web_ui.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        # Better logging
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server():
    """Start the HTTP server."""
    os.chdir(SCRIPT_DIR)
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════════════╗
║           Course Test Generator - Web UI Server                 ║
╚════════════════════════════════════════════════════════════════╝

✓ Server started on port {PORT}
✓ Open your browser to: http://localhost:{PORT}

📌 Make sure the API server is running:
   python -m uvicorn src.api.main:app --reload

Press Ctrl+C to stop the server.
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped.")


if __name__ == '__main__':
    run_server()
