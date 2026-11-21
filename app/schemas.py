"""
schemas.py - Pydantic Request & Response Validation Schemas

Defines strongly typed schemas for:
- Authentication & User Management (JWT, Tokens, RBAC)
- Student CRUD (Demographics, Marks, Attendance, Risk Tiers)
- Bulk File Ingestion (CSV / Excel summaries)
- Assessment Marks & Attendance Records
- Institutional Performance Analytics & Comparisons
- AI Recommendations & Structured Gemini Diagnostics
- Weekly Study Plans & Task Completion Checklists
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


# --- Authentication & User Schemas ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique login username")
    email: EmailStr = Field(..., description="User email address")
    role: Literal["admin", "teacher", "student"] = Field(
        default="student",
        description="User access authorization role"
    )

    @field_validator("username")
    @classmethod
    def clean_username(cls, v: str) -> str:
        return v.strip().lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="Plaintext user password")


class UserLogin(BaseModel):
    username: str = Field(..., description="Login username or email")
    password: str = Field(..., description="Plaintext password")


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int
    student_id: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


# --- Student Management Schemas ---

class StudentBase(BaseModel):
    """Base fields shared across create, update, and response models."""
    student_id: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Unique student registration/roll identifier (e.g. STU1001)",
        examples=["STU1001"]
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the student",
        examples=["Aarav Sharma"]
    )
    department: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Academic department / branch",
        examples=["Artificial Intelligence & Machine Learning"]
    )
    semester: int = Field(
        ...,
        ge=1,
        le=8,
        description="Current semester number (1 to 8)",
        examples=[5]
    )
    academic_year: str = Field(
        default="2024-2025",
        min_length=4,
        max_length=20,
        description="Academic Year session (e.g. 2024-2025)",
        examples=["2024-2025"]
    )
    email: EmailStr = Field(
        ...,
        description="Valid student institutional or personal email address",
        examples=["aarav.sharma@example.edu"]
    )
    math_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Marks scored in Mathematics (0 - 100)",
        examples=[85.5]
    )
    programming_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Marks scored in Programming / Python (0 - 100)",
        examples=[92.0]
    )
    data_structures_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Marks scored in Data Structures (0 - 100)",
        examples=[78.0]
    )
    database_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Marks scored in Database Management Systems (0 - 100)",
        examples=[88.5]
    )
    machine_learning_marks: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Marks scored in Machine Learning (0 - 100)",
        examples=[91.0]
    )
    attendance_percentage: float = Field(
        default=85.0,
        ge=0.0,
        le=100.0,
        description="Attendance percentage rate (0 - 100%)",
        examples=[88.0]
    )

    @field_validator("name", "student_id", "department", "academic_year")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Sanitizes string inputs by stripping unnecessary whitespace."""
        return v.strip()


class StudentCreate(StudentBase):
    """Schema for creating a new student record."""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating an existing student (all fields optional for partial update)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    semester: Optional[int] = Field(None, ge=1, le=8)
    academic_year: Optional[str] = Field(None, min_length=4, max_length=20)
    email: Optional[EmailStr] = None
    math_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    programming_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    data_structures_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    database_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    machine_learning_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)

    @field_validator("name", "department", "academic_year")
    @classmethod
    def strip_optional_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v


class StudentResponse(StudentBase):
    """Schema returned to clients, including database ID and computed academic metrics."""
    id: int
    total_marks: float
    average_marks: float
    percentage: float
    grade: str
    needs_support: bool
    risk_level: str = "Good"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedStudentResponse(BaseModel):
    """Standardized response structure for paginated student lists."""
    items: List[StudentResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


# --- Bulk Data Ingestion Schemas ---

class BulkUploadResult(BaseModel):
    """Summary of bulk student data upload."""
    total_records: int
    created_records: int
    skipped_records: int
    errors: List[str] = []


# --- Assessment Marks & Attendance Schemas ---

class AssessmentMarkCreate(BaseModel):
    student_id: str
    subject_name: str
    semester: int
    assessment_type: str
    marks_obtained: float = Field(..., ge=0.0, le=100.0)
    max_marks: float = Field(default=100.0, ge=1.0)


class AssessmentMarkResponse(AssessmentMarkCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Analytics Response Schemas ---

class AnalyticsSummary(BaseModel):
    """Overall academic summary statistics for the institution."""
    total_students: int
    overall_average: float
    highest_average: float
    lowest_average: float
    pass_percentage: float
    at_risk_count: int
    needs_attention_count: int = 0
    good_standing_count: int = 0
    top_performer: Optional[StudentResponse] = None


class DepartmentAnalytics(BaseModel):
    """Aggregated academic metrics for a single academic department."""
    department: str
    student_count: int
    average_marks: float
    highest_marks: float
    lowest_marks: float


class GradeDistributionItem(BaseModel):
    """Count and percentage of students in each letter grade tier."""
    grade: str
    count: int
    percentage: float


class SubjectAverageItem(BaseModel):
    """Performance statistics for a specific academic subject."""
    subject: str
    average_score: float
    highest_score: float
    lowest_score: float


class StudentComparisonItem(BaseModel):
    """Comparison metrics for an individual student against cohort."""
    metric: str
    student_value: float
    class_average: float
    difference: float


class PerformanceTrendItem(BaseModel):
    """Semester or assessment progression data point."""
    period: str
    score: float
    subject: str


# --- AI Diagnostics & Study Plan Schemas ---

class WeakSubjectDetail(BaseModel):
    subject: str
    score: float
    gap: float
    priority_topics: List[str]


class AIPerformanceAnalysis(BaseModel):
    """Validated structured output from Gemini AI."""
    overall_summary: str
    strong_subjects: List[str]
    weak_subjects: List[WeakSubjectDetail]
    personalized_advice: str
    recommended_weekly_hours: int


class StudyPlanItemCreate(BaseModel):
    day_of_week: str
    topic: str
    activity: str
    estimated_minutes: int = 45


class StudyPlanItemResponse(StudyPlanItemCreate):
    id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class StudyPlanResponse(BaseModel):
    id: int
    student_id: str
    week_number: int
    title: str
    focus_subject: str
    status: str
    created_at: datetime
    items: List[StudyPlanItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Standard success/information response envelope."""
    message: str
    detail: Optional[str] = None


# --- Phase 3: Risk Assessment, Comparison, Trends, & Rankings Schemas ---

class RiskAssessmentResponse(BaseModel):
    student_id: str
    name: str
    department: str
    semester: int
    academic_year: str
    average_marks: float
    attendance_percentage: float
    category: str
    risk_score: float
    factors: List[str]
    recommendations: List[str]


class StudentComparisonRequest(BaseModel):
    student_ids: List[str] = Field(..., min_length=1, max_length=10)


class StudentComparisonResult(BaseModel):
    students: List[StudentResponse]
    comparison_table: List[Dict[str, Any]]
    benchmarks: Dict[str, float]


class BenchmarkVarianceItem(BaseModel):
    subject: str
    student_score: float
    department_average: float
    variance: float
    status: str


class StudentClassBenchmarkResponse(BaseModel):
    student: StudentResponse
    department: str
    college_average: float
    college_attendance: float
    breakdown: List[BenchmarkVarianceItem]


class SemesterTrendItem(BaseModel):
    semester: int
    semester_label: str
    student_count: int
    average_marks: float
    max_marks: float
    min_marks: float
    avg_attendance: float
    pass_percentage: float


class AttendanceTierItem(BaseModel):
    tier: str
    student_count: int
    average_marks: float
    pass_percentage: float


class AttendanceInsightResult(BaseModel):
    correlation_coefficient: float
    correlation_strength: str
    tiers: List[AttendanceTierItem]
    summary: str


class PerformersRankingResponse(BaseModel):
    highest_performers: List[StudentResponse]
    lowest_performers: List[StudentResponse]


# --- AI Analysis & Study Plan Execution Models ---

class FullAIAnalysisResponse(BaseModel):
    student_id: str
    name: str
    analysis: AIPerformanceAnalysis
    study_plan_id: Optional[int] = None
    study_plan_items_count: int = 0
    source: str  # "gemini_api" or "resilient_fallback"


class StudyPlanItemToggleResponse(BaseModel):
    item_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    plan_id: int
    completed_items_count: int
    total_items_count: int
    completion_percentage: float


class AIRecommendationHistoryItem(BaseModel):
    id: int
    student_id: str
    overall_summary: str
    strong_subjects: str
    weak_subjects: str
    recommended_topics: str
    actionable_plan: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


