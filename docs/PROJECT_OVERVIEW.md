# Project Overview: Student Performance Analytics System

## 1. Executive Summary & Problem Statement

In contemporary higher education institutions, monitoring student academic progress across diverse engineering departments is often fragmented. Traditional systems rely on static spreadsheets or disconnected university portals that fail to provide:
1. Real-time aggregated performance insights.
2. Cross-department comparative analytics.
3. Automated early-warning detection for students requiring academic counseling.

The **Student Performance Analytics System** solves this challenge by establishing an end-to-end, decoupled web application. It combines high-throughput RESTful backend APIs, persistent relational database storage with ACID guarantees, and an interactive analytical frontend dashboard.

---

## 2. Key Objectives

- **Centralized Academic Records**: Provide robust Create, Read, Update, and Delete (CRUD) operations for student demographics and course evaluations.
- **Automated Metric Computation**: Automatically calculate total marks, percentage, letter grades, and academic standing without manual intervention.
- **Data-Driven Institutional Governance**: Empower academic deans and department heads with interactive visual comparisons of department averages and grade distributions.
- **Early Intervention Alerting**: Instantly identify at-risk students who fall below institutional benchmarks to enable proactive tutoring and mentoring.
- **Production-Grade Separation of Concerns**: Enforce strict architectural boundaries between data persistence (SQLite/SQLAlchemy), API contract validation (FastAPI/Pydantic), and user experience (Streamlit/Plotly).

---

## 3. Core Functional Capabilities

### Student Management
- **Add Records**: Register student profiles with academic roll ID, full name, department, semester, email, and 5 subject scores.
- **Pagination & Browsing**: Browse large student rosters with configurable page limits.
- **Search & Filter**: Perform real-time case-insensitive search by student name or roll ID, alongside department and semester filters.
- **Update Records**: Edit student demographics or scores with automated recalculation of cached analytical metrics.
- **Delete Records**: Safe deletion of records with UI confirmation to prevent accidental loss.
- **Strict Data Validation**: Reject out-of-bounds marks ($<0$ or $>100$), invalid email formats, out-of-range semesters, and duplicate roll IDs or emails.

### Academic Analytics
- **Institutional KPIs**: College-wide enrollment, mean grade point average, pass rate, and at-risk count.
- **Department Benchmarking**: Aggregated department averages, enrollment distribution, and top/lowest marks per branch.
- **Grade Distribution**: Categorization across 6 letter grade tiers ($A+, A, B, C, D, F$).
- **Subject-Level Analysis**: Comparative mean, maximum, and minimum score distribution across each subject.
- **At-Risk Monitoring**: Dedicated view highlighting students with average marks $< 50\%$ or any individual subject $< 40\%$.

---

## 4. Current Limitations & Scope Boundaries

While engineered for high code quality and testability, the system has defined boundaries:
1. **Single-Tenant Database**: Uses SQLite for zero-configuration local deployment; distributed enterprise scaling would migrate to PostgreSQL.
2. **Synchronous HTTP Client**: The Streamlit frontend performs synchronous HTTP requests via Python `requests`; high-concurrency client architectures could employ asynchronous client pools (`httpx`).
3. **No Role-Based Access Control (RBAC)**: All authenticated or local network users currently have uniform read/write permissions. Production deployment would introduce JWT authentication and OAuth2 roles (e.g., Student vs Faculty vs Administrator).
