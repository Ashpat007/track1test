"""
Single command launcher for Boundly - Bounded Agent Commerce Platform.
Starts both:
1. FastAPI Backend (port 8000)
2. Next.js Frontend (port 3000)
"""

import os
import sys
import time
import subprocess
import threading

def run_backend():
    print("[*] Starting FastAPI Merchant Backend on http://127.0.0.1:8000...")
    subprocess.run([sys.executable, "-m", "uvicorn", "merchant_api.app:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"])

def run_frontend():
    print("[*] Starting Next.js Studio Frontend on http://localhost:3000...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.run([npm_cmd, "run", "dev"], cwd=frontend_dir)

if __name__ == "__main__":
    print("=" * 65)
    print("   Boundly — Bounded Agent Commerce Platform")
    print("   Next.js 14 Frontend + FastAPI Multi-Merchant Backend")
    print("=" * 65)
    print("[*] Frontend: http://localhost:3000")
    print("[*] Backend:  http://127.0.0.1:8000")
    print("[*] Docs:     http://127.0.0.1:8000/docs")
    print("=" * 65)
    
    t_backend = threading.Thread(target=run_backend, daemon=True)
    t_backend.start()
    
    time.sleep(2)
    run_frontend()
