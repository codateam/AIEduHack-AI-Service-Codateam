import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GEMINI_API_KEY = ""
print(f"GEMINI_API_KEY: showig {GEMINI_API_KEY}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPI_API_KEY = os.getenv("ANTHROPI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LOCAL_OLLAMA_BASE_URL = os.getenv("LOCAL_OLLAMA_API_KEY")
LOCAL_LLAMACPP_BASE_URL = os.getenv("LOCAL_LLAMACPP_API_KEY")