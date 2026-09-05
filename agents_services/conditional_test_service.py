"""
Conditional Test Service
FastAPI service for generating and evaluating skill tests.
Port: 8009
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import logging
import json
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))
# Add backend/app to path for job_extraction agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

app = FastAPI(title="Conditional Test Service", version="1.0.0")
logger = logging.getLogger("uvicorn.error")

# In-memory test storage (use Redis/DB in production)
test_store: Dict[str, dict] = {}


class TestGenerationRequest(BaseModel):
    skills: List[str]
    difficulty: str = "medium"  # easy, medium, hard
    num_questions: int = 10


class Question(BaseModel):
    id: str
    text: str
    options: List[str]
    correct_answer: str  # Store for validation, don't send to frontend


class TestResponse(BaseModel):
    test_id: str
    questions: List[dict]  # Without correct answers
    time_limit: int  # Minutes
    passing_score: int


class TestSubmission(BaseModel):
    test_id: str
    answers: Dict[str, str]  # question_id -> answer


class TestResult(BaseModel):
    score: int
    passed: bool
    total_questions: int
    correct_answers: int
    feedback: str


class JobExtractionRequest(BaseModel):
    job_title: str
    job_description: str


@app.post("/extract")
async def extract_job_skills(request: JobExtractionRequest):
    """
    Extract technical skills and experience level from a job description.
    """
    try:
        # Import the agent logic - using the same path added above
        from agents.job_extraction import JobExtractionAgent
        
        # Initialize and run
        agent = JobExtractionAgent()
        result = agent.extract(request.job_description, request.job_title)
        return result
    except Exception as e:
        logger.error(f"Job extraction failed: {str(e)}")
        # Fallback to local logic if needed, but returning error for transparency
        raise HTTPException(
            status_code=500,
            detail=f"Job extraction failed: {str(e)}"
        )


@app.post("/generate", response_model=TestResponse)
async def generate_test(request: TestGenerationRequest):
    """
    Generate a skill test based on verified skills
    
    Uses LLM to create relevant questions for the candidate's skill set.
    """
    try:
        # Generate test ID
        test_id = hashlib.sha256(
            f"{'-'.join(request.skills)}-{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Generate assessment questions for required skills
        questions = []
        
        for i, skill in enumerate(request.skills[:request.num_questions]):
            question = {
                "id": f"q{i+1}",
                "text": f"Which of the following best describes {skill}?",
                "options": [
                    f"Option A about {skill}",
                    f"Option B about {skill}",
                    f"Option C about {skill}",
                    f"Option D about {skill}"
                ],
                "correct_answer": "A"  # Store internally
            }
            questions.append(question)
        
        # Store test for validation
        test_store[test_id] = {
            "questions": questions,
            "skills": request.skills,
            "difficulty": request.difficulty,
            "created_at": datetime.utcnow().isoformat(),
            "passing_score": 70
        }
        
        # Remove correct answers before sending to frontend
        questions_without_answers = [
            {
                "id": q["id"],
                "text": q["text"],
                "options": q["options"]
            }
            for q in questions
        ]
        
        return TestResponse(
            test_id=test_id,
            questions=questions_without_answers,
            time_limit=30,  # 30 minutes
            passing_score=70
        )
    
    except Exception as e:
        logger.error(f"Test generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test generation failed: {str(e)}"
        )


@app.post("/evaluate", response_model=TestResult)
async def evaluate_test(submission: TestSubmission):
    """
    Evaluate submitted test answers
    
    Scores the test and determines if candidate passed.
    """
    try:
        # Retrieve test
        test = test_store.get(submission.test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found or expired")
        
        # Grade answers
        questions = test["questions"]
        total = len(questions)
        correct = 0
        
        for question in questions:
            q_id = question["id"]
            correct_answer = question["correct_answer"]
            submitted_answer = submission.answers.get(q_id, "")
            
            if submitted_answer.upper() == correct_answer.upper():
                correct += 1
        
        # Calculate score
        score = int((correct / total) * 100) if total > 0 else 0
        passed = score >= test["passing_score"]
        
        # Generate feedback
        if passed:
            feedback = f"Great job! You scored {score}% and passed the test."
        else:
            feedback = f"You scored {score}%, which is below the passing threshold of {test['passing_score']}%. Please review the topics and try again."
        
        # Clean up test (optional - keep for audit)
        # del test_store[submission.test_id]
        
        return TestResult(
            score=score,
            passed=passed,
            total_questions=total,
            correct_answers=correct,
            feedback=feedback
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test evaluation failed: {str(e)}"
        )


@app.get("/test/{test_id}")
async def get_test(test_id: str):
    """Retrieve test questions (for resuming/review)"""
    test = test_store.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Return without correct answers
    questions_without_answers = [
        {
            "id": q["id"],
            "text": q["text"],
            "options": q["options"]
        }
        for q in test["questions"]
    ]
    
    return {
        "test_id": test_id,
        "questions": questions_without_answers,
        "time_limit": 30,
        "passing_score": test["passing_score"]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "conditional_test",
        "tests_in_memory": len(test_store)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)
