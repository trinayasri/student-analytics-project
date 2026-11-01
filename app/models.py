"""
models.py - SQLAlchemy ORM Models

Defines the database schema for the Student Performance Analytics System.
Includes the Student table, column types, constraints, and business logic
for calculating academic metrics (total, average, percentage, grade, at-risk status).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base


def compute_metrics(
    math: float,
    prog: float,
    ds: float,
    db: float,
    ml: float
) -> dict:
    """
    Computes academic metrics based on subject marks.
    
    Academic Rules:
    - Total: sum of 5 subjects (max 500)
    - Average / Percentage: total / 5 (0 - 100%)
    - Grading Scale:
        A+ : >= 90%
        A  : >= 80% and < 90%
        B  : >= 70% and < 80%
        C  : >= 60% and < 70%
        D  : >= 50% and < 60%
        F  : < 50%
    - At-Risk Threshold:
        needs_support = True if average < 50.0 OR any subject mark < 40.0
    """
    total = round(float(math + prog + ds + db + ml), 2)
    avg = round(total / 5.0, 2)
    percentage = avg

    if avg >= 90.0:
        grade = "A+"
    elif avg >= 80.0:
        grade = "A"
    elif avg >= 70.0:
        grade = "B"
    elif avg >= 60.0:
        grade = "C"
    elif avg >= 50.0:
        grade = "D"
    else:
        grade = "F"

    # Academic support needed if aggregate is low or student failed any individual course
    needs_support = (avg < 50.0) or any(mark < 40.0 for mark in [math, prog, ds, db, ml])

    return {
        "total_marks": total,
        "average_marks": avg,
        "percentage": percentage,
        "grade": grade,
        "needs_support": needs_support
    }


class Student(Base):
    """
    SQLAlchemy model representing the 'students' table in SQLite.
    
    Stores core student demographic details, subject marks, and pre-calculated
    academic summary metrics for fast querying and reporting.
    """
    __tablename__ = "students"

    # Primary key (internal autoincrement integer)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Academic Roll/Registration ID (e.g. STU1001), must be unique
    student_id = Column(String(30), unique=True, index=True, nullable=False)

    # Student Demographics
    name = Column(String(100), index=True, nullable=False)
    department = Column(String(100), index=True, nullable=False)
    semester = Column(Integer, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)

    # Subject Marks (Range: 0.0 to 100.0)
    math_marks = Column(Float, nullable=False, default=0.0)
    programming_marks = Column(Float, nullable=False, default=0.0)
    data_structures_marks = Column(Float, nullable=False, default=0.0)
    database_marks = Column(Float, nullable=False, default=0.0)
    machine_learning_marks = Column(Float, nullable=False, default=0.0)

    # Cached Computed Analytics (calculated on insert / update)
    total_marks = Column(Float, nullable=False, default=0.0)
    average_marks = Column(Float, nullable=False, default=0.0)
    percentage = Column(Float, nullable=False, default=0.0)
    grade = Column(String(5), nullable=False, default="F")
    needs_support = Column(Boolean, nullable=False, default=False)

    # Audit Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def recalculate_metrics(self) -> None:
        """Recalculates cached derived fields from current subject marks."""
        metrics = compute_metrics(
            math=self.math_marks,
            prog=self.programming_marks,
            ds=self.data_structures_marks,
            db=self.database_marks,
            ml=self.machine_learning_marks
        )
        self.total_marks = metrics["total_marks"]
        self.average_marks = metrics["average_marks"]
        self.percentage = metrics["percentage"]
        self.grade = metrics["grade"]
        self.needs_support = metrics["needs_support"]

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}', avg={self.average_marks})>"
