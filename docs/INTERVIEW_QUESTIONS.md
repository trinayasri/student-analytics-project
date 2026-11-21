# 🎓 Technical Interview Guide: AI-Powered Student Performance Analytics Platform

This guide provides in-depth, interview-ready answers to the most common architectural, software design, security, and AI engineering questions related to this project.

---

## 1. System Architecture & Backend Design

### Q1: Why did you decouple the Streamlit frontend from the FastAPI backend rather than writing all database logic directly in Streamlit?
**Answer**:
- **Separation of Concerns (SoC)**: Streamlit is designed strictly for reactive data presentation. Coupling database transactions or LLM calls directly inside Streamlit scripts causes redundant executions whenever a widget triggers a re-render.
- **Client Agnostic API**: By exposing standard RESTful endpoints, the backend can simultaneously support web dashboards, mobile applications, CLI administrative tools, and third-party Learning Management System (LMS) integrations via a single contract.
- **Scalability & Security**: Decoupling allows the FastAPI backend to run horizontally behind an API Gateway/Load Balancer, whereas database connection pooling, secrets management, and role-based token validation remain centralized and secure.

### Q2: Why choose FastAPI over Flask or Django for this platform?
**Answer**:
- **Native Asynchronous Support**: FastAPI is built on Starlette and Uvicorn, natively supporting Python `asyncio` for non-blocking I/O operations (such as streaming file uploads and asynchronous LLM network calls).
- **Automated Validation via Pydantic v2**: Eliminates manual request parsing by validating input bounds, emails, and data types before the route handler executes, returning standard HTTP 422 errors automatically.
- **Auto-Generated OpenAPI / Swagger Documentation**: Produces interactive documentation at `/docs` and `/redoc` directly from Python type annotations, saving significant development overhead.
- **Fast Execution**: Benchmarks consistently place FastAPI among the fastest Python web frameworks, approaching NodeJS and Go speeds for I/O-bound tasks.

---

## 2. Authentication, Security & Authorization (RBAC)

### Q3: Why use Bcrypt rather than standard SHA-256 for password hashing?
**Answer**:
- **Computationally Expensive by Design**: SHA-256 is an algorithm designed for rapid cryptographic hashing of files. High throughput makes SHA-256 vulnerable to modern GPU-based brute-force attacks capable of testing billions of hashes per second.
- **Salt Generation & Cost Factor**: Bcrypt incorporates a 128-bit salt automatically and uses an adaptive work factor (iteration rounds). As computing hardware advances, the cost factor can be increased to ensure stored hashes remain resilient against rainbow table and brute-force attacks.

### Q4: How does JWT authentication work in this platform, and what are its trade-offs?
**Answer**:
- **Mechanism**: Upon successful login (`/api/auth/login`), the server issues an encoded token containing standard claims (`sub` for username, `role`, `user_id`, `student_id`) and an expiration timestamp (`exp`), signed cryptographically with a secret key using the HMAC-SHA256 (`HS256`) algorithm.
- **Stateless Verification**: The backend verifies incoming requests using the `Authorization: Bearer <token>` header without querying a persistent session store (like Redis), minimizing database load.
- **Trade-Off**: Because JWTs are stateless, immediate revocation prior to expiration requires maintaining a token blacklist or shortening token TTLs (e.g. 15 minutes) and using refresh tokens.

### Q5: How is Student Record Isolation enforced at the API boundary?
**Answer**:
- The API implements a dependency `get_current_user_optional`.
- When an authenticated request arrives, the route handler inspects `current_user.role`. If `role == "student"`, the handler checks whether the requested `student_id` matches the caller's assigned ID.
- Any attempt to access, update, or delete another student's profile raises an immediate `HTTP 403 Forbidden` exception, preventing Insecure Direct Object Reference (IDOR) vulnerabilities.

---

## 3. Database Architecture & SQLAlchemy ORM

### Q6: How does your database schema transition between SQLite and PostgreSQL?
**Answer**:
- The SQLAlchemy engine is instantiated using a dynamic `DATABASE_URL` environment variable.
- For SQLite (development), connection arguments include `{"check_same_thread": False}` because FastAPI operates across multiple worker threads.
- For PostgreSQL (production), the connection string changes to `postgresql://user:pass@host:5432/dbname`, and connection pooling (`pool_size`, `max_overflow`) handles concurrent database requests efficiently without changing any application code.

### Q7: Why maintain both denormalized summary fields on `Student` and separate relational tables (`AssessmentMark`, `AttendanceRecord`)?
**Answer**:
- **Read-Heavy Dashboard Optimization**: Institutional executive dashboards frequently display average marks, grade distributions, and risk tiers for hundreds of students. Pre-computing and caching these values on the `Student` entity eliminates expensive multi-table `JOIN` and `AVG()` queries during every page refresh.
- **Longitudinal Depth**: Relational tables (`assessment_marks`, `attendance_records`, `study_plans`) store granular historical data points for progression trends, ensuring normalization and data integrity.

---

## 4. AI Engineering & Google Gemini Integration

### Q8: How do you prevent hallucination and format drift when integrating Gemini AI?
**Answer**:
- **Constrained Decoding**: We configure the Gemini API with `types.GenerateContentConfig(response_mime_type="application/json")` to enforce JSON grammar at the sampling level.
- **Schema Contracts**: Prompt templates define the exact required JSON structure.
- **Pydantic Validation**: The raw JSON string is validated against our Pydantic model (`AIPerformanceAnalysis`). If unexpected keys or malformed types are encountered, Pydantic raises a validation error, triggering fallback logic.

### Q9: Explain your AI Resilient Fallback Engine. Why is it essential for enterprise applications?
**Answer**:
- Cloud AI services can experience transient rate limits (HTTP 429), regional outages, or network latency.
- In educational environments, students and faculty cannot be blocked from accessing study roadmaps or performance insights due to third-party API issues.
- Our platform implements a **deterministic pedagogical diagnostic engine** that analyzes actual marks and syllabus mapping to generate score gaps, priority topics, and weekly study plans. This guarantees an uninterrupted 100% service SLA.

---

## 5. Statistical Algorithms & Data Ingestion

### Q10: How does your 3-Tier At-Risk Early Warning Engine calculate risk?
**Answer**:
The engine uses a 4-dimensional multi-factor scoring algorithm:
1. *Aggregate Average*: Fails below 50.0% (+40 risk points) or borderline 50–59.9% (+20 points).
2. *Individual Course Failures*: Scored $< 40.0\%$ adds +20 risk points per course and identifies course names.
3. *Attendance Deficits*: Critical attendance $< 65\%$ adds +35 points; warning attendance $< 75\%$ adds +15 points.
4. *Historical Assessment Trends*: Score drops $> 10\%$ across consecutive assessments add +15 points.
- **Tiers**: $\ge 45$ points $\rightarrow$ **At Risk**; $20–44$ points $\rightarrow$ **Needs Attention**; $< 20$ points $\rightarrow$ **Good Standing**.

### Q11: How do you compute the Pearson Correlation Coefficient ($r$) between attendance and marks?
**Answer**:
We calculate the covariance of attendance ($x$) and average marks ($y$) divided by the product of their standard deviations:
$$r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$
The service guards against division-by-zero (e.g. zero variance in attendance) and returns $0.0$ when sample size is insufficient ($n < 2$). An $r \ge 0.7$ signifies a strong positive correlation, validating institutional attendance requirements.

---

## 6. PDF Compilation & Memory Management

### Q12: Why compile PDFs in-memory using `io.BytesIO` instead of saving temporary files to disk?
**Answer**:
- **Concurrency & Race Conditions**: In multi-threaded environments, saving temporary files on disk requires unique naming schemes (`uuid`), locks, and cleanup routines.
- **Disk I/O Latency**: In-memory compilation avoids disk reads/writes, improving response times.
- **Leak Prevention**: Temporary disk files can accumulate if an unhandled exception occurs before deletion. `io.BytesIO` buffers are garbage-collected automatically once the HTTP response is completed.
