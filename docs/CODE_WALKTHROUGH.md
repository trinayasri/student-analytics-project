# Comprehensive Code Walkthrough & Module Dictionary

This document explains every core file and function in the repository, explaining **what it does**, **how it works**, and **why it was designed this way**.

---

## 1. Directory Structure Map

```
student-performance-analytics/
├── app/
│   ├── database.py       # SQLite connection engine & session dependency
│   ├── models.py         # SQLAlchemy ORM entity models & metric calculations
│   ├── schemas.py        # Pydantic request & response validation contracts
│   ├── crud.py           # Pure database operations & SQL aggregation queries
│   ├── routes/
│   │   ├── students.py   # REST route handlers for student CRUD & search
│   │   └── analytics.py  # REST route handlers for institutional analytics
│   └── main.py           # FastAPI application root, CORS, & lifespan manager
├── frontend/
│   └── dashboard.py      # Streamlit multi-tab user interface & Plotly charts
├── tests/
│   ├── conftest.py       # Pytest in-memory database fixtures & TestClient
│   ├── test_crud.py      # Unit tests for database queries & calculations
│   ├── test_students_api.py # Integration tests for student API endpoints
│   └── test_analytics_api.py# Integration tests for analytics API endpoints
├── seed_data.py          # Synthetic demonstration data generator
└── requirements.txt      # Dependency specification
```

---

## 2. Module Breakdown

### 2.1 `app/database.py` (Database Engine & Session Management)

- **`create_engine(DATABASE_URL, connect_args={"check_same_thread": False})`**:
  - *Purpose*: Creates the low-level database engine interface to SQLite.
  - *Why*: SQLite restricts connections to the thread that created them by default. `check_same_thread=False` allows FastAPI's multi-threaded worker pool to share connections safely.
- **`SessionLocal = sessionmaker(...)`**:
  - *Purpose*: A factory for instantiating new database sessions.
  - *Why*: We set `autocommit=False` and `autoflush=False` to ensure all database transactions are explicit.
- **`Base = declarative_base()`**:
  - *Purpose*: The declarative base class that all ORM models inherit from.
- **`get_db()`**:
  - *Purpose*: A generator dependency providing a fresh session per request and closing it in a `finally:` block.
  - *Why*: Prevents connection leaks and guarantees connection closure even if request exceptions occur.

---

### 2.2 `app/models.py` (SQLAlchemy Entities & Business Rules)

- **`compute_metrics(math, prog, ds, db, ml)`**:
  - *Purpose*: A pure Python function that accepts 5 subject scores and calculates:
    - `total_marks`: Sum of scores (out of 500.0).
    - `average_marks` / `percentage`: Aggregate percentage.
    - `grade`: Letter tier ($A+ \ge 90, A \ge 80, B \ge 70, C \ge 60, D \ge 50, F < 50$).
    - `needs_support`: Boolean flag (`True` if average $< 50.0$ or any subject $< 40.0$).
  - *Why*: Centralizes calculation logic in one place, avoiding duplicated math across insert and update operations.
- **`Student(Base)` Model Class**:
  - *Purpose*: Maps the `students` table in SQLite to Python objects.
  - *Key Columns*: `id`, `student_id`, `name`, `department`, `semester`, `email`, 5 subject marks, 5 computed metric columns, and audit timestamps (`created_at`, `updated_at`).
- **`Student.recalculate_metrics()`**:
  - *Purpose*: Re-runs `compute_metrics` using the current subject attributes and updates the cached database columns.

---

### 2.3 `app/schemas.py` (Pydantic Request & Response Contracts)

- **`StudentBase`**:
  - *Purpose*: Defines shared student attributes (`student_id`, `name`, `department`, `semester`, `email`, subject scores) with Pydantic validation rules (`ge=0.0, le=100.0`, `EmailStr`).
  - *`@field_validator("name", ...)`*: Strips leading and trailing whitespace from string inputs.
- **`StudentCreate(StudentBase)`**:
  - *Purpose*: Request body schema for `POST /api/students/`. All fields are mandatory.
- **`StudentUpdate(BaseModel)`**:
  - *Purpose*: Request body schema for `PUT /api/students/{id}`. All fields are optional to support partial updates.
- **`StudentResponse(StudentBase)`**:
  - *Purpose*: Response model sent back to API clients. Includes database `id`, computed analytics, and audit timestamps.
  - *`model_config = ConfigDict(from_attributes=True)`*: Instructs Pydantic to read attributes directly from SQLAlchemy ORM instances.
- **`PaginatedStudentResponse`**:
  - *Purpose*: Standardized response envelope containing `items`, `total_count`, `page`, `page_size`, and `total_pages`.
- **`AnalyticsSummary`, `DepartmentAnalytics`, `GradeDistributionItem`, `SubjectAverageItem`**:
  - *Purpose*: Strongly typed response structures for analytical endpoints.

---

### 2.4 `app/crud.py` (Data Access Layer)

- **`get_student_by_id` & `get_student_by_student_id`**:
  - *Purpose*: Queries a single student using primary key or unique roll ID.
- **`get_students(db, skip, limit, search, department, semester)`**:
  - *Purpose*: Builds a dynamic SQLAlchemy query applying substring matching (`ilike`), department exact match, semester filter, and offset/limit pagination.
  - *Returns*: A tuple `(items, total_count)`.
- **`create_student(db, student_in)`**:
  - *Purpose*: Computes metrics, instantiates a `Student` ORM model, adds it to the session, commits the transaction, and returns the refreshed record.
- **`update_student(db, db_student, student_update)`**:
  - *Purpose*: Updates changed fields, checks if any subject marks changed, calls `recalculate_metrics()` if needed, and commits.
- **`delete_student(db, db_student)`**:
  - *Purpose*: Deletes the record and commits the transaction.
- **`get_overall_summary(db)`**:
  - *Purpose*: Queries aggregate counts, averages, and identifies the highest-performing student. Includes defensive fallbacks for empty databases.
- **`get_department_analytics(db)`**:
  - *Purpose*: Executes a SQL `GROUP BY department` aggregation.
- **`get_grade_distribution(db)`**:
  - *Purpose*: Tallies student counts across each grade tier.
- **`get_subject_averages(db)`**:
  - *Purpose*: Calculates mean, max, and min for each of the 5 subjects.
- **`get_at_risk_students(db)`**:
  - *Purpose*: Queries students where `needs_support == True`.

---

### 2.5 `app/routes/students.py` & `app/routes/analytics.py`

- **`_resolve_student(identifier, db)`**:
  - *Purpose*: Resolves a student parameter whether the user passed an integer ID (`21`) or an academic string ID (`STU1001`), returning a 404 error if not found.
- **Endpoints in `students.py`**:
  - `POST /`: Validates uniqueness of roll ID and email before calling `crud.create_student`, raising HTTP 409 Conflict if duplicates exist.
  - `GET /`: Handles pagination parameters and returns `PaginatedStudentResponse`.
  - `GET /{identifier}`: Returns a single student profile.
  - `PUT /{identifier}`: Updates student information.
  - `DELETE /{identifier}`: Deletes student record and returns a confirmation message.
- **Endpoints in `analytics.py`**:
  - Exposes `/summary`, `/departments`, `/grade-distribution`, `/subject-averages`, and `/at-risk`.

---

### 2.6 `app/main.py` (Application Entry Point)

- **`lifespan(app)`**:
  - *Purpose*: Context manager that automatically creates SQLite tables on application startup.
- **`CORSMiddleware`**:
  - *Purpose*: Configures allowable origins, methods, and headers so the Streamlit frontend can communicate cross-origin with FastAPI.
- **Router Mounting**:
  - Mounts `students.router` at `/api/students` and `analytics.router` at `/api/analytics`.
- **Health Checks**:
  - Exposes `GET /` and `GET /health` for service monitoring.

---

### 2.7 `frontend/dashboard.py` (Streamlit User Interface)

- **HTTP Client Helpers (`api_get`, `api_post`, `api_put`, `api_delete`)**:
  - *Purpose*: Wraps `requests` calls with error handling, converting network drops and HTTP error codes into clean UI messages.
- **Navigation Sidebar**:
  - Provides a real-time backend connection status badge and radio button navigation.
- **5 Application Views**:
  1. *Executive Dashboard*: Metric cards with college KPIs, top student card, and quick charts.
  2. *Student Directory*: Search bar, department dropdown, semester filter, data table with pagination, and single student deep dive.
  3. *Visual Analytics*: Plotly interactive charts for department benchmarks, grade distributions, and subject dynamics.
  4. *Support & At-Risk Monitor*: Alert table listing students needing academic support with exact failed course details and recommended actions.
  5. *Manage Students*: Forms for adding a new student, editing an existing student, and deleting a student with confirmation.
