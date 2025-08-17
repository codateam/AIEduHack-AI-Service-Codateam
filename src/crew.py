from crewai import Crew, Process
from utils.constant import GEMINI_API_KEY, GEMINI_MODEL
# Import directly from the agents.py file using importlib
import importlib.util
import sys
from pathlib import Path
from utils.course_material_service import CourseMaterialService

# Load the agents.py file directly
agents_file_path = Path(__file__).parent / "agents.py"
spec = importlib.util.spec_from_file_location("agents_module", agents_file_path)
agents_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agents_module)

# Get the specific items we need
tutor = agents_module.tutor
translator = agents_module.translator
task1 = agents_module.task1
task2 = agents_module.task2

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