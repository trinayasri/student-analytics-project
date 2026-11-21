"""
students.py - Student Management API Endpoints

Handles:
- CRUD operations, pagination, search, and multi-criteria filtering (department, semester, academic year, risk level).
- Bulk CSV and Excel (.xlsx) file ingestion with row-level validation and error tracking.
- Sample CSV import template download.
- Role-Based Access Control (restricting students to their own individual records).
"""

import io
import csv
import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Response
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.models import Student, User
from app import crud
from app.schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    PaginatedStudentResponse,
    BulkUploadResult,
    MessageResponse
)
from app.core.deps import get_current_user_optional

router = APIRouter()


def _normalize_header(header: str) -> str:
    """Standardizes column headers for flexible CSV/Excel field mapping."""
    clean = header.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "")
    mapping = {
        "id": "student_id",
        "roll_no": "student_id",
        "roll_number": "student_id",
        "registration_id": "student_id",
        "student_name": "name",
        "full_name": "name",
        "dept": "department",
        "branch": "department",
        "sem": "semester",
        "year": "academic_year",
        "session": "academic_year",
        "email_id": "email",
        "email_address": "email",
        "math": "math_marks",
        "mathematics": "math_marks",
        "prog": "programming_marks",
        "programming": "programming_marks",
        "python": "programming_marks",
        "ds": "data_structures_marks",
        "dsa": "data_structures_marks",
        "data_structures": "data_structures_marks",
        "db": "database_marks",
        "dbms": "database_marks",
        "database": "database_marks",
        "database_systems": "database_marks",
        "ml": "machine_learning_marks",
        "machine_learning": "machine_learning_marks",
        "attendance": "attendance_percentage",
        "attendance_pct": "attendance_percentage",
        "attendance_rate": "attendance_percentage"
    }
    return mapping.get(clean, clean)


def _resolve_student(identifier: str, db: Session, current_user: Optional[User] = None) -> Student:
    """Helper to locate a student by database ID or student_id and verify student role permissions."""
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

    # Restrict student users to only view/access their own profile
    if current_user and current_user.role == "student":
        student_id_allowed = None
        if current_user.student_profile:
            student_id_allowed = current_user.student_profile.student_id
        # Also check if username matches student_id
        if student.student_id != student_id_allowed and current_user.username.upper() != student.student_id.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Students are restricted to accessing their own records only."
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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Creates a new student record with demographic, attendance, and subject marks data.
    """
    if current_user and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not authorized to create new student records."
        )

    if crud.get_student_by_student_id(db, student_in.student_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student ID '{student_in.student_id}' already exists in the system."
        )

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
    academic_year: Optional[str] = Query(None, description="Filter by academic year (e.g. 2024-2025)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier: Good, Needs Attention, At Risk"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns a paginated list of students with multi-criteria filtering:
    - Search by Name or Student ID
    - Department, Semester, Academic Year, and Risk Level filters
    """
    # If authenticated as a student, restrict listing to self
    if current_user and current_user.role == "student":
        stu_id = current_user.student_profile.student_id if current_user.student_profile else current_user.username.upper()
        single_student = crud.get_student_by_student_id(db, stu_id)
        items = [single_student] if single_student else []
        return PaginatedStudentResponse(
            items=items,
            total_count=len(items),
            page=1,
            page_size=page_size,
            total_pages=1
        )

    skip = (page - 1) * page_size
    items, total_count = crud.get_students(
        db=db,
        skip=skip,
        limit=page_size,
        search=search,
        department=department,
        semester=semester,
        academic_year=academic_year,
        risk_level=risk_level
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
    "/academic-years",
    response_model=List[str],
    summary="Get list of all active academic years"
)
def get_academic_years(db: Session = Depends(get_db)):
    """Returns a distinct sorted list of academic years present in records."""
    return crud.get_academic_years_list(db)


@router.get(
    "/template/csv",
    summary="Download sample CSV template for bulk student upload"
)
def download_csv_template():
    """Provides a ready-to-use CSV template containing all required columns and an example row."""
    template_content = (
        "student_id,name,department,semester,academic_year,email,math_marks,programming_marks,data_structures_marks,database_marks,machine_learning_marks,attendance_percentage\n"
        "STU2001,John Doe,Computer Science & Engineering,4,2024-2025,john.doe@university.edu,85.0,90.0,78.0,88.0,92.0,91.5\n"
    )
    return Response(
        content=template_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_upload_template.csv"}
    )


@router.post(
    "/upload",
    response_model=BulkUploadResult,
    summary="Bulk upload student records via CSV or Excel (.xlsx/.xls)"
)
async def upload_student_records(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Parses and ingests student records in bulk from CSV or Excel spreadsheets.
    Performs field normalization, Pydantic type validation, and collision checks.
    """
    if current_user and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not authorized to upload student data batches."
        )

    filename = file.filename or ""
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    raw_rows: List[Dict[str, Any]] = []

    # Parse Excel vs CSV
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            df = pd.read_excel(io.BytesIO(content))
            # Convert NaN to None
            df = df.where(pd.notnull(df), None)
            raw_rows = df.to_dict(orient="records")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse Excel file: {str(e)}"
            )
    else:
        # Default to CSV
        try:
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            raw_rows = list(reader)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse CSV file: {str(e)}"
            )

    if not raw_rows:
        return BulkUploadResult(
            total_records=0,
            created_records=0,
            skipped_records=0,
            errors=["No data rows found in the uploaded file."]
        )

    created_count = 0
    skipped_count = 0
    errors: List[str] = []

    seen_batch_ids = set()
    seen_batch_emails = set()

    for idx, row in enumerate(raw_rows, start=2):  # Row 2 corresponds to spreadsheet line 2
        # Normalize keys
        clean_row = {}
        for k, v in row.items():
            if k is not None and v is not None:
                clean_key = _normalize_header(str(k))
                clean_row[clean_key] = v

        stu_id = str(clean_row.get("student_id", "")).strip()
        email = str(clean_row.get("email", "")).strip().lower()

        if not stu_id or not clean_row.get("name") or not email:
            skipped_count += 1
            errors.append(f"Row {idx}: Missing mandatory fields (student_id, name, or email).")
            continue

        # In-batch duplicate check
        if stu_id in seen_batch_ids:
            skipped_count += 1
            errors.append(f"Row {idx}: Duplicate student_id '{stu_id}' in uploaded file.")
            continue
        if email in seen_batch_emails:
            skipped_count += 1
            errors.append(f"Row {idx}: Duplicate email '{email}' in uploaded file.")
            continue

        # Database duplicate check
        if crud.get_student_by_student_id(db, stu_id):
            skipped_count += 1
            errors.append(f"Row {idx}: Student ID '{stu_id}' already exists in database.")
            continue
        if crud.get_student_by_email(db, email):
            skipped_count += 1
            errors.append(f"Row {idx}: Email '{email}' is already registered in database.")
            continue

        try:
            # Set defaults for optional fields if not in row
            if "academic_year" not in clean_row or not clean_row["academic_year"]:
                clean_row["academic_year"] = "2024-2025"
            if "attendance_percentage" not in clean_row or clean_row["attendance_percentage"] is None:
                clean_row["attendance_percentage"] = 85.0

            student_schema = StudentCreate(**clean_row)
            crud.create_student(db, student_schema)
            created_count += 1
            seen_batch_ids.add(stu_id)
            seen_batch_emails.add(email)
        except Exception as e:
            skipped_count += 1
            errors.append(f"Row {idx} ({stu_id}): Validation error - {str(e)}")

    return BulkUploadResult(
        total_records=len(raw_rows),
        created_records=created_count,
        skipped_records=skipped_count,
        errors=errors[:50]  # Limit error list to 50 items for response clarity
    )


@router.get(
    "/{identifier}",
    response_model=StudentResponse,
    summary="Get individual student details by ID or Student ID"
)
def get_student(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieves full details and computed metrics for a single student.
    Enforces student isolation: students can only access their own profile.
    """
    return _resolve_student(identifier, db, current_user=current_user)


@router.put(
    "/{identifier}",
    response_model=StudentResponse,
    summary="Update an existing student record"
)
def update_student_record(
    identifier: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Updates student demographics, attendance, or subject marks.
    Students cannot edit records.
    """
    if current_user and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not authorized to edit student records."
        )

    db_student = _resolve_student(identifier, db, current_user=current_user)

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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Permanently deletes a student record from the database.
    Students cannot delete records.
    """
    if current_user and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not authorized to delete student records."
        )

    db_student = _resolve_student(identifier, db, current_user=current_user)
    student_id_val = db_student.student_id
    student_name = db_student.name

    crud.delete_student(db=db, db_student=db_student)

    return MessageResponse(
        message=f"Student record '{student_id_val}' ({student_name}) successfully deleted.",
        detail=f"Record with ID {db_student.id} has been removed from persistent storage."
    )
