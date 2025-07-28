from langchain_google_genai import GoogleGenerativeAIEmbeddings
from utils.models import LLMConfig
from pydantic import SecretStr
from langchain_ollama import OllamaEmbeddings
from utils.constant import GEMINI_API_KEY



def get_gemini_embedding(text: str) -> list:
    # print(f"Using Gemini API Key: {GEMINI_API_KEY}")
    if GEMINI_API_KEY is None: 
        raise ValueError("Gemini API Key is required")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=SecretStr(GEMINI_API_KEY)
    )
    return embeddings.embed_query(text)


def get_ollama_embedding(text: str) -> list:
    embedding = OllamaEmbeddings(
        model="gemma3:latest",
    )
    return embedding.embed_query(text)