import json
import urllib.request
import urllib.error
import base64
import logging
from typing import Optional, Literal
from core.config import settings

logger = logging.getLogger(__name__)

ThinkingLevelType = Literal["low", "medium", "high"]

class GeminiClient:
    """
    Client for Google Gemini API configured for gemini-3.8-flash with fallback to gemini-3.5-flash.
    Adheres to Rules:
    - Primary Model: gemini-3.8-flash
    - Omits temperature, top_p, top_k
    - Uses thinking_level ('low', 'medium', 'high') mapped to thinkingConfig
    - Enforces maximum output token limits
    - Multimodal audio understanding for Persian voice messages
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
        Executes generateContent call with model gemini-3.8-flash and automatic fallback.
        """
        if not self.api_key:
            return ""

        contents = []
        if system_instruction:
            contents.append({
                "role": "user", 
                "parts": [{"text": f"Instruction: {system_instruction}\n\nTask:\n{prompt}"}]
            })
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})

        level_map = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH"}
        mapped_level = level_map.get(thinking_level.lower(), "LOW")

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

        # Try primary model first, fallback to 3.5 if 3.8 is busy (HTTP 503)
        candidate_models = [self.model, "gemini-3.5-flash", "gemini-flash-latest"]
        for target_model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
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
                logger.warning(f"Gemini call to {target_model} failed: {e}")
                continue
                
        return ""

    def transcribe_audio_bytes(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Transcribes speech from audio bytes (voice notes) using Gemini multimodal capabilities.
        """
        if not self.api_key or not audio_bytes:
            return ""

        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        for target_model in ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
            body_dict = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_audio
                                }
                            },
                            {
                                "text": "لطفاً گفتار فارسی موجود در این فایل صوتی را با دقت تمام و بدون هیچ توضیح اضافه‌ای به متن فارسی تبدیل کن."
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 400
                }
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
                            return parts[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"Audio transcription on {target_model} failed: {e}")
                continue

        return ""

gemini_client = GeminiClient()
