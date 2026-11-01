"""
students.py - Student Management API Endpoints

Handles CRUD operations, pagination, search, and filtering for students.
Provides robust HTTP error responses (400, 404, 409) with informative detail messages.
"""

import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student
from app import crud
from app.schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    PaginatedStudentResponse,
    MessageResponse
)

router = APIRouter()


def _resolve_student(identifier: str, db: Session) -> Student:
    """Helper to locate a student by database integer ID or string student_id."""
    student = None
    if identifier.isdigit():
        student = crud.get_student_by_id(db, int(identifier))
    if not student:
        student = crud.get_student_by_student_id(db, identifier)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{identifier}' not found."
        )
    return student


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student record"
)
def create_new_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new student record with demographic and subject marks data.
    
    Validations:
    - Unique Student ID (e.g. STU1001)
    - Unique Email Address
    - Subject marks in range [0.0, 100.0]
    - Semester in range [1, 8]
    """
    # Check for duplicate student_id
    if crud.get_student_by_student_id(db, student_in.student_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student ID '{student_in.student_id}' already exists in the system."
        )

    # Check for duplicate email
    if crud.get_student_by_email(db, student_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{student_in.email}' is already registered with another student."
        )

    return crud.create_student(db=db, student_in=student_in)


@router.get(
    "/",
    response_model=PaginatedStudentResponse,
    summary="List all students with pagination, search, and filtering"
)
def list_students(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for name or student ID"),
    department: Optional[str] = Query(None, description="Filter by exact department name"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of students.
    Supports substring search by student name or student ID, and exact filtering by department/semester.
    """
    skip = (page - 1) * page_size
    items, total_count = crud.get_students(
        db=db,
        skip=skip,
        limit=page_size,
        search=search,
        department=department,
        semester=semester
    )

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

    return PaginatedStudentResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/departments",
    response_model=List[str],
    summary="Get list of all active departments"
)
def get_departments(db: Session = Depends(get_db)):
    """Returns a distinct list of departments present in student records."""
    return crud.get_departments_list(db)


@router.get(
    "/{identifier}",
    response_model=StudentResponse,
    summary="Get individual student details by ID or Student ID"
)
def get_student(
    identifier: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details and computed metrics for a single student.
    Can accept either the internal integer ID or the academic Student ID (e.g. STU1001).
    """
    return _resolve_student(identifier, db)


@router.put(
    "/{identifier}",
    response_model=StudentResponse,
    summary="Update an existing student record"
)
def update_student_record(
    identifier: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates student demographics or marks.
    If marks are modified, total marks, average, percentage, grade, and support status
    are automatically recomputed.
    """
    db_student = _resolve_student(identifier, db)

    # Check email conflict if email is updated
    if student_in.email and student_in.email.lower() != db_student.email.lower():
        existing = crud.get_student_by_email(db, student_in.email)
        if existing and existing.id != db_student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{student_in.email}' is already taken by another student."
            )

    return crud.update_student(db=db, db_student=db_student, student_update=student_in)


@router.delete(
    "/{identifier}",
    response_model=MessageResponse,
    summary="Delete a student record"
)
def delete_student_record(
    identifier: str,
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a student record from the database.
    """
    db_student = _resolve_student(identifier, db)
    student_id_val = db_student.student_id
    student_name = db_student.name

    crud.delete_student(db=db, db_student=db_student)

    return MessageResponse(
        message=f"Student record '{student_id_val}' ({student_name}) successfully deleted.",
        detail=f"Record with ID {db_student.id} has been removed from persistent storage."
    )
