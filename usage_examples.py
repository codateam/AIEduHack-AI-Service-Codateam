# API Usage Examples

import requests
import json

# Base URL of your API
BASE_URL = "http://localhost:8000"

# Example 1: Generate questions using Anthropic Claude
def generate_questions_anthropic():
    url = f"{BASE_URL}/generate-questions"
    
    payload = {
        "topic": "Machine Learning Basics",
        "subject": "Computer Science",
        "difficulty": "medium",
        "question_types": ["mcq", "theory"],
        "num_questions": 4,
        "llm_config": {
            "provider": "anthropic",
            "api_key": "your-anthropic-api-key",
            "model_name": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "additional_context": "Focus on supervised learning algorithms"
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example 2: Generate questions using local Ollama
def generate_questions_ollama():
    url = f"{BASE_URL}/generate-questions"
    
    payload = {
        "topic": "Deutsche Grammatik",
        "subject": "German Language",
        "difficulty": "easy",
        "question_types": ["german"],
        "num_questions": 3,
        "llm_config": {
            "provider": "local_ollama",
            "base_url": "http://localhost:11434",
            "model_name": "llama2",
            "temperature": 0.6,
            "max_tokens": 1500
        }
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example 3: Grade a German answer
def grade_german_answer():
    url = f"{BASE_URL}/grade-answer"
    
    payload = {
        "question_id": "german_123",
        "question_text": "Beschreiben Sie den Unterschied zwischen 'der', 'die' und 'das'.",
        "expected_answer": "'Der' ist der bestimmte Artikel für maskuline Substantive, 'die' für feminine Substantive und Plural, und 'das' für neutrale Substantive. Zum Beispiel: der Mann, die Frau, das Kind.",
        "student_answer": "'Der' ist für männliche Wörter, 'die' für weibliche Wörter und 'das' für sächliche Wörter. Beispiele sind der Hund, die Katze, das Haus.",
        "question_type": "german",
        "max_points": 10,
        "llm_config": {
            "provider": "openai",
            "api_key": "your-openai-api-key",
            "model_name": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 1000
        }
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example 4: Grade a theory answer
def grade_theory_answer():
    url = f"{BASE_URL}/grade-answer"
    
    payload = {
        "question_id": "theory_456",
        "question_text": "Explain the concept of overfitting in machine learning and how to prevent it.",
        "expected_answer": "Overfitting occurs when a model learns the training data too well, including noise and irrelevant patterns, leading to poor generalization on new data. Prevention methods include regularization, cross-validation, early stopping, dropout, and collecting more training data.",
        "student_answer": "Overfitting is when the model memorizes the training data and performs poorly on test data. We can use regularization and validation sets to prevent it.",
        "question_type": "theory",
        "max_points": 15,
        "llm_config": {
            "provider": "deepseek",
            "api_key": "your-deepseek-api-key",
            "model_name": "deepseek-chat",
            "temperature": 0.2,
            "max_tokens": 1200
        }
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example 5: Get supported providers
def get_providers():
    url = f"{BASE_URL}/supported-providers"
    response = requests.get(url)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Generate questions
    print("=== Generating Questions with Anthropic ===")
    questions = generate_questions_anthropic()
    print(json.dumps(questions, indent=2))
    
    print("\n=== Grading German Answer ===")
    german_grade = grade_german_answer()
    print(json.dumps(german_grade, indent=2))
    
    print("\n=== Supported Providers ===")
    providers = get_providers()
    print(json.dumps(providers, indent=2))

# Command line usage examples:

"""
# 1. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Generate questions with curl
curl -X POST "http://localhost:8000/generate-questions" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "Python Programming",
       "subject": "Computer Science",
       "difficulty": "medium",
       "question_types": ["mcq", "theory"],
       "num_questions": 2,
       "llm_config": {
         "provider": "local_ollama",
         "base_url": "http://localhost:11434",
         "model_name": "codellama",
         "temperature": 0.7,
         "max_tokens": 2000
       }
     }'

# 3. Grade an answer with curl
curl -X POST "http://localhost:8000/grade-answer" \
     -H "Content-Type: application/json" \
     -d '{
       "question_id": "test_1",
       "question_text": "What is a Python list?",
       "expected_answer": "A Python list is a mutable, ordered collection of items that can store different data types.",
       "student_answer": "A list is a way to store multiple items in Python.",
       "question_type": "theory",
       "max_points": 10,
       "llm_config": {
         "provider": "local_ollama",
         "base_url": "http://localhost:11434",
         "model_name": "llama2",
         "temperature": 0.3,
         "max_tokens": 1000
       }
     }'
"""