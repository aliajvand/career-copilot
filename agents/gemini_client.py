import json
import urllib.request
import urllib.error
import re
from core.config import settings

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.proxy = settings.PROXY_URL

    def generate_content(self, prompt: str, system_instruction: str = "") -> str:
        """
        Sends prompt to Gemini API. If network is blocked (e.g. Iran censorship or lack of proxy),
        gracefully falls back so development and UI testing never crash.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_instruction:
            contents.append({"role": "user", "parts": [{"text": f"Instruction: {system_instruction}\n\nTask:\n{prompt}"}]})
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})

        body = json.dumps({"contents": contents}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        
        if self.proxy:
            proxy_support = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_support)
        else:
            opener = urllib.request.build_opener()

        try:
            with opener.open(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            # Network blocked or timeout - fall through to intelligent fallback
            pass
            
        return ""

gemini_client = GeminiClient()
