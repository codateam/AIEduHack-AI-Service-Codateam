# LLM Question Generation & Grading System

## Table of Contents
- [Overview](#overview)
- [Use Cases](#use-cases)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Key Components & Modules](#key-components--modules)
- [API Usage Examples](#api-usage-examples)
- [Extending the Project](#extending-the-project)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview
This project is an automated question generation and grading system powered by Large Language Models (LLMs). It supports multiple LLM providers (OpenAI, Anthropic, Gemini, DeepSeek, and local models) and is designed to generate various types of questions (MCQ, fill-in-the-blank, essay) and grade student answers automatically. The system is modular, extensible, and can be integrated into e-learning platforms, assessment tools, or used for research.

## Use Cases
- **E-learning platforms**: Auto-generate quizzes and assignments for students.
- **Educators**: Quickly create diverse question sets and automate grading.
- **Students**: Self-assessment and practice with instant feedback.
- **Research**: Experiment with LLM-based question generation and grading.

## Features
- **Multi-provider LLM support**: Easily switch between OpenAI, Anthropic, Gemini, DeepSeek, and local LLMs (Ollama, llama.cpp).
- **Flexible question generation**: Generate MCQs, fill-in-the-blank (German), and essay questions.
- **Automated grading**: Grade student answers using LLMs, with detailed feedback and analysis.
- **Customizable configuration**: Set model, temperature, max tokens, and more per request.
- **ChromaDB integration**: For efficient storage and retrieval of embeddings and course materials.
- **Batch grading**: Grade multiple answers in a single request.
- **Context-aware**: Use course materials to generate relevant questions.

## Project Structure
```text
llm-question/
│   main.py                  # Entry point for the API or CLI
│   requirements.txt         # Python dependencies
│   usage_examples.py        # Example usage scripts
│
├── utils/
│   ├── constant.py
│   ├── course_material_service.py
│   ├── embedding.py
│   ├── grading_service.py
│   ├── llm_client.py
│   ├── models.py            # Pydantic models and enums
│   ├── questions_generator.py
│   └── utils.py
│
├── chroma_db/               # ChromaDB files for vector storage
```

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <repo-url>
cd llm-question
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
# Or
source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Set your LLM provider API keys as environment variables or in a `.env` file (if supported by your deployment):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY` (for Gemini)

### 5. ChromaDB Setup
ChromaDB is used for storing and retrieving course material embeddings. The default setup uses a local SQLite database in `chroma_db/`. No extra setup is needed for local use.

## Configuration
- Configure the LLM provider and model in the `LLMConfig` model (see `utils/models.py`).
- Set API keys and base URLs as needed for cloud providers.
- Adjust temperature, max tokens, and other parameters per request.
- You can override the default configuration per request.

## Key Components & Modules

### 1. Models (`utils/models.py`)
Defines all Pydantic models and enums used throughout the system:
- **LLMProvider**: Enum for supported LLMs.
- **QuestionType**: Enum for question types (MCQ, fill-in-the-blank, essay).
- **LLMConfig**: Model for LLM configuration (provider, model name, temperature, max tokens).
- **MCQOption**: Model for MCQ options.
- **QuestionRequest**: Model for question generation requests.
- **GeneratedQuestion**: Model for generated questions.
- **GradingRequest**: Model for grading requests.
- **GradingResult**: Model for grading results.
- **BatchGradingRequest**: Model for batch grading.

### 2. Question Generation (`utils/questions_generator.py`)
- **Functionality**: Generates questions based on the `QuestionRequest` model.
- **Highlights**:
  - Supports MCQ, fill-in-the-blank, and essay questions.
  - Integrates with course material and embeddings for context-aware question generation.
  - Selects LLM provider dynamically.

### 3. Grading Service (`utils/grading_service.py`)
- **Functionality**: Grades student answers using LLMs.
- **Highlights**:
  - Provides detailed feedback and scoring.
  - Supports batch grading.
  - Uses LLMConfig for provider/model selection.

### 4. LLM Client (`utils/llm_client.py`)
- **Functionality**: Handles communication with different LLM providers.
- **Highlights**:
  - Abstracts API calls and local model inference.
  - Handles authentication and error management.

### 5. Embedding & Course Material
- **`utils/embedding.py`**: Manages embeddings for course materials using ChromaDB.
- **`utils/course_material_service.py`**: Retrieves relevant context for question generation and grading.

### 6. Main Application (`main.py`)
- **Functionality**: Entry point for running the API or CLI.
- **Highlights**: Handles request routing and orchestration.

## API Usage Examples

### 1. Generate Questions
**Request Example:**
```python
from utils.models import QuestionRequest, LLMConfig, QuestionType

req = QuestionRequest(
    course_id="CS101",
    subject="Data Structures",
    difficulty="medium",
    question_types=[QuestionType.MCQ, QuestionType.THEORY],
    num_questions=5,
    llm_config=LLMConfig(provider="openai", model_name="gpt-3.5-turbo"),
    additional_context="Focus on binary trees.",
    mark=10
)
```
**Response Example:**
```json
{
  "questions": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "What is the time complexity of searching in a balanced binary search tree?",
      "options": [
        {"option": "O(log n)", "is_correct": true},
        {"option": "O(n)", "is_correct": false},
        {"option": "O(1)", "is_correct": false}
      ],
      "expected_answer": null,
      "mark": 10,
      "metadata": {}
    }
  ]
}
```

### 2. Grade an Answer
**Request Example:**
```python
from utils.models import GradingRequest, QuestionType

req = GradingRequest(
    id="q1",
    question="What is the time complexity of searching in a balanced binary search tree?",
    course_id="CS101",
    expected_answer="O(log n)",
    student_answer="O(log n)",
    type=QuestionType.MCQ,
    points=10
)
```
**Response Example:**
```json
{
  "question_id": "q1",
  "score": 10,
  "max_score": 10,
  "percentage": 100.0,
  "feedback": "Correct answer!",
  "detailed_analysis": {}
}
```

### 3. Batch Grading
**Request Example:**
```python
from utils.models import BatchGradingRequest

batch_req = BatchGradingRequest(answers=[...])
```

## Extending the Project
- Add new LLM providers by extending the `LLMProvider` enum and updating `llm_client.py`.
- Add new question types by updating `QuestionType` and the question generator logic.
- Integrate additional storage or context sources as needed.
- Add new endpoints or CLI commands in `main.py`.

## Troubleshooting & FAQ
- **Q: I get an authentication error with my LLM provider.**
  - A: Ensure your API key is set correctly as an environment variable.
- **Q: ChromaDB errors?**
  - A: Ensure the `chroma_db/` directory is writable and not corrupted.
- **Q: How do I add a new question type?**
  - A: Update `QuestionType` in `models.py` and extend the logic in `questions_generator.py`.

## Contributing
1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## License
[MIT License](LICENSE)

## Contact
For questions or contributions, please open an issue or pull request.
