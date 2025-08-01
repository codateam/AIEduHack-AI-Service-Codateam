

from fastapi import HTTPException
import json
from utils.models import GeneratedQuestion, QuestionRequest, QuestionType
from utils.llm_client import LLMClient
from typing import List
from utils.utils import prompt_template
from utils.course_material_service import CourseMaterialService


# Question Generator Service
class QuestionGenerator:
    def __init__(self, llm_client: LLMClient, course_material_service: CourseMaterialService = CourseMaterialService()):
        self.llm_client = llm_client
        self.course_material_service = course_material_service
    
    async def generate_questions(self, request: QuestionRequest) -> List[GeneratedQuestion]:
        questions = []
       
        # print(f"Generating {request.num_questions} questions of types {request.question_types} for topic '{request.topic}'")
        for question_type in request.question_types:
            # print(f"Generating {question_type.value} questions...")
            type_questions = await self._generate_questions_by_type(
                request, question_type, request.num_questions // len(request.question_types)
            )
            questions.extend(type_questions)
        
        return questions
    
    async def _generate_questions_by_type(self, request: QuestionRequest, 
                                        question_type: QuestionType, 
                                        count: int) -> List[GeneratedQuestion]:
        if question_type == QuestionType.MCQ:
            return await self._generate_mcq_questions(request, count)
        elif question_type == QuestionType.GERMAN:
            return await self._generate_german_questions(request, count)
        elif question_type == QuestionType.THEORY:
            return await self._generate_theory_questions(request, count)
    
    async def _generate_mcq_questions(self, request: QuestionRequest, count: int) -> List[GeneratedQuestion]:
        context = self.course_material_service.query(request.course_id, request.subject)
        # print(f"Context {count} {context}")
        prompt = prompt_template.format(
        subject=request.subject,
        question_type=QuestionType.MCQ.value,
        difficulty=request.difficulty,
        additional_context=request.additional_context or "",
        num_questions=count,
        context=context if context else "No course material available for this topic.",
        mark=request.mark if request.mark else 10  # Default mark for each question
        )
        
        response = await self.llm_client.generate_text(prompt)
        try:
            return self._parse_question_response(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse MCQ response: {str(e)}")
    
    async def _generate_german_questions(self, request: QuestionRequest, count: int) -> List[GeneratedQuestion]:
        context = self.course_material_service.query(request.course_id, request.subject)
        prompt = prompt_template.format(
        subject=request.subject,
        question_type=QuestionType.GERMAN.value,
        difficulty=request.difficulty,
        additional_context=request.additional_context or "",
        num_questions=count,
        context=context if context else "No course material available for this topic.",
        mark=request.mark if request.mark else 10  # Default mark for each question
        )
        
        response = await self.llm_client.generate_text(prompt)
        try:
            return self._parse_question_response(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse German response: {str(e)}")
        # response = await self.llm_client.generate_text(prompt)
        # return self._parse_text_response(response, QuestionType.GERMAN)
    
    async def _generate_theory_questions(self, request: QuestionRequest, count: int) -> List[GeneratedQuestion]:
        context = self.course_material_service.query(request.course_id, request.subject)
        print(f"Context {count} {context}")
        prompt = prompt_template.format(
        subject=request.subject,
        question_type=QuestionType.THEORY.value,
        difficulty=request.difficulty,
        additional_context=request.additional_context or "",
        num_questions=count,
        context=context if context else "No course material available for this topic.",
        mark=request.mark if request.mark else 10  # Default mark for each question
        )
        
        response = await self.llm_client.generate_text(prompt)
        try:
            return self._parse_question_response(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse theory response: {str(e)}")
    
    def _parse_question_response(self, response: str) -> List[GeneratedQuestion]:
        try:
            # Try to extract JSON block if extra text is present
            cleaned_content = response.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:-3]
            
            question_json = json.loads(cleaned_content)
            return question_json
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")
    