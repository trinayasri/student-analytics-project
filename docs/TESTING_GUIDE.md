# Automated & Manual Testing Guide

## 1. Automated Testing Architecture

The test suite is built using **Pytest** and FastAPI's **TestClient** (backed by `httpx`). It runs tests against an isolated, high-speed, in-memory SQLite database (`sqlite:///:memory:`).

### Benefits of Our Test Setup:
- **No Test Pollution**: Production database (`student_analytics.db`) is never modified during tests.
- **Sub-Second Execution**: All 16 tests execute in under 1 second.
- **Repeatable & Deterministic**: Each test function receives a completely fresh schema via the `db_session` fixture.

---

## 2. Running Automated Tests

Open a terminal in the project root directory:

```powershell
# Navigate to project root
cd C:\Users\Trinayasri\.gemini\antigravity\scratch\student-performance-analytics

# Run entire test suite with verbose output
.\venv\Scripts\pytest -v

# Run with short test summary
.\venv\Scripts\pytest -q

# Run a specific test module
.\venv\Scripts\pytest tests/test_students_api.py -v
```

### Verified Test Suite Output:
```
tests/test_analytics_api.py::test_analytics_empty_database PASSED        [  6%]
tests/test_analytics_api.py::test_analytics_calculations_with_data PASSED [ 12%]
tests/test_crud.py::test_create_and_get_student PASSED                   [ 18%]
tests/test_crud.py::test_update_student_recalculates_metrics PASSED      [ 25%]
tests/test_crud.py::test_at_risk_threshold_detection PASSED              [ 31%]
tests/test_crud.py::test_delete_student PASSED                           [ 37%]
tests/test_crud.py::test_search_and_pagination PASSED                    [ 43%]
tests/test_students_api.py::test_create_student_success PASSED           [ 50%]
tests/test_students_api.py::test_create_student_validation_errors PASSED [ 56%]
tests/test_students_api.py::test_duplicate_student_id_conflict PASSED    [ 62%]
tests/test_students_api.py::test_duplicate_email_conflict PASSED         [ 68%]
tests/test_students_api.py::test_get_student_by_id_and_student_id PASSED [ 75%]
tests/test_students_api.py::test_get_nonexistent_student_404 PASSED      [ 81%]
tests/test_students_api.py::test_list_students_pagination_and_filtering PASSED [ 87%]
tests/test_students_api.py::test_update_student PASSED                   [ 93%]
tests/test_students_api.py::test_delete_student PASSED                   [100%]

======================== 16 passed in 0.82s ========================
```

---

## 3. Manual Verification Checklist

Follow this checklist to manually test and demonstrate each feature:

| # | Feature / Test Case | Manual Action to Perform | Expected Result | Verified? |
|---|---|---|---|---|
| 1 | **Backend Startup** | Run `.\venv\Scripts\uvicorn app.main:app --reload` | Terminal displays `Uvicorn running on http://127.0.0.1:8000` | [x] |
| 2 | **Swagger Docs** | Open `http://127.0.0.1:8000/docs` in browser | Interactive documentation renders with all endpoints | [x] |
| 3 | **Seed Data** | Run `.\venv\Scripts\python seed_data.py --reset` | 20 synthetic demo student records are inserted into SQLite | [x] |
| 4 | **Frontend Startup** | Run `.\venv\Scripts\streamlit run frontend/dashboard.py` | Browser opens `http://localhost:8501` showing Executive Dashboard | [x] |
| 5 | **Backend Health Indicator** | Inspect top-left of sidebar in Streamlit | Displays green badge: `● Backend Operational (FastAPI v1.0.0)` | [x] |
| 6 | **Add Student (Success)** | Go to "Manage Students" -> "Add New Student". Enter valid ID `STU3001`, marks: `80, 85, 90, 88, 92` | Success message displays with computed average `87.0%` (Grade: A) | [x] |
| 7 | **Validation: Marks Range** | Try adding a student with `math_marks = 120` or `-10` | Form rejected with clear validation error; no DB insertion | [x] |
| 8 | **Validation: Duplicate ID** | Try adding a student with existing ID `STU1001` | Error alert displays: `Student ID 'STU1001' already exists` | [x] |
| 9 | **Search by Name/ID** | In "Student Directory", type `Aarav` in the search bar | Table dynamically updates to show only Aarav Sharma's record | [x] |
| 10 | **Department Filter** | Filter by `Artificial Intelligence & Machine Learning` | Table shows only students from the AI & ML department | [x] |
| 11 | **Pagination** | Set rows per page to 10 and click `Next Page` | Table navigates smoothly to Page 2 of records | [x] |
| 12 | **Edit Student & Recalculate** | In "Manage Students" -> "Edit Student", load `STU1011`. Change failed score `38` to `85` | Student average updates and at-risk flag clears automatically | [x] |
| 13 | **At-Risk Early Warning** | Navigate to "Support & At-Risk Monitor" | Displays flagged students, highlighting specific failed courses | [x] |
| 14 | **Delete with Confirmation** | In "Manage Students" -> "Delete Student", enter ID, check confirmation box, click Delete | Record is deleted and subsequent lookup returns 404 | [x] |
| 15 | **Visual Analytics** | Open "Visual Analytics" tab | Plotly charts render: Department bars, Donut chart, Subject bars | [x] |
| 16 | **Backend Offline Handling** | Stop FastAPI (Ctrl+C). Refresh Streamlit. | Sidebar shows red badge `● Backend Offline` with start instructions | [x] |
