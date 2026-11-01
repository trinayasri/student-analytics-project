"""
crud.py - Database CRUD (Create, Read, Update, Delete) & Analytics Operations

Encapsulates all database query logic separate from API routes.
Utilizes parameterized SQLAlchemy ORM queries to guarantee protection against SQL injection.
"""

from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models import Student, compute_metrics
from app.schemas import StudentCreate, StudentUpdate


def get_student_by_id(db: Session, student_db_id: int) -> Optional[Student]:
    """Retrieves a student by internal primary key ID."""
    return db.query(Student).filter(Student.id == student_db_id).first()


def get_student_by_student_id(db: Session, student_id: str) -> Optional[Student]:
    """Retrieves a student by unique academic student ID (e.g. STU1001)."""
    return db.query(Student).filter(Student.student_id == student_id.strip()).first()


def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    """Retrieves a student by email address."""
    return db.query(Student).filter(Student.email == email.strip().lower()).first()


def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[int] = None
) -> Tuple[List[Student], int]:
    """
    Retrieves students with optional search, filtering, and pagination.
    Returns a tuple of (items_list, total_matching_count).
    """
    query = db.query(Student)

    # Search filter (case-insensitive substring match on name or student_id)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.name.ilike(search_term),
                Student.student_id.ilike(search_term)
            )
        )

    # Department filter (exact match)
    if department:
        query = query.filter(Student.department == department.strip())

    # Semester filter
    if semester is not None:
        query = query.filter(Student.semester == semester)

    # Get total count before applying limit/offset
    total_count = query.count()

    # Apply pagination and order by registration ID
    items = query.order_by(Student.student_id.asc()).offset(skip).limit(limit).all()

    return items, total_count


def create_student(db: Session, student_in: StudentCreate) -> Student:
    """
    Inserts a new student record into the database with pre-computed academic metrics.
    """
    metrics = compute_metrics(
        math=student_in.math_marks,
        prog=student_in.programming_marks,
        ds=student_in.data_structures_marks,
        db=student_in.database_marks,
        ml=student_in.machine_learning_marks
    )

    db_student = Student(
        student_id=student_in.student_id.strip(),
        name=student_in.name.strip(),
        department=student_in.department.strip(),
        semester=student_in.semester,
        email=student_in.email.strip().lower(),
        math_marks=student_in.math_marks,
        programming_marks=student_in.programming_marks,
        data_structures_marks=student_in.data_structures_marks,
        database_marks=student_in.database_marks,
        machine_learning_marks=student_in.machine_learning_marks,
        total_marks=metrics["total_marks"],
        average_marks=metrics["average_marks"],
        percentage=metrics["percentage"],
        grade=metrics["grade"],
        needs_support=metrics["needs_support"]
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(
    db: Session,
    db_student: Student,
    student_update: StudentUpdate
) -> Student:
    """
    Updates an existing student record and recalculates metrics if marks changed.
    """
    update_data = student_update.model_dump(exclude_unset=True)

    marks_changed = False
    mark_fields = {
        "math_marks",
        "programming_marks",
        "data_structures_marks",
        "database_marks",
        "machine_learning_marks"
    }

    for key, value in update_data.items():
        if key in mark_fields and getattr(db_student, key) != value:
            marks_changed = True
        setattr(db_student, key, value)

    # If email was updated, ensure lowercase
    if "email" in update_data and update_data["email"]:
        db_student.email = update_data["email"].lower()

    # Recalculate metrics if any subject mark was modified
    if marks_changed:
        db_student.recalculate_metrics()

    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, db_student: Student) -> bool:
    """Deletes a student record from the database."""
    db.delete(db_student)
    db.commit()
    return True


# --- Analytics Operations ---

def get_overall_summary(db: Session) -> Dict[str, Any]:
    """Calculates college-wide academic key performance indicators (KPIs)."""
    total_students = db.query(func.count(Student.id)).scalar() or 0

    if total_students == 0:
        return {
            "total_students": 0,
            "overall_average": 0.0,
            "highest_average": 0.0,
            "lowest_average": 0.0,
            "pass_percentage": 0.0,
            "at_risk_count": 0,
            "top_performer": None
        }

    overall_avg = db.query(func.avg(Student.average_marks)).scalar() or 0.0
    highest_avg = db.query(func.max(Student.average_marks)).scalar() or 0.0
    lowest_avg = db.query(func.min(Student.average_marks)).scalar() or 0.0

    at_risk_count = db.query(func.count(Student.id)).filter(Student.needs_support == True).scalar() or 0
    passed_count = db.query(func.count(Student.id)).filter(Student.needs_support == False).scalar() or 0
    pass_pct = round((passed_count / total_students) * 100.0, 2)

    top_student = db.query(Student).order_by(Student.average_marks.desc()).first()

    return {
        "total_students": total_students,
        "overall_average": round(float(overall_avg), 2),
        "highest_average": round(float(highest_avg), 2),
        "lowest_average": round(float(lowest_avg), 2),
        "pass_percentage": pass_pct,
        "at_risk_count": at_risk_count,
        "top_performer": top_student
    }


def get_department_analytics(db: Session) -> List[Dict[str, Any]]:
    """Calculates performance aggregated by academic department."""
    results = (
        db.query(
            Student.department,
            func.count(Student.id).label("student_count"),
            func.avg(Student.average_marks).label("average_marks"),
            func.max(Student.average_marks).label("highest_marks"),
            func.min(Student.average_marks).label("lowest_marks")
        )
        .group_by(Student.department)
        .order_by(func.avg(Student.average_marks).desc())
        .all()
    )

    return [
        {
            "department": row.department,
            "student_count": row.student_count,
            "average_marks": round(float(row.average_marks), 2),
            "highest_marks": round(float(row.highest_marks), 2),
            "lowest_marks": round(float(row.lowest_marks), 2)
        }
        for row in results
    ]


def get_grade_distribution(db: Session) -> List[Dict[str, Any]]:
    """Calculates counts and percentages for each grade tier."""
    total_students = db.query(func.count(Student.id)).scalar() or 0
    grades = ["A+", "A", "B", "C", "D", "F"]

    if total_students == 0:
        return [{"grade": g, "count": 0, "percentage": 0.0} for g in grades]

    counts = (
        db.query(Student.grade, func.count(Student.id))
        .group_by(Student.grade)
        .all()
    )
    count_dict = {grade: cnt for grade, cnt in counts}

    return [
        {
            "grade": g,
            "count": count_dict.get(g, 0),
            "percentage": round((count_dict.get(g, 0) / total_students) * 100.0, 2)
        }
        for g in grades
    ]


def get_subject_averages(db: Session) -> List[Dict[str, Any]]:
    """Calculates the average, max, and min marks across each subject."""
    total_students = db.query(func.count(Student.id)).scalar() or 0
    if total_students == 0:
        return []

    subjects = [
        ("Mathematics", Student.math_marks),
        ("Programming", Student.programming_marks),
        ("Data Structures", Student.data_structures_marks),
        ("Database Systems", Student.database_marks),
        ("Machine Learning", Student.machine_learning_marks)
    ]

    result = []
    for subject_name, col in subjects:
        avg_score = db.query(func.avg(col)).scalar() or 0.0
        max_score = db.query(func.max(col)).scalar() or 0.0
        min_score = db.query(func.min(col)).scalar() or 0.0
        result.append({
            "subject": subject_name,
            "average_score": round(float(avg_score), 2),
            "highest_score": round(float(max_score), 2),
            "lowest_score": round(float(min_score), 2)
        })

    return result


def get_at_risk_students(db: Session, limit: int = 100) -> List[Student]:
    """Retrieves list of students identified as needing academic support."""
    return (
        db.query(Student)
        .filter(Student.needs_support == True)
        .order_by(Student.average_marks.asc())
        .limit(limit)
        .all()
    )


def get_departments_list(db: Session) -> List[str]:
    """Returns a distinct sorted list of all active departments."""
    rows = db.query(Student.department).distinct().order_by(Student.department.asc()).all()
    return [row[0] for row in rows if row[0]]
