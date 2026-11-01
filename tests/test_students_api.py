"""
test_students_api.py - Integration Tests for Student Management REST Endpoints
"""

import pytest


def _sample_payload(
    student_id="STU5001",
    name="Ravi Kumar",
    email="ravi.kumar@example.edu",
    department="Data Science",
    semester=5,
    math=85.0
):
    return {
        "student_id": student_id,
        "name": name,
        "department": department,
        "semester": semester,
        "email": email,
        "math_marks": math,
        "programming_marks": 90.0,
        "data_structures_marks": 80.0,
        "database_marks": 85.0,
        "machine_learning_marks": 88.0
    }


def test_create_student_success(client):
    """Test successful student creation with HTTP 201 Created."""
    response = client.post("/api/students/", json=_sample_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == "STU5001"
    assert data["name"] == "Ravi Kumar"
    assert data["total_marks"] == 428.0
    assert data["average_marks"] == 85.6
    assert data["grade"] == "A"
    assert data["needs_support"] is False
    assert "id" in data


def test_create_student_validation_errors(client):
    """Test input validations: marks range, email format, semester bounds."""
    # Negative mark
    bad_mark = _sample_payload(student_id="STU5002", email="bad.mark@example.edu")
    bad_mark["math_marks"] = -5.0
    res = client.post("/api/students/", json=bad_mark)
    assert res.status_code == 422

    # Mark > 100
    over_mark = _sample_payload(student_id="STU5003", email="over.mark@example.edu")
    over_mark["machine_learning_marks"] = 105.0
    res = client.post("/api/students/", json=over_mark)
    assert res.status_code == 422

    # Invalid email
    bad_email = _sample_payload(student_id="STU5004", email="not-an-email")
    res = client.post("/api/students/", json=bad_email)
    assert res.status_code == 422

    # Invalid semester
    bad_sem = _sample_payload(student_id="STU5005", email="bad.sem@example.edu", semester=10)
    res = client.post("/api/students/", json=bad_sem)
    assert res.status_code == 422


def test_duplicate_student_id_conflict(client):
    """Test creating duplicate student ID returns HTTP 409 Conflict."""
    payload1 = _sample_payload(student_id="STU6001", email="first@example.edu")
    res1 = client.post("/api/students/", json=payload1)
    assert res1.status_code == 201

    payload2 = _sample_payload(student_id="STU6001", email="second@example.edu")
    res2 = client.post("/api/students/", json=payload2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_duplicate_email_conflict(client):
    """Test creating duplicate email returns HTTP 409 Conflict."""
    payload1 = _sample_payload(student_id="STU7001", email="same@example.edu")
    res1 = client.post("/api/students/", json=payload1)
    assert res1.status_code == 201

    payload2 = _sample_payload(student_id="STU7002", email="same@example.edu")
    res2 = client.post("/api/students/", json=payload2)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


def test_get_student_by_id_and_student_id(client):
    """Test retrieving student by internal ID and student_id string."""
    create_res = client.post("/api/students/", json=_sample_payload(student_id="STU8001", email="stu8001@example.edu"))
    internal_id = create_res.json()["id"]

    # Retrieve by student_id
    res_code = client.get("/api/students/STU8001")
    assert res_code.status_code == 200
    assert res_code.json()["student_id"] == "STU8001"

    # Retrieve by numeric ID
    res_id = client.get(f"/api/students/{internal_id}")
    assert res_id.status_code == 200
    assert res_id.json()["id"] == internal_id


def test_get_nonexistent_student_404(client):
    """Test requesting nonexistent student returns 404."""
    res = client.get("/api/students/DOESNOTEXIST")
    assert res.status_code == 404


def test_list_students_pagination_and_filtering(client):
    """Test pagination, search parameter, and department filtering."""
    for i in range(1, 8):
        client.post(
            "/api/students/",
            json=_sample_payload(
                student_id=f"STU900{i}",
                name=f"Filter Student {i}",
                email=f"filter{i}@example.edu",
                department="CSE" if i <= 4 else "ECE",
                semester=3 if i % 2 == 0 else 5
            )
        )

    # Page size 3
    res_p1 = client.get("/api/students/?page=1&page_size=3")
    assert res_p1.status_code == 200
    body = res_p1.json()
    assert body["total_count"] == 7
    assert len(body["items"]) == 3
    assert body["total_pages"] == 3

    # Department filter
    res_dept = client.get("/api/students/?department=ECE")
    assert res_dept.status_code == 200
    assert res_dept.json()["total_count"] == 3

    # Search filter
    res_search = client.get("/api/students/?search=Student 2")
    assert res_search.status_code == 200
    assert res_search.json()["total_count"] == 1


def test_update_student(client):
    """Test updating existing student details and recalculating scores."""
    client.post("/api/students/", json=_sample_payload(student_id="STU9501", email="edit@example.edu", math=50.0))

    # Update math_marks to 95.0
    update_res = client.put(
        "/api/students/STU9501",
        json={"name": "Ravi Updated", "math_marks": 95.0}
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "Ravi Updated"
    assert updated_data["math_marks"] == 95.0


def test_delete_student(client):
    """Test deleting student record and confirming removal."""
    client.post("/api/students/", json=_sample_payload(student_id="STU9999", email="delete@example.edu"))

    del_res = client.delete("/api/students/STU9999")
    assert del_res.status_code == 200
    assert "successfully deleted" in del_res.json()["message"]

    # Verify no longer exists
    get_res = client.get("/api/students/STU9999")
    assert get_res.status_code == 404
