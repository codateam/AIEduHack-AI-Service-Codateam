from crewai import Crew, Process
from utils.constant import GEMINI_API_KEY, GEMINI_MODEL
from src.agents import tutor, translator, task1, task2
from utils.course_material_service import CourseMaterialService

class LearningAIAgent:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.course_material_service = CourseMaterialService()
        print(f"api_key: {self.api_key}")
        print(f"model: {self.model}")
    
    def create_crew(self, lang, course_id, additional_info):
        context = self.course_material_service.query(course_id, additional_info)
        crew = Crew(
                agents=[tutor, translator],
                tasks=[task1(lang, context, additional_info), task2(lang, context, additional_info)],
                api_key=self.api_key,
                model=self.model,
                name="Learning AI Agent",
                description="An AI agent tutor that can teacher student based on material in user provided language",
                # memory=True,
                temperature=0.7,
                process=Process.sequential,
                # embedder={
                #     "provider": "gemini",  # Match your LLM provider
                #     "config": {
                #         "api_key": self.api_key,
                #         "model": self.model
                #     }
                # },
                verbose=True
            )

        result = crew.kickoff(inputs={"context": context, "language":lang, "additional_info": additional_info})

        return result.raw