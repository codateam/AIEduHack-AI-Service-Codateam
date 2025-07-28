import requests
import chromadb
from chromadb.config import Settings
from PyPDF2 import PdfReader
import tempfile
import os
from utils.embedding import get_gemini_embedding, get_ollama_embedding


# RAG Course Material Service
class CourseMaterialService:
    _instance = None

    def __new__(cls, persist_directory="chroma_db"):
        if cls._instance is None:
            cls._instance = super(CourseMaterialService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_directory="chroma_db"):
        if self._initialized:
            return
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "course_materials"
        # Use get_or_create_collection to avoid duplicate creation
        self.collection = self.client.get_or_create_collection(self.collection_name)
        self._initialized = True

    def add_pdf(self, course_id: str, pdf_url: str, embedding_provider: str, api_key: str):
        if not pdf_url.lower().endswith(".pdf"):
            raise ValueError("Only PDF links are accepted.")
        # Download PDF
        response = requests.get(pdf_url)
        
        if response.status_code != 200:
            raise ValueError("Failed to download PDF.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        reader = PdfReader(tmp_path)

        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        os.remove(tmp_path)
        # Choose embedding
        if embedding_provider == "gemini":
            embedding = get_gemini_embedding(text)
        elif embedding_provider == "local_ollama":
            embedding = get_ollama_embedding(text)
        else:
            raise ValueError("Unsupported embedding provider")
        # Store in ChromaDB with custom embedding
        self.collection.add(
            documents=[text],
            metadatas=[{"course_id": course_id, "pdf_url": pdf_url}],
            ids=[f"{course_id}_{os.path.basename(pdf_url)}"],
            embeddings=[embedding]
        )
        return True
    
    def add_pdfs(self, course_id: str, pdf_urls: list[str], embedding_provider: str):
        """Accepts an array of PDF URLs, processes and stores them in ChromaDB."""
        for i in range(len(pdf_urls)):
            pdf_url = pdf_urls[i]
            if not pdf_url.lower().endswith(".pdf"):
                raise ValueError(f"Only PDF links are accepted. Invalid: {pdf_url}")
            response = requests.get(pdf_url)
            print(f"Downloading PDF from {pdf_url} for course {response.status_code}")
            if response.status_code != 200:
                raise ValueError(f"Failed to download PDF: {pdf_url}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            reader = PdfReader(tmp_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            os.remove(tmp_path)
            chunks = split_text(text, max_length=2000)
            for i, chunk in enumerate(chunks):
                if embedding_provider == "gemini":
                    embedding = get_gemini_embedding(chunk)
                elif embedding_provider == "local_ollama":
                    embedding = get_ollama_embedding(chunk)
                else:
                    raise ValueError("Unsupported embedding provider")
                # Store in ChromaDB with custom embedding
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{"course_id": course_id, "pdf_url": pdf_url, "chunk": i}],
                    ids=[f"{course_id}_{os.path.basename(pdf_url)}_{i}"],
                    embeddings=[embedding]
                )
        return True

    def query(self, course_id: str, query_text: str=""):
        embedding = get_gemini_embedding(query_text)
        results = self.collection.query(
            query_texts=[query_text],
            where={"course_id": course_id},
            query_embeddings= [embedding],  
            # n_results=5,
            # ids=[course_id]
        )
        return results
    
    def delete_course_material(self, course_id: str):
        """Delete all course materials for a specific course."""
        self.collection.delete(where={"course_id": course_id})
        return True
    
    def update_course_material(self, course_id: str, pdf_url: str, embedding_provider: str, api_key: str):
        """Update course material by re-adding the PDF."""
        self.delete_course_material(course_id)
        self.add_pdf(course_id, pdf_url, embedding_provider, api_key)
        return True

def split_text(text, max_length=2000):
    """Split text into chunks of max_length characters."""
    paragraphs = text.split('\n')
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > max_length:
            if current:
                chunks.append(current)
            current = para
        else:
            current += "\n" + para if current else para
    if current:
        chunks.append(current)
    return chunks