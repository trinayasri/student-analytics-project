"""
test_bulk_upload_and_filters.py - Tests for Academic Year, Risk Filters, CSV/Excel Ingestion, and RBAC Isolation
"""

import io
import pytest
import pandas as pd
from fastapi import status
from app.core.security import create_access_token


def test_filter_by_academic_year_and_risk(client):
    """Verifies filtering by academic_year and risk_level."""
    # Create students in different years and risk states
    s1 = {
        "student_id": "STU_AY_1",
        "name": "Student AY 2024",
        "department": "Computer Science",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "ay1@university.edu",
        "math_marks": 90.0,
        "programming_marks": 90.0,
        "data_structures_marks": 90.0,
        "database_marks": 90.0,
        "machine_learning_marks": 90.0,
        "attendance_percentage": 95.0
    }
    s2 = {
        "student_id": "STU_AY_2",
        "name": "Student AY 2023",
        "department": "Computer Science",
        "semester": 4,
        "academic_year": "2023-2024",
        "email": "ay2@university.edu",
        "math_marks": 35.0,  # Failed -> At Risk
        "programming_marks": 40.0,
        "data_structures_marks": 40.0,
        "database_marks": 40.0,
        "machine_learning_marks": 40.0,
        "attendance_percentage": 60.0
    }
    client.post("/api/students/", json=s1)
    client.post("/api/students/", json=s2)

    # Filter by 2023-2024
    res_year = client.get("/api/students/?academic_year=2023-2024")
    assert res_year.status_code == status.HTTP_200_OK
    items_year = res_year.json()["items"]
    assert len(items_year) == 1
    assert items_year[0]["student_id"] == "STU_AY_2"

    # Filter by risk_level
    res_risk = client.get("/api/students/?risk_level=At Risk")
    assert res_risk.status_code == status.HTTP_200_OK
    items_risk = res_risk.json()["items"]
    assert any(s["student_id"] == "STU_AY_2" for s in items_risk)


def test_get_academic_years_list(client):
    """Verifies that distinct academic years are listed."""
    s = {
        "student_id": "STU_YEAR_TEST",
        "name": "Year Tester",
        "department": "IT",
        "semester": 2,
        "academic_year": "2025-2026",
        "email": "yeartest@university.edu",
        "math_marks": 80.0,
        "programming_marks": 80.0,
        "data_structures_marks": 80.0,
        "database_marks": 80.0,
        "machine_learning_marks": 80.0,
        "attendance_percentage": 85.0
    }
    client.post("/api/students/", json=s)

    res = client.get("/api/students/academic-years")
    assert res.status_code == status.HTTP_200_OK
    years = res.json()
    assert "2025-2026" in years


def test_download_csv_template(client):
    """Verifies download of sample student CSV upload template."""
    res = client.get("/api/students/template/csv")
    assert res.status_code == status.HTTP_200_OK
    assert "text/csv" in res.headers["content-type"]
    assert "student_id,name,department" in res.text


def test_bulk_upload_csv_success(client):
    """Verifies successful batch creation of students from a CSV file."""
    csv_content = (
        "student_id,name,department,semester,academic_year,email,math_marks,programming_marks,data_structures_marks,database_marks,machine_learning_marks,attendance_percentage\n"
        "BULK101,Bulk Alpha,Data Science,3,2024-2025,bulk.alpha@test.edu,85,90,82,88,91,92.5\n"
        "BULK102,Bulk Beta,Data Science,3,2024-2025,bulk.beta@test.edu,75,80,72,78,81,85.0\n"
    )
    files = {"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/students/upload", files=files)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_records"] == 2
    assert data["created_records"] == 2
    assert data["skipped_records"] == 0
    assert len(data["errors"]) == 0

    # Verify presence in database
    chk = client.get("/api/students/BULK101")
    assert chk.status_code == status.HTTP_200_OK
    assert chk.json()["name"] == "Bulk Alpha"


def test_bulk_upload_excel_success(client):
    """Verifies successful batch creation from an Excel (.xlsx) file."""
    df = pd.DataFrame([
        {
            "student_id": "XLS201",
            "name": "Excel Student One",
            "department": "Artificial Intelligence",
            "semester": 5,
            "academic_year": "2024-2025",
            "email": "xls1@university.edu",
            "math_marks": 92.0,
            "programming_marks": 95.0,
            "data_structures_marks": 89.0,
            "database_marks": 91.0,
            "machine_learning_marks": 96.0,
            "attendance_percentage": 94.0
        }
    ])
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    files = {"file": ("students.xlsx", excel_buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/students/upload", files=files)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["created_records"] == 1
    assert data["skipped_records"] == 0

    chk = client.get("/api/students/XLS201")
    assert chk.status_code == status.HTTP_200_OK


def test_bulk_upload_with_duplicates_and_errors(client):
    """Verifies row-level validation and error logging for duplicate IDs and invalid scores."""
    # Pre-insert STU_EXIST
    client.post("/api/students/", json={
        "student_id": "STU_EXIST",
        "name": "Existing",
        "department": "IT",
        "semester": 2,
        "academic_year": "2024-2025",
        "email": "exist@test.edu",
        "math_marks": 80.0,
        "programming_marks": 80.0,
        "data_structures_marks": 80.0,
        "database_marks": 80.0,
        "machine_learning_marks": 80.0,
        "attendance_percentage": 85.0
    })

    csv_data = (
        "student_id,name,department,semester,academic_year,email,math_marks,programming_marks,data_structures_marks,database_marks,machine_learning_marks,attendance_percentage\n"
        "STU_EXIST,Duplicate DB,IT,2,2024-2025,diff@test.edu,80,80,80,80,80,85\n"
        "STU_BAD_MARK,Bad Mark Student,IT,2,2024-2025,badmark@test.edu,150,80,80,80,80,85\n"
        "STU_VALID_ROW,Valid Row Student,IT,2,2024-2025,validrow@test.edu,80,80,80,80,80,85\n"
    )
    files = {"file": ("mixed.csv", csv_data.encode("utf-8"), "text/csv")}
    res = client.post("/api/students/upload", files=files)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_records"] == 3
    assert data["created_records"] == 1
    assert data["skipped_records"] == 2
    assert len(data["errors"]) == 2


def test_student_role_authorization_isolation(client):
    """Verifies that a user with student role cannot access other students' records or mutate data."""
    # Create student record in DB
    client.post("/api/students/", json={
        "student_id": "STU_SELF",
        "name": "Self Student",
        "department": "CS",
        "semester": 1,
        "academic_year": "2024-2025",
        "email": "self@test.edu",
        "math_marks": 85.0,
        "programming_marks": 85.0,
        "data_structures_marks": 85.0,
        "database_marks": 85.0,
        "machine_learning_marks": 85.0,
        "attendance_percentage": 90.0
    })
    client.post("/api/students/", json={
        "student_id": "STU_OTHER",
        "name": "Other Student",
        "department": "CS",
        "semester": 1,
        "academic_year": "2024-2025",
        "email": "other@test.edu",
        "math_marks": 85.0,
        "programming_marks": 85.0,
        "data_structures_marks": 85.0,
        "database_marks": 85.0,
        "machine_learning_marks": 85.0,
        "attendance_percentage": 90.0
    })

    # Token for student STU_SELF
    student_token = create_access_token(
        data={"sub": "STU_SELF", "role": "student", "user_id": 999, "student_id": "STU_SELF"}
    )
    headers = {"Authorization": f"Bearer {student_token}"}

    # Student accessing self: OK (200)
    res_self = client.get("/api/students/STU_SELF", headers=headers)
    assert res_self.status_code == status.HTTP_200_OK

    # Student accessing someone else: 403 Forbidden
    res_other = client.get("/api/students/STU_OTHER", headers=headers)
    assert res_other.status_code == status.HTTP_403_FORBIDDEN
    assert "Students are restricted to accessing their own records" in res_other.json()["detail"]

    # Student attempting to delete: 403 Forbidden
    res_del = client.delete("/api/students/STU_SELF", headers=headers)
    assert res_del.status_code == status.HTTP_403_FORBIDDEN
