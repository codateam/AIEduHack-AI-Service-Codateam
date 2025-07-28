
from fastapi import  HTTPException
import httpx
from utils.models import LLMConfig, LLMProvider
from utils.constant import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPI_API_KEY, DEEPSEEK_API_KEY, LOCAL_OLLAMA_BASE_URL, LOCAL_LLAMACPP_BASE_URL


# LLM Client Factory

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        if self.config.provider == LLMProvider.ANTHROPIC:
            self.headers = {
                "Authorization": f"Bearer {ANTHROPI_API_KEY}",
                "Content-Type": "application/json"
            }
            self.base_url = "https://api.anthropic.com/v1/messages"
        
        elif self.config.provider == LLMProvider.OPENAI:
            self.headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            self.base_url = "https://api.openai.com/v1/chat/completions"
        
        elif self.config.provider == LLMProvider.GEMINI:
            self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model_name}:generateContent?key={GEMINI_API_KEY}"
            self.headers = {"Content-Type": "application/json"}
        
        elif self.config.provider == LLMProvider.DEEPSEEK:
            self.headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
        elif self.config.provider == LLMProvider.LOCAL_OLLAMA:
            self.base_url = f"{LOCAL_OLLAMA_BASE_URL or 'http://localhost:11434'}/api/generate"
            self.headers = {"Content-Type": "application/json"}
        
        elif self.config.provider == LLMProvider.LOCAL_LLAMACPP:
            self.base_url = f"{LOCAL_LLAMACPP_BASE_URL or 'http://localhost:8080'}/completion"
            self.headers = {"Content-Type": "application/json"}

    async def generate_text(self, prompt: str) -> str: # type: ignore
        async with httpx.AsyncClient(timeout=50000.0) as client:
            try:
                if self.config.provider == LLMProvider.ANTHROPIC:
                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    response = await client.post(self.base_url, headers=self.headers, json=payload)
                    result = response.json()
                    return result["content"][0]["text"]
                
                elif self.config.provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK]:
                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    response = await client.post(self.base_url, headers=self.headers, json=payload)
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                
                elif self.config.provider == LLMProvider.GEMINI:
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": self.config.temperature,
                            "maxOutputTokens": self.config.max_tokens
                        }
                    }
                    response = await client.post(self.base_url, headers=self.headers, json=payload)
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                
                elif self.config.provider == LLMProvider.LOCAL_OLLAMA:
                    payload = {
                        "model": self.config.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens
                        }
                    }
                    response = await client.post(self.base_url, headers=self.headers, json=payload)
                    print(f"Response: {response.text.strip()}")
                    # response = response.text.strip()
                    result = response.json()
                    return result["response"]
                
                elif self.config.provider == LLMProvider.LOCAL_LLAMACPP:
                    payload = {
                        "prompt": prompt,
                        "temperature": self.config.temperature,
                        "n_predict": self.config.max_tokens,
                        "stop": ["</s>", "\n\n"]
                    }
                    response = await client.post(self.base_url, headers=self.headers, json=payload)
                    result = response.json()
                    return result["content"]
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
