# IBM Placement Interview Preparation: 42 Project Questions & Answers

This interview guide contains 42 real-world questions categorized by technical domain. Each answer is formulated to be concise, technically accurate, and easy to explain clearly to an interviewer.

---

## Category 1: System Design & Project Architecture

### Q1: Can you give a high-level summary of your project?
**Answer**: I built the **Student Performance Analytics System**, a decoupled web application designed to manage academic student records and provide real-time institutional performance analytics. The backend is built with FastAPI and SQLite using SQLAlchemy ORM, while the frontend is an interactive Streamlit dashboard featuring Plotly visualizations. It automatically computes GPA metrics, department benchmarks, grade distributions, and flags students needing academic intervention.

### Q2: Why did you choose a decoupled architecture instead of running Streamlit directly against SQLite?
**Answer**: Decoupling enforces separation of concerns. By placing FastAPI between the frontend and database, we guarantee security (no direct SQL access from the UI), reusability (the REST API can serve web, mobile, or external consumers), independent scalability, and a single source of truth for business and validation rules.

### Q3: What is the purpose of the `crud.py` file? Why not write database queries inside route handlers?
**Answer**: `crud.py` implements the Data Access / Repository pattern. Keeping database queries separate from route handlers keeps routes focused strictly on HTTP protocol concerns (headers, status codes, query parameters), prevents code duplication, and makes our unit tests much easier to write and maintain.

### Q4: How does your frontend communicate with the backend?
**Answer**: The Streamlit frontend uses the Python `requests` library to issue standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) with JSON payloads to the FastAPI REST API over port 8000.

### Q5: What is CORS, and why did you configure it in FastAPI?
**Answer**: Cross-Origin Resource Sharing (CORS) is a security mechanism enforced by HTTP clients when requests originate from a different port or domain. Since our Streamlit UI runs on port 8501 and FastAPI runs on port 8000, we added FastAPI's `CORSMiddleware` to permit cross-origin HTTP traffic.

### Q6: How does the application prevent SQL Injection?
**Answer**: We use SQLAlchemy ORM, which automatically parameterizes all queries. Instead of concatenating raw strings into SQL statements, parameters are passed as bound values, completely neutralizing SQL injection risks.

### Q7: What design patterns did you apply in this project?
**Answer**:
1. **Repository/Data Access Pattern** in `crud.py`.
2. **Dependency Injection Pattern** using FastAPI's `Depends(get_db)`.
3. **Data Transfer Object (DTO) Pattern** using Pydantic schemas.
4. **Context Manager Pattern** in `lifespan` and database session generator.

### Q8: How does the system automatically create database tables on startup?
**Answer**: In `app/main.py`, we define an `@asynccontextmanager` function called `lifespan`. Inside its startup section, `Base.metadata.create_all(bind=engine)` inspects all registered SQLAlchemy models and automatically creates missing tables in SQLite.

---

## Category 2: Python Language Fundamentals

### Q9: What are type hints in Python, and why did you use them?
**Answer**: Type hints (PEP 484) specify expected data types for function arguments and return values (e.g., `def get_student(id: int) -> Student:`). They make code self-documenting, catch bugs early in development, and allow Pydantic to enforce runtime data validation.

### Q10: What is the difference between `return` and `yield`?
**Answer**: `return` terminates a function and returns a single value to the caller. `yield` pauses function execution and produces a value, turning the function into a generator. When called again, execution resumes immediately after the `yield` statement.

### Q11: How did you use `yield` in `get_db()`?
**Answer**: In `app/database.py`, `get_db()` opens a database session, yields it to the route handler, and when the request finishes, resumes into the `finally:` block to execute `db.close()`, guaranteeing no database connections are leaked.

### Q12: What is a Python decorator, and where is it used in your code?
**Answer**: A decorator is a function that wraps another function to modify or extend its behavior without changing its source code. We use `@router.get()` for routing, `@field_validator()` in Pydantic for string sanitization, and `@pytest.fixture()` for test setup.

### Q13: What does the `**` unpacking operator do?
**Answer**: The `**` operator unpackages a dictionary into named keyword arguments. For example, `StudentCreate(**item)` converts key-value pairs in a dictionary into keyword arguments for the Pydantic schema constructor.

### Q14: What is the difference between a list comprehension and a traditional `for` loop?
**Answer**: A list comprehension provides a concise syntax for constructing a new list from an iterable (e.g., `[row.department for row in rows]`). In Python, list comprehensions are implemented in C under the hood, making them faster than repeated `.append()` calls in a standard loop.

### Q15: Why is `datetime.now(timezone.utc)` preferred over `datetime.utcnow()`?
**Answer**: `datetime.utcnow()` returns a naive datetime without explicit timezone metadata and is deprecated in Python 3.12+. `datetime.now(timezone.utc)` returns an unambiguous, timezone-aware datetime object conforming to modern standards.

### Q16: How does Python handle memory management for database connections?
**Answer**: Python uses reference counting and a cyclic garbage collector. However, external resources like database handles or file descriptors require explicit closing. We use `try...finally` in `get_db()` to ensure deterministic closing rather than relying on delayed garbage collection.

---

## Category 3: FastAPI & REST API Concepts

### Q17: What makes FastAPI different from Flask or Django?
**Answer**: FastAPI is built on Starlette and Pydantic. It provides automatic interactive Swagger documentation (`/docs`), native asynchronous request handling (`async`/`await`), automatic request parsing and type validation, and high performance comparable to Node.js and Go.

### Q18: What is Pydantic, and what role does it play in your project?
**Answer**: Pydantic is a data validation and settings management library. In our project, it parses incoming HTTP request JSON bodies into validated Python objects, validates data bounds (e.g., marks between 0 and 100), and serializes response data.

### Q19: What is the difference between status codes 400, 404, 409, and 422?
**Answer**:
- `400 Bad Request`: General client request syntax error.
- `404 Not Found`: The requested resource or student does not exist.
- `409 Conflict`: Business logic conflict, such as duplicate student ID or email.
- `422 Unprocessable Entity`: Semantic validation failure generated by Pydantic (e.g., negative score or invalid email).

### Q20: How does FastAPI generate Swagger UI documentation automatically?
**Answer**: FastAPI inspects route type annotations, query parameters, and Pydantic schemas to generate an OpenAPI-compliant JSON specification at `/openapi.json`. Swagger UI then renders this JSON interactively at `/docs`.

### Q21: What is Dependency Injection in FastAPI?
**Answer**: Dependency Injection is a mechanism where a component receives its required dependencies from an external provider rather than hardcoding their creation. In FastAPI, `Depends(get_db)` injects a database session into route parameters automatically.

### Q22: How is pagination implemented in your student listing endpoint?
**Answer**: The endpoint accepts `page` and `page_size` query parameters. We calculate `skip = (page - 1) * page_size`, execute `query.count()` for total records, and apply `.offset(skip).limit(page_size)` to fetch only the requested slice.

### Q23: How does your search filter work?
**Answer**: The search parameter takes a query string and applies an `or_` filter with SQL `ilike` on both the student's `name` and `student_id` columns, providing case-insensitive partial substring matching.

### Q24: What happens if a client submits a mark of 120?
**Answer**: Pydantic intercepts the payload because `Field(ge=0.0, le=100.0)` defines an upper bound of 100.0. It immediately halts execution and returns an HTTP `422 Unprocessable Entity` with a detailed error message without touching the database.

---

## Category 4: SQLAlchemy & Database Concepts

### Q25: What is an ORM, and what are its advantages?
**Answer**: An Object-Relational Mapper (ORM) translates database tables into Python classes and table rows into Python objects. It eliminates manual SQL authoring, reduces syntax errors, prevents SQL injection, and allows switching database backends with minimal code changes.

### Q26: What is the purpose of `Base = declarative_base()`?
**Answer**: `declarative_base()` is a factory function that produces a base class. When our `Student` model inherits from `Base`, SQLAlchemy's metaclass registers the class attributes with internal table metadata for cataloging and schema generation.

### Q27: Why did you add `connect_args={"check_same_thread": False}` to SQLite?
**Answer**: SQLite prevents connections created in one thread from being shared with another thread by default. FastAPI uses a multi-threaded worker pool to handle incoming requests concurrently. Disabling this check allows different request threads to safely access the shared SQLite database.

### Q28: What is the difference between `db.add()` and `db.commit()`?
**Answer**: `db.add(student)` places an object into the current session's pending transaction tracking list. `db.commit()` writes the pending transaction permanently to the database file on disk.

### Q29: What does `db.refresh(student)` do?
**Answer**: After a transaction is committed, `db.refresh()` queries SQLite to reload the model instance with database-generated attributes, such as the autoincremented primary key `id` and default timestamps.

### Q30: Why did you index columns like `student_id`, `name`, and `department`?
**Answer**: An index creates a B-Tree search structure in the database file. Instead of performing a slow full table scan ($O(N)$), the database engine finds matching records in $O(\log N)$ time, significantly speeding up search and filtering queries.

### Q31: How do you handle database sessions across concurrent requests?
**Answer**: `SessionLocal` generates an isolated session per HTTP request via `Depends(get_db)`. Each thread operates on its own session, preventing transaction conflicts between concurrent users.

### Q32: What is the difference between a primary key and a unique constraint?
**Answer**: A primary key uniquely identifies each row in a table and cannot contain null values. A unique constraint ensures that values in a specific column (like `student_id` or `email`) are unique across all rows. In our design, `id` is the primary key, while `student_id` and `email` have unique constraints.

---

## Category 5: Streamlit, Data Analytics & Plotly

### Q33: How does Streamlit handle application state across user interactions?
**Answer**: Streamlit reruns the Python script from top to bottom whenever a user interacts with a widget. To preserve variables across reruns (such as the current table page number), we store them in `st.session_state`.

### Q34: What is the advantage of Plotly over static libraries like Matplotlib?
**Answer**: Matplotlib generates static bitmap images. Plotly renders dynamic HTML5/WebGL vector charts that allow users to hover for tooltips, zoom, pan, toggle series, and download high-resolution exports directly in the browser.

### Q35: How does the system compute department-wise analytics?
**Answer**: We execute a SQL `GROUP BY department` query using SQLAlchemy's aggregation functions: `func.count()`, `func.avg()`, `func.max()`, and `func.min()`. The database engine aggregates the values directly and returns summarized rows.

### Q36: What is your criteria for flagging a student as "At-Risk"?
**Answer**: A student is flagged for academic support if their overall aggregate average is below **50.0%** (failing GPA) OR if they scored below **40.0%** in any individual course, ensuring students with localized subject difficulties are identified.

---

## Category 6: QA, Automated Testing & Edge Cases

### Q37: Why did you use an in-memory SQLite database for Pytest instead of the production file?
**Answer**: In `tests/conftest.py`, we use `sqlite:///:memory:` with `StaticPool`. This keeps tests completely isolated, runs them in RAM at sub-second speeds, and ensures test data never pollutes or alters the production database.

### Q38: How did you override the database dependency in your tests?
**Answer**: We used `app.dependency_overrides[get_db] = override_get_db`. This tells FastAPI to substitute the production database session with our in-memory test session whenever `Depends(get_db)` is invoked during test execution.

### Q39: What test cases did you write?
**Answer**: We wrote 16 automated test cases covering:
1. Student creation with valid and invalid data (negative marks, out-of-range semester, invalid email).
2. HTTP 409 conflict detection for duplicate roll IDs and emails.
3. Pagination, substring search, and department filtering.
4. Metric recalculation on mark updates.
5. Deletion and subsequent 404 verification.
6. Institutional summary KPIs, department aggregations, grade distributions, and empty database edge cases.

### Q40: What happens if the database is completely empty when the dashboard loads?
**Answer**: We implemented defensive zero-handling in `crud.py`. If `total_students == 0`, the summary endpoint returns 0 counts and 0.0 averages rather than throwing a division-by-zero exception, allowing the dashboard to render an empty state cleanly.

### Q41: How did you verify your code quality and reliability?
**Answer**: All 16 automated tests pass in `0.82 seconds` with zero application errors. We also verified Python module compilation with `py_compile` to eliminate syntax warnings.

### Q42: If you had another sprint, what would you improve next?
**Answer**: I would add JWT-based role authentication (Admin vs Faculty vs Student), integrate background asynchronous task processing (Celery/Redis) for automated PDF transcript generation, and containerize the entire stack using Docker and Docker Compose.
