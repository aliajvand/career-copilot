import os
import sys
import subprocess
import uvicorn
from core.db import init_db

def main():
    print("=" * 60)
    print("🚀 Career Co-Pilot Cloud Server Starting...")
    print("=" * 60)
    
    # 1. Initialize database schema
    init_db()
    
    # 2. Launch Telegram Bot worker if enabled
    bot_process = None
    if os.getenv("ENABLE_TELEGRAM_BOT", "true").lower() in ("1", "true", "yes"):
        print("🤖 Launching Background Telegram Bot Worker (@Career_Copilot_ir_bot)...")
        try:
            bot_process = subprocess.Popen([sys.executable, "telegram_bot.py"])
        except Exception as e:
            print(f"⚠️ Failed to launch Telegram Bot worker: {e}")
    
    # 3. Run FastAPI Application
    port = int(os.getenv("PORT", "7860"))
    print(f"🌐 Serving Web Dashboard & REST API on port {port}...")
    try:
        uvicorn.run("backend.app:app", host="0.0.0.0", port=port)
    finally:
        if bot_process:
            print("🛑 Shutting down Telegram Bot worker...")
            bot_process.terminate()

if __name__ == "__main__":
    main()
