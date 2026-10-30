import sys
import webbrowser
import uvicorn
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 پلتفرم هوشمند کاریابی Career Co-Pilot (Agent Workflow)")
    print("📍 آدرس داشبورد وب / موبایل: http://127.0.0.1:8088")
    print("⚙️ در حال راه‌اندازی سرور و موتور ایجنت‌ها...")
    print("=" * 60)
    
    # Open browser automatically after a short delay
    try:
        webbrowser.open("http://127.0.0.1:8088")
    except Exception:
        pass
        
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8088, reload=False)

if __name__ == "__main__":
    main()
