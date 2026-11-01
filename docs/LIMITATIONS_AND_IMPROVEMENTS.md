# Genuine Limitations & Future Architectural Enhancements

In technical interviews, senior interviewers appreciate engineers who demonstrate candid awareness of their system's boundaries and can articulate a realistic roadmap for production scaling.

---

## 1. Current System Limitations

### 1.1 Single-File Database Storage (SQLite)
- **Constraint**: SQLite operates on file-level locks during write transactions. While highly efficient for read-heavy local deployments, high-concurrency write workloads (hundreds of simultaneous writes) can result in `database is locked` operational timeouts.
- **Why It Was Chosen Here**: Zero installation friction, self-contained persistence, and optimal for beginner-friendly local execution and interview presentations.

### 1.2 Synchronous HTTP Communication in UI
- **Constraint**: The Streamlit frontend uses synchronous `requests` calls. If a network latency spike occurs between frontend and backend, the Streamlit UI thread blocks until the timeout expires.
- **Why It Was Chosen Here**: Clean, readable Python code suitable for beginners without complex async event-loop integration in Streamlit.

### 1.3 Absence of Role-Based Access Control (RBAC)
- **Constraint**: There is currently no authentication gateway. Any user with network access to the API can perform destructive operations (such as deleting a student record).
- **Scope Justification**: Keeps the codebase focused on core data modeling, analytics, and clean RESTful design without overwhelming authentication boilerplate.

---

## 2. Production Enhancement Roadmap

```mermaid
flowchart LR
    subgraph Current["Current State (Phase 1)"]
        StreamlitUI["Streamlit UI"]
        FastAPI_S["FastAPI (Single Process)"]
        SQLiteDB[("SQLite Database")]
    end

    subgraph Enterprise["Production Target (Phase 2)"]
        ReactUI["React / Next.js SPA"]
        Nginx["Nginx Reverse Proxy"]
        Gunicorn["Uvicorn Workers + Gunicorn"]
        Redis[("Redis Cache")]
        Postgres[("PostgreSQL Cluster")]
        CeleryWorker["Celery Background Worker"]
    end

    Current -.-> Enterprise
```

### 2.1 Database Migration to PostgreSQL
- **Upgrade**: Replace `sqlite:///./student_analytics.db` with `postgresql://user:pass@host:5432/university_db`.
- **Advantage**: Multi-version concurrency control (MVCC), row-level locking, and connection pooling via PgBouncer.
- **Effort**: Because our models use standard SQLAlchemy declarative syntax, migrating only requires changing the connection string and installing `psycopg2-binary`.

### 2.2 Security & Authentication (JWT + OAuth2)
- **Upgrade**: Integrate `fastapi.security.OAuth2PasswordBearer` and `python-jose` for JSON Web Tokens (JWT).
- **Role Hierarchy**:
  - `Dean / Administrator`: Full CRUD permissions, system configuration, and bulk student export.
  - `Department Faculty`: Grade update permissions restricted to their own department.
  - `Student`: Read-only access to their individual academic transcript.

### 2.3 Redis Analytical Caching
- **Upgrade**: Cache the results of `/api/analytics/summary` and `/api/analytics/departments` in an in-memory Redis key-value store with a 5-minute Time-To-Live (TTL).
- **Advantage**: Reduces database load by 90% during peak portal traffic (e.g., semester result announcements). Cache entries are automatically invalidated whenever a student record is inserted, updated, or deleted.

### 2.4 Asynchronous Background Worker (Celery + Redis)
- **Upgrade**: Offload bulk report generation, batch CSV imports, and automated email notifications for at-risk counseling to asynchronous Celery workers.
- **Advantage**: Prevents long-running jobs from blocking web server threads.

### 2.5 Containerization (Docker & Docker Compose)
- Create a `Dockerfile` for the FastAPI backend and a `Dockerfile` for the Streamlit frontend.
- Provide a `docker-compose.yml` orchestrating FastAPI, Streamlit, PostgreSQL, and Redis with a single command (`docker compose up --build`).
