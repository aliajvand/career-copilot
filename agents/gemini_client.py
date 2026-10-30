import json
import urllib.request
import urllib.error
import re
from typing import Optional, Literal
from core.config import settings

ThinkingLevelType = Literal["low", "medium", "high"]

class GeminiClient:
    """
    Client for Google Gemini API configured strictly for gemini-3.8-flash.
    Adheres to Rules:
    - Model: gemini-3.8-flash
    - Omits temperature, top_p, top_k
    - Uses thinking_level ('low', 'medium', 'high') mapped to thinkingConfig
    - Enforces maximum output token limits
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-3.8-flash"
        self.proxy = settings.PROXY_URL

    def generate_content(
        self, 
        prompt: str, 
        system_instruction: str = "",
        thinking_level: ThinkingLevelType = "low",
        max_output_tokens: int = 1500
    ) -> str:
        """
        Executes generateContent call with model gemini-3.8-flash.
        """
        if not self.api_key:
            return ""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user", 
                "parts": [{"text": f"Instruction: {system_instruction}\n\nTask:\n{prompt}"}]
            })
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Map thinking_level to upper-case enum ('LOW', 'MEDIUM', 'HIGH')
        level_map = {
            "low": "LOW",
            "medium": "MEDIUM",
            "high": "HIGH"
        }
        mapped_level = level_map.get(thinking_level.lower(), "LOW")

        # generationConfig without temperature/top_p/top_k, with thinkingConfig & token cap
        generation_config = {
            "maxOutputTokens": max_output_tokens,
            "thinkingConfig": {
                "thinkingLevel": mapped_level
            }
        }

        body_dict = {
            "contents": contents,
            "generationConfig": generation_config
        }
        body = json.dumps(body_dict).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        
        if self.proxy:
            proxy_support = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_support)
        else:
            opener = urllib.request.build_opener()

        try:
            with opener.open(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception:
            # Safe fallback if network/proxy is unavailable
            pass
            
        return ""

gemini_client = GeminiClient()
