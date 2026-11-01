"""
schemas.py - Pydantic Request & Response Validation Schemas

Defines data validation models for API requests and response contracts.
Ensures strong typing, input sanitization, and automatic OpenAPI schema generation.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


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

    @field_validator("name", "student_id", "department")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Sanitizes string inputs by stripping unnecessary whitespace."""
        return v.strip()


class StudentCreate(StudentBase):
    """Schema for creating a new student record (all fields mandatory)."""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating an existing student (all fields optional for partial update)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    semester: Optional[int] = Field(None, ge=1, le=8)
    email: Optional[EmailStr] = None
    math_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    programming_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    data_structures_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    database_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    machine_learning_marks: Optional[float] = Field(None, ge=0.0, le=100.0)

    @field_validator("name", "department")
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


# --- Analytics Response Schemas ---

class AnalyticsSummary(BaseModel):
    """Overall academic summary statistics for the institution."""
    total_students: int
    overall_average: float
    highest_average: float
    lowest_average: float
    pass_percentage: float
    at_risk_count: int
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


class MessageResponse(BaseModel):
    """Standard success/information response envelope."""
    message: str
    detail: Optional[str] = None
