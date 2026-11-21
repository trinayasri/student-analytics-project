# 🏛️ System Architecture & Technical Specifications

## 1. Architectural Philosophy: Decoupled Multi-Tier Platform

The **AI-Powered Student Performance Analytics Platform** follows an industry-standard **N-Tier Decoupled Architecture**:

1. **Presentation Tier (Frontend)**: Streamlit interactive multi-role web platform utilizing Plotly for dynamic charts and WebSocket-backed session state management.
2. **API Gateway & Routing Tier (Backend REST API)**: FastAPI framework handling request routing, JWT validation, RBAC enforcement, and CORS policy management.
3. **Service & Intelligence Tier (Business Logic)**:
   - `Security Service`: Bcrypt password hashing & JWT token lifecycle management.
   - `3-Tier Risk Engine`: Multi-factor 4D academic risk evaluation.
   - `AI Diagnostic Service`: Google Gemini API client with Pydantic validation & deterministic fallback.
   - `Reporting Service`: In-memory ReportLab PDF compilation and CSV streaming.
4. **Data Persistence Tier (ORM & Database)**: Relational schema managed by SQLAlchemy ORM supporting both SQLite (development) and PostgreSQL (production).

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Port 8501)"]
        UI_A["Admin Portal"]
        UI_T["Teacher Portal"]
        UI_S["Student Portal"]
        State["Session State (JWT Bearer Token)"]
    end

    subgraph API["FastAPI Gateway & Route Handlers (Port 8000)"]
        RouterAuth["Auth Router (/api/auth)"]
        RouterStu["Students Router (/api/students)"]
        RouterAn["Analytics Router (/api/analytics)"]
        RouterAI["AI Diagnostics (/api/ai)"]
        RouterPlan["Study Plans (/api/study-plans)"]
        RouterRep["Reports (/api/reports)"]
    end

    subgraph Services["Application Services"]
        SvcSec["Security & Token Service"]
        SvcRisk["3-Tier At-Risk Engine"]
        SvcAI["Gemini AI & Fallback Service"]
        SvcRep["ReportLab PDF & CSV Generator"]
    end

    subgraph Data["Persistence Layer"]
        ORM["SQLAlchemy ORM (models.py)"]
        DB[("Relational Database: SQLite / PostgreSQL")]
    end

    UI_A & UI_T & UI_S --> State
    State -- "HTTP REST + Bearer JWT" --> API
    RouterAuth --> SvcSec
    RouterStu --> SvcSec
    RouterAn --> SvcRisk
    RouterAI --> SvcAI
    RouterPlan --> SvcAI
    RouterRep --> SvcRep
    Services --> ORM
    ORM --> DB
    SvcAI -.->|JSON API Request| Gemini["Google Gemini API Cloud"]
```

---

## 2. Technical Sequence Workflows

### Workflow A: Role-Based Authentication & Self-Access Isolation

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student User
    participant Streamlit as Streamlit Frontend (:8501)
    participant FastAPI as FastAPI Backend (:8000)
    participant Security as Security Service (Bcrypt/JWT)
    participant DB as Relational Database

    Student->>Streamlit: Enters credentials (username, password)
    Streamlit->>FastAPI: POST /api/auth/login {username, password}
    FastAPI->>DB: Query User by username
    DB-->>FastAPI: Returns User (hashed_password, role="student")
    FastAPI->>Security: verify_password(plain, hashed)
    Security-->>FastAPI: Password valid
    FastAPI->>Security: create_access_token(sub, role, student_id)
    Security-->>FastAPI: Signed JWT Token
    FastAPI-->>Streamlit: 200 OK {access_token, role: "student"}
    Streamlit->>Streamlit: Stores token in st.session_state

    Note over Student,FastAPI: Student requests another student's report card
    Student->>Streamlit: Requests /api/reports/student/STU_OTHER/pdf
    Streamlit->>FastAPI: GET /api/reports/student/STU_OTHER/pdf (Bearer Token)
    FastAPI->>FastAPI: Extract claims: role="student", allowed_id="STU_SELF"
    FastAPI-->>Streamlit: 403 Forbidden ("Students restricted to own records")
    Streamlit-->>Student: Displays Access Denied notification
```

---

### Workflow B: Gemini AI Diagnosis with Resilient Fallback

```mermaid
sequenceDiagram
    autonumber
    actor User as Teacher / Student
    participant FastAPI as FastAPI Backend (:8000)
    participant AISvc as AI Service (ai_service.py)
    participant Gemini as Google Gemini API Cloud
    participant Fallback as Pedagogical Fallback Engine
    participant DB as Relational Database

    User->>FastAPI: POST /api/ai/analyze/{student_id}
    FastAPI->>DB: Fetch Student demographics, marks & attendance
    DB-->>FastAPI: Student profile (Math: 36, DBMS: 45, Avg: 64.8%)
    FastAPI->>AISvc: generate_and_save_ai_analysis(db, student)

    alt Gemini API Key Available & Online
        AISvc->>Gemini: POST generateContent (Prompt + JSON Schema)
        Gemini-->>AISvc: Raw JSON {overall_summary, weak_subjects, study_plan}
        AISvc->>AISvc: Validate schema via Pydantic AIPerformanceAnalysis
    else Gemini Offline / Timeout / No Key
        AISvc->>Fallback: Trigger deterministic pedagogical analysis
        Fallback->>Fallback: Compute score gaps (75 - score) & syllabus mapping
        Fallback-->>AISvc: Structured AIPerformanceAnalysis & 5-day study plan
    end

    AISvc->>DB: INSERT INTO ai_recommendations (summary, weak_subjects, ...)
    AISvc->>DB: INSERT INTO study_plans & study_plan_items
    DB-->>AISvc: Plan created with ID
    AISvc-->>FastAPI: FullAIAnalysisResponse (source: gemini_api | resilient_fallback)
    FastAPI-->>User: 200 OK with diagnostic summary & weekly task roadmap
```

---

### Workflow C: In-Memory PDF Streaming Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Faculty
    participant FastAPI as FastAPI Backend (:8000)
    participant ReportSvc as ReportLab Engine
    participant Mem as In-Memory BytesIO Buffer

    User->>FastAPI: GET /api/reports/student/STU1001/pdf
    FastAPI->>ReportSvc: generate_student_pdf_report(student, db)
    ReportSvc->>Mem: Instantiate io.BytesIO()
    ReportSvc->>Mem: Compile SimpleDocTemplate with Tables, Colors & Flowables
    ReportSvc->>Mem: Seek buffer to offset 0
    Mem-->>ReportSvc: Return buffer.getvalue() (Raw binary bytes)
    ReportSvc-->>FastAPI: bytes (starts with %PDF)
    FastAPI-->>User: 200 OK (Content-Type: application/pdf, Content-Disposition: attachment)
    Note over User,Mem: Zero temporary files written to server disk
```
