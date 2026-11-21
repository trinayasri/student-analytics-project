"""
models.py - SQLAlchemy ORM Models for Multi-Table Architecture

Defines database schemas for:
- Users & Roles (Admin, Teacher, Student)
- Students (Demographics, Subject Marks, Computed Analytics, Attendance, Risk Tier)
- Teachers (Faculty profiles)
- Subjects (Curriculum course registry)
- AssessmentMarks (Historical assessment marks for progression trends)
- AttendanceRecords (Semester attendance logs)
- AIRecommendations (Persisted Gemini AI analysis)
- StudyPlans & StudyPlanItems (Personalized weekly actionable task checklists)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def compute_metrics(
    math: float,
    prog: float,
    ds: float,
    db: float,
    ml: float,
    attendance: float = 85.0
) -> Dict[str, Any]:
    """
    Computes academic metrics based on subject marks and attendance.
    
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
    - 3-Tier Risk Model:
        At Risk: Average < 50.0% OR >= 2 subjects < 40.0 OR Attendance < 65.0%
        Needs Attention: (50.0 <= Avg < 60.0) OR 1 subject < 40.0 OR (65.0 <= Attendance < 75.0)
        Good: Otherwise
    - needs_support: True if At Risk or Needs Attention (or avg < 50 or any subject < 40)
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

    subject_scores = [math, prog, ds, db, ml]
    failed_count = sum(1 for score in subject_scores if score < 40.0)

    # 3-Tier Multi-Factor Evaluation
    if avg < 50.0 or failed_count >= 2 or attendance < 65.0:
        risk_level = "At Risk"
    elif (50.0 <= avg < 60.0) or failed_count == 1 or (65.0 <= attendance < 75.0):
        risk_level = "Needs Attention"
    else:
        risk_level = "Good"

    # Backward compatibility with existing boolean needs_support
    needs_support = (avg < 50.0) or (failed_count > 0) or (attendance < 75.0)

    return {
        "total_marks": total,
        "average_marks": avg,
        "percentage": percentage,
        "grade": grade,
        "needs_support": needs_support,
        "risk_level": risk_level
    }


class User(Base):
    """
    User credentials and role-based access management.
    Roles: 'admin', 'teacher', 'student'.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="student", index=True, nullable=False)  # admin, teacher, student
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # One-to-one reverse associations
    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Teacher(Base):
    """Faculty profile linked to a user account."""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    teacher_id = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="teacher_profile")

    def __repr__(self) -> str:
        return f"<Teacher(teacher_id='{self.teacher_id}', name='{self.name}', dept='{self.department}')>"


class Subject(Base):
    """Academic curriculum subject registry."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    min_pass_marks = Column(Float, default=40.0, nullable=False)

    def __repr__(self) -> str:
        return f"<Subject(code='{self.code}', name='{self.name}')>"


class Student(Base):
    """
    SQLAlchemy model representing the 'students' table.
    Preserves all legacy fields for backward compatibility while extending with:
    - academic_year
    - attendance_percentage
    - risk_level ('Good', 'Needs Attention', 'At Risk')
    - user_id linking to authentication account
    - relationships to historical marks, attendance, AI recommendations, and study plans.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), index=True, nullable=False)
    department = Column(String(100), index=True, nullable=False)
    semester = Column(Integer, index=True, nullable=False)
    academic_year = Column(String(20), default="2024-2025", index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)

    # Core curriculum course marks (0.0 to 100.0)
    math_marks = Column(Float, nullable=False, default=0.0)
    programming_marks = Column(Float, nullable=False, default=0.0)
    data_structures_marks = Column(Float, nullable=False, default=0.0)
    database_marks = Column(Float, nullable=False, default=0.0)
    machine_learning_marks = Column(Float, nullable=False, default=0.0)

    # Attendance & Risk metrics
    attendance_percentage = Column(Float, nullable=False, default=85.0)
    risk_level = Column(String(20), nullable=False, default="Good", index=True)

    # Cached Computed Analytics
    total_marks = Column(Float, nullable=False, default=0.0)
    average_marks = Column(Float, nullable=False, default=0.0)
    percentage = Column(Float, nullable=False, default=0.0)
    grade = Column(String(5), nullable=False, default="F")
    needs_support = Column(Boolean, nullable=False, default=False)

    # User account relationship (optional link)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    user = relationship("User", back_populates="student_profile")

    # Audit Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # One-to-Many Relationships
    assessment_marks = relationship("AssessmentMark", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    ai_recommendations = relationship("AIRecommendation", back_populates="student", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="student", cascade="all, delete-orphan")

    def recalculate_metrics(self) -> None:
        """Recalculates cached metrics from marks and attendance."""
        metrics = compute_metrics(
            math=self.math_marks,
            prog=self.programming_marks,
            ds=self.data_structures_marks,
            db=self.database_marks,
            ml=self.machine_learning_marks,
            attendance=self.attendance_percentage
        )
        self.total_marks = metrics["total_marks"]
        self.average_marks = metrics["average_marks"]
        self.percentage = metrics["percentage"]
        self.grade = metrics["grade"]
        self.needs_support = metrics["needs_support"]
        self.risk_level = metrics["risk_level"]

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}', avg={self.average_marks}, risk={self.risk_level})>"


class AssessmentMark(Base):
    """Granular multi-semester or internal assessment marks for tracking progression trends."""
    __tablename__ = "assessment_marks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(30), ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False)
    subject_name = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    assessment_type = Column(String(50), nullable=False)  # "Internal 1", "Midterm", "End Semester"
    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Float, default=100.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="assessment_marks")


class AttendanceRecord(Base):
    """Detailed semester attendance ledger for student records."""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(30), ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False)
    semester = Column(Integer, nullable=False)
    total_classes = Column(Integer, default=100, nullable=False)
    attended_classes = Column(Integer, default=85, nullable=False)
    attendance_percentage = Column(Float, default=85.0, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="attendance_records")


class AIRecommendation(Base):
    """Persisted Gemini AI diagnostic summaries and learning recommendations."""
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(30), ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False)
    overall_summary = Column(Text, nullable=False)
    strong_subjects = Column(Text, nullable=False)  # JSON formatted or comma-separated
    weak_subjects = Column(Text, nullable=False)
    recommended_topics = Column(Text, nullable=False)
    actionable_plan = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="ai_recommendations")


class StudyPlan(Base):
    """Personalized weekly study roadmap generated for a student."""
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(30), ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False)
    week_number = Column(Integer, default=1, nullable=False)
    title = Column(String(200), nullable=False)
    focus_subject = Column(String(100), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # "active", "completed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="study_plans")
    items = relationship("StudyPlanItem", back_populates="study_plan", cascade="all, delete-orphan")


class StudyPlanItem(Base):
    """Actionable study task item with student completion state."""
    __tablename__ = "study_plan_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), index=True, nullable=False)
    day_of_week = Column(String(30), nullable=False)  # "Monday", "Day 1"
    topic = Column(String(200), nullable=False)
    activity = Column(String(500), nullable=False)
    estimated_minutes = Column(Integer, default=45, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    study_plan = relationship("StudyPlan", back_populates="items")
