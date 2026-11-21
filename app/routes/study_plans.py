"""
study_plans.py - Personalized Study Plan REST API Endpoints

Provides:
- Retrieval of active weekly study plans with task completion status.
- Interactive toggling of study checklist items.
- Dynamic study plan re-generation based on weak subjects.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, User, StudyPlan, StudyPlanItem
from app.schemas import (
    StudyPlanResponse,
    StudyPlanItemToggleResponse,
    MessageResponse
)
from app.core.deps import get_current_user_optional
from app.services.ai_service import generate_and_save_ai_analysis
from app.routes.students import _resolve_student

router = APIRouter()


@router.get(
    "/{identifier}",
    response_model=StudyPlanResponse,
    summary="Get active study plan and task items for a student"
)
def get_student_study_plan(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieves the current active weekly study plan and its task items for a student.
    If no plan exists, generates an initial plan automatically.
    """
    student = _resolve_student(identifier, db, current_user=current_user)

    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.student_id == student.student_id, StudyPlan.status == "active")
        .order_by(StudyPlan.created_at.desc())
        .first()
    )

    if not plan:
        # Generate initial study plan on-demand
        ai_result = generate_and_save_ai_analysis(db, student)
        plan = db.query(StudyPlan).filter(StudyPlan.id == ai_result.study_plan_id).first()

    return plan


@router.patch(
    "/items/{item_id}/toggle",
    response_model=StudyPlanItemToggleResponse,
    summary="Toggle completion status of a study plan task item"
)
def toggle_study_plan_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Toggles is_completed between True and False for a specific study plan item.
    Updates completion timestamps and returns updated progress percentages.
    """
    item = db.query(StudyPlanItem).filter(StudyPlanItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study plan item with ID {item_id} not found."
        )

    plan = item.study_plan
    # Enforce student access isolation
    if current_user and current_user.role == "student":
        allowed_stu_id = current_user.student_profile.student_id if current_user.student_profile else current_user.username.upper()
        if plan.student_id != allowed_stu_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only modify their own study plan tasks."
            )

    # Toggle status
    item.is_completed = not item.is_completed
    item.completed_at = datetime.now(timezone.utc) if item.is_completed else None
    db.commit()

    # Recalculate plan completion statistics
    total_items = len(plan.items)
    completed_items = sum(1 for i in plan.items if i.is_completed)
    pct = round((completed_items / total_items) * 100.0, 1) if total_items > 0 else 0.0

    if completed_items == total_items and total_items > 0:
        plan.status = "completed"
    else:
        plan.status = "active"
    db.commit()

    return StudyPlanItemToggleResponse(
        item_id=item.id,
        is_completed=item.is_completed,
        completed_at=item.completed_at,
        plan_id=plan.id,
        completed_items_count=completed_items,
        total_items_count=total_items,
        completion_percentage=pct
    )


@router.post(
    "/generate/{identifier}",
    response_model=StudyPlanResponse,
    summary="Generate a fresh weekly study plan based on weak subjects"
)
def regenerate_student_study_plan(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Generates a new weekly study plan based on the student's latest course marks.
    """
    student = _resolve_student(identifier, db, current_user=current_user)
    ai_result = generate_and_save_ai_analysis(db, student)
    new_plan = db.query(StudyPlan).filter(StudyPlan.id == ai_result.study_plan_id).first()
    return new_plan
