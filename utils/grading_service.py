from fastapi import HTTPException
import json
from utils.models import  GradingRequest, GradingResult, QuestionType
from utils.llm_client import LLMClient
from utils.utils import grading_prompt_template
from utils.course_material_service import CourseMaterialService



# Grading Service
class GradingService:
    def __init__(self, llm_client: LLMClient, course_material_service: CourseMaterialService = CourseMaterialService()):
        self.llm_client = llm_client
        self.course_material_service = course_material_service

    
    async def grade_answer(self, request: GradingRequest) -> GradingResult:

        if request.type == QuestionType.MCQ:
            raise HTTPException(status_code=400, detail="MCQ questions don't need LLM grading")
        
        prompt = self._create_grading_prompt(request)
        response = await self.llm_client.generate_text(prompt)
        return self._parse_grading_response(response, request.points)
    
    def _create_grading_prompt(self, request: GradingRequest) -> str:
        question_type_context = {
            QuestionType.GERMAN: "Evaluate the following fill-in-the-blank answer based on how well it answers the question and meaning accuracy.",
            QuestionType.THEORY: "Focus on conceptual understanding, completeness of explanation, accuracy of information, and logical reasoning."
        }

        context = self.course_material_service.query(request.course_id)

        prompt = grading_prompt_template.format(
            question_id=request.id,
            question_type=request.type,
            question_text=request.question,
            expected_answer=request.expected_answer,
            student_answer=request.student_answer,
            max_points=request.points,
            grading_criteria=question_type_context.get(request.type, ""),
            context=context if context else "No course material available for this topic."
        )   
        
        return prompt
    
    def _parse_grading_response(self, response: str, max_points: int) -> GradingResult:
        try:
            # Try to extract JSON block if extra text is present
            cleaned_content = response.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:-3]
            
            question_json = json.loads(cleaned_content)
            return question_json
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")
        # try:
        #     data = json.loads(response.strip())
        #     score = min(max_points, max(0, data["score"]))
        #     percentage = (score / max_points) * 100
            
        #     detailed_analysis = {
        #         "strengths": data.get("strengths", []),
        #         "improvements": data.get("improvements", []),
        #         "accuracy_score": data.get("accuracy_score", 0),
        #         "completeness_score": data.get("completeness_score", 0),
        #         "language_quality_score": data.get("language_quality_score", 0)
        #     }
            
        #     return GradingResult(
        #         question_id=data.get("question_id", ""),
        #         score=score,
        #         max_score=max_points,
        #         percentage=percentage,
        #         feedback=data["feedback"],
        #         detailed_analysis=detailed_analysis
        #     )
        # except Exception as e:
        #     raise HTTPException(status_code=500, detail=f"Failed to parse grading response: {str(e)}")
