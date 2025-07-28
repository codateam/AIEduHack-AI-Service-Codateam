from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from utils.models import GeneratedQuestion, GradingResult

# Use your existing MCQOption and GeneratedQuestion models
mcq_parser = PydanticOutputParser(pydantic_object=GeneratedQuestion)
# use 
prompt_template = PromptTemplate(
    template=(
        "You are a university exam question generator.\n"
        "Generate {num_questions} {question_type} Based on the {subject} and {context} and should reflect a comprehensive coverage.\n"
        "Difficulty: {difficulty}\n"
        "{additional_context}\n"
        "Course Material: {context}\n"
        "Generate questions that are clear, concise, and suitable for university-level students.\n"
        "Generate expected answers for each question.\n"
        "add mark {mark} to each question\n"
        "Format your response as JSON matching this schema:\n"
        "{format_instructions}"
    ),
    input_variables=["subject","question_type", "difficulty", "additional_context", "num_questions", "context", "mark"],
    partial_variables={"format_instructions": mcq_parser.get_format_instructions()},
)


# Use your existing MCQOption and GeneratedQuestion models
grading_parser = PydanticOutputParser(pydantic_object=GradingResult)
# use 
grading_prompt_template = PromptTemplate(
    template=(
        "You are a university exam answer grader.\n"
        "Your task is to evaluate a student's answer to a university-level {question_type} question using the technical correctness of the response, based on the provided expected answer and grading criteria and the course materials\n"
        "Grade the following {question_type} answer:\n"
        "Question ID: {question_id}\n"
        "Question: {question_text}\n"
        "Expected Answer: {expected_answer}\n"
        "Student Answer: {student_answer}\n"
        "Maximum Points: {max_points}\n"
        "Grading Criteria: {grading_criteria}\n"
        "Provide a score between 0 and {max_points} \n"
        "Be strictly objective and focus on technical language and ignore gramatical mistakes where necessary, award less than 50% where the answer does correct technically "
        "Course material {context}"
        "Return your evaluation in this exact JSON format:\n" 
        "{format_instructions}"
        ""
    ),
    input_variables=["question_id", "question_type", "question_text", "expected_answer", "student_answer", "max_points", "grading_criteria", "context"],
    partial_variables={"format_instructions": grading_parser.get_format_instructions()},
)