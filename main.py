# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='.env')

# Now import everything else
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPBearer
import json
from datetime import datetime
from utils.models import GeneratedQuestion, QuestionRequest, GradingRequest, GradingResult, QuestionType, BatchGradingRequest, LearningRequest
from utils.llm_client import LLMClient
from utils.questions_generator import QuestionGenerator
from utils.course_material_service import CourseMaterialService
from src.crew import LearningAIAgent
from typing import List

from fastapi import Form, Body

# Request/Response Models
from utils.grading_service import GradingService
course_material_service = CourseMaterialService()

# FastAPI App
app = FastAPI(
    title="LLM Exam Question Generator and Grader API",
    description="Generate exam questions and grade answers using various LLM providers",
    version="1.0.0"
)

security = HTTPBearer(auto_error=False)

@app.get("/")
async def root():
    return {
        "message": "LLM Exam Question Generator and Grader API",
        "version": "1.0.0",
        "endpoints": {
            "generate_questions": "/generate-questions",
            "grade_answer": "/grade-answer",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/generate-questions", response_model=List[GeneratedQuestion])
async def generate_questions(request: QuestionRequest):
    print(f"Generating {request.num_questions} questions of types {request.question_types} for topic '{request}'")
    """Generate exam questions using specified LLM provider"""
    try:
        llm_client = LLMClient(request.llm_config)
        generator = QuestionGenerator(llm_client)
        questions = await generator.generate_questions(request)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@app.post("/batch-grade-answers", response_model=List[GradingResult])
async def batch_grade_answers(request: BatchGradingRequest):
    """Grade multiple fill-in-the-blank or Theory question answers using specified LLM provider answers in a single request. Each answer uses the same grading logic as the single endpoint."""
    results = []
    for answer in request.answers:
        try:
            llm_client = LLMClient(answer.llm_config)
            grader = GradingService(llm_client)
            result = await grader.grade_answer(answer)
            results.append(result)
        except Exception as e:
            # Optionally, you can append an error result or skip
            results.append(HTTPException(status_code=500, detail=f"Answer grading failed: {str(e)}"))
    return results

@app.post("/upload-multiple-course-materials")
async def upload_multiple_course_material(course_id: str = Form(...), pdf_urls: list[str] = Form(...)):
    print(f"Uploading multiple PDFs for course {course_id}: {pdf_urls}")
    """Upload a PDF course material by URL for RAG (LOCAL_OLLAMA and GEMINI only)."""
    try:
        formatted_urls= [url.strip() for url in pdf_urls[0].split(',')]
        course_material_service.add_pdfs(course_id, formatted_urls, "gemini" )
        return {"status": "success", "message": "PDFs uploaded and indexed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload course material: {str(e)}")


@app.post("/ai-teaching-agent")
def run_crew_api(request: LearningRequest):
    try:
        crew_run = LearningAIAgent()
        result = crew_run.create_crew(request.lang, request.course_id, request.additional_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run crew: {str(e)}")


@app.get("/supported-providers")
async def get_supported_providers():
    """Get list of supported LLM providers and their configuration requirements"""
    return {
        "providers": {
            "anthropic": {
                "requires_api_key": True,
                "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "base_url": "https://api.anthropic.com"
            },
            "openai": {
                "requires_api_key": True,
                "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                "base_url": "https://api.openai.com"
            },
            "gemini": {
                "requires_api_key": True,
                "models": ["gemini-pro", "gemini-pro-vision"],
                "base_url": "https://generativelanguage.googleapis.com"
            },
            "deepseek": {
                "requires_api_key": True,
                "models": ["deepseek-chat", "deepseek-coder"],
                "base_url": "https://api.deepseek.com"
            },
            "local_ollama": {
                "requires_api_key": False,
                "models": ["llama2", "codellama", "mistral", "custom"],
                "default_base_url": "http://localhost:11434"
            },
            "local_llamacpp": {
                "requires_api_key": False,
                "models": ["custom"],
                "default_base_url": "http://localhost:8080"
            }
        }
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


