from pydantic import BaseModel, Field 
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

# Configuration Models
class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    LOCAL_OLLAMA = "local_ollama"
    LOCAL_LLAMACPP = "local_llamacpp"

class QuestionType(str, Enum):
    MCQ = "mcq"
    GERMAN = "fill-in-the-blank" # German questions
    THEORY = "essay"


# class LLMConfig(BaseModel):
#     provider: LLMProvider = LLMProvider.LOCAL_OLLAMA 
#     api_key: Optional[str] = None
#     base_url: Optional[str] = None  # For local LLMs
#     model_name: str= "gemma3:latest"  # Default model for local LLMs
#     temperature: float = 0.7
#     max_tokens: int = 

class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.GEMINI
    model_name: str= "gemini-2.5-flash"  # Default model for local LLMs
    temperature: float = 0.7
    max_tokens: int = 20000


class MCQOption(BaseModel):
    option: str
    is_correct: bool

class QuestionRequest(BaseModel):
    # topic: str
    course_id: str
    subject: str
    difficulty: Literal["easy", "medium", "hard"]
    question_types: List[QuestionType]
    num_questions: int = Field(ge=1, le=100)
    llm_config: LLMConfig
    additional_context: Optional[str] = None
    mark: int = 10  # Default points for each question

class GeneratedQuestion(BaseModel):
    id: str
    type: QuestionType
    question: str
    options: Optional[List[MCQOption]] = None  # Only for MCQ
    expected_answer: Optional[str] = None  # For German and Theory
    mark: int = 10
    metadata: Dict[str, Any] = {}

class GradingRequest(BaseModel):
    id: str
    question: str
    course_id: str
    expected_answer: str
    student_answer: str
    type: QuestionType
    points: int = 10
    llm_config: LLMConfig = LLMConfig()  # Default to local Ollama config

class GradingResult(BaseModel):
    question_id: str
    score: float
    max_score: float
    percentage: float
    feedback: str
    detailed_analysis: Dict[str, Any]

class BatchGradingRequest(BaseModel):
    answers: List[GradingRequest]

class LearningRequest(BaseModel):
    lang: str
    # context: str
    course_id: str
    additional_info: Optional[str] = None
    # subject: str
    # difficulty: Literal["easy", "medium", "hard"]
    # question_types: List[QuestionType]
    # num_questions: int = Field(ge=1, le=100)
    # llm_config: LLMConfig = LLMConfig()  # Default to local Ollama config
    # mark: int = 10  # Default points for each question

class LearningResponse(BaseModel):
    content: str
    # course_id: str
    # subject: str
    # difficulty: Literal["easy", "medium", "hard"]
    # question_types: List[QuestionType]
    # num_questions: int = Field(ge=1, le=100)
    # llm_config: LLMConfig = LLMConfig()  # Default to local Ollama config
    # additional_context: Optional[str] = None
    # mark: int = 10  # Default points for each question