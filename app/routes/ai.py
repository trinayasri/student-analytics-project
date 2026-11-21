"""
ai.py - AI Diagnostic & Recommendation REST API Endpoints

Provides:
- On-demand AI analysis for individual students via Google Gemini with automatic fallback.
- Structured performance diagnosis (weak subjects, gaps, priority curriculum topics).
- Historical AI recommendation retrieval.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, User, AIRecommendation
from app.schemas import FullAIAnalysisResponse, AIRecommendationHistoryItem
from app.core.deps import get_current_user_optional
from app.services.ai_service import generate_and_save_ai_analysis
from app.routes.students import _resolve_student

router = APIRouter()


@router.post(
    "/analyze/{identifier}",
    response_model=FullAIAnalysisResponse,
    summary="Generate AI performance analysis and study plan for a student"
)
def run_ai_student_analysis(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Executes an intelligent diagnostic evaluation for a student:
    - Analyzes actual marks in Mathematics, Programming, DSA, DBMS, and ML.
    - Evaluates attendance and academic risk factors.
    - Identifies strong vs. weak subjects with precise score gaps.
    - Suggests prioritized syllabus topics and generates an actionable 5-day study plan.
    - Uses Google Gemini API when configured; otherwise runs high-fidelity pedagogical fallback.
    """
    student = _resolve_student(identifier, db, current_user=current_user)
    return generate_and_save_ai_analysis(db, student)


@router.get(
    "/history/{identifier}",
    response_model=List[AIRecommendationHistoryItem],
    summary="Get historical AI recommendations for a student"
)
def get_ai_recommendation_history(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieves previous AI diagnostic records generated for this student.
    """
    student = _resolve_student(identifier, db, current_user=current_user)
    recommendations = (
        db.query(AIRecommendation)
        .filter(AIRecommendation.student_id == student.student_id)
        .order_by(AIRecommendation.generated_at.desc())
        .all()
    )
    return recommendations
