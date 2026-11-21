"""
dashboard.py - Streamlit Interactive Multi-Role Analytics & AI Platform

Features:
- Role-Based Authentication: Admin, Teacher, and Student views with JWT session handling.
- Quick-Demo login presets for instant interview demonstrations.
- Admin View: Full institutional KPIs, CSV/Excel drag-and-drop ingestion, user metrics, and management.
- Teacher View: Cohort progression, 3-tier at-risk early warnings, comparative benchmarks, and batch exports.
- Student View: Personal report card, subject breakdown vs class average, on-demand Gemini AI diagnosis,
  interactive weekly study plan checklist with live progress tracking, and official PDF download.
"""

import os
import io
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure Backend API endpoint from environment or default local port
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Student Performance Analytics Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling cards, metric highlights, and badges
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-top: 4px;
        color: #38bdf8;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 2px;
    }
    .badge-good {
        background-color: #065f46;
        color: #6ee7b7;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-attention {
        background-color: #78350f;
        color: #fde68a;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-risk {
        background-color: #991b1b;
        color: #fca5a5;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .ai-box {
        background: #0f172a;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# --- HTTP Client API Helpers with Auth Bearer ---

def get_auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(endpoint: str, params: dict = None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable. Please ensure FastAPI is running on port 8000."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, json_data: dict = None, files: dict = None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=json_data, files=files, headers=get_auth_headers(), timeout=15)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def api_put(endpoint: str, json_data: dict):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.put(url, json=json_data, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def api_patch(endpoint: str, json_data: dict = None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.patch(url, json=json_data, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def api_delete(endpoint: str):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.delete(url, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


def download_file(endpoint: str):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        res = requests.get(url, headers=get_auth_headers(), timeout=15)
        res.raise_for_status()
        return res.content, None
    except Exception as e:
        return None, str(e)


# --- Session State Initialization ---

if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None
if "curr_page" not in st.session_state:
    st.session_state["curr_page"] = 1


# --- Authentication Functions ---

def login(username, password):
    res, err = api_post("/api/auth/login", json_data={"username": username, "password": password})
    if err:
        st.error(f"Login failed: {err}")
    elif res:
        st.session_state["token"] = res["access_token"]
        st.session_state["user_info"] = {
            "username": res["username"],
            "role": res["role"],
            "user_id": res["user_id"],
            "student_id": res.get("student_id")
        }
        st.success(f"Welcome back, {res['username']} ({res['role'].upper()})!")
        st.rerun()


def logout():
    st.session_state["token"] = None
    st.session_state["user_info"] = None
    st.rerun()


# --- View Renderers ---

def render_login_view():
    st.title("🎓 Student Performance Analytics & Recommendation Platform")
    st.markdown("Enterprise AI-Powered Academic Evaluation, Early Warning & Study Planning System.")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("🔐 Secure Sign In")
        with st.form("login_form"):
            user_input = st.text_input("Username or Email", placeholder="e.g. admin or aarav.sharma@example.edu")
            pass_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In to Platform", use_container_width=True)
            if submitted:
                if not user_input.strip() or not pass_input.strip():
                    st.warning("Please enter both username and password.")
                else:
                    login(user_input.strip(), pass_input.strip())

        st.markdown("---")
        st.subheader("⚡ Quick Demo Access (1-Click Login)")
        st.caption("Use these pre-seeded roles to explore the application during technical evaluations:")

        demo_c1, demo_c2, demo_c3 = st.columns(3)
        with demo_c1:
            if st.button("🔑 Demo Admin", use_container_width=True):
                login("admin", "Admin@123")
        with demo_c2:
            if st.button("👩‍🏫 Demo Teacher", use_container_width=True):
                login("teacher", "Teacher@123")
        with demo_c3:
            if st.button("👨‍🎓 Demo Student (Aarav)", use_container_width=True):
                login("student", "Student@123")

    with col2:
        st.info(
            "### 🌟 Platform Capabilities\n\n"
            "- **Multi-Factor At-Risk Engine**: 4-dimensional detection evaluating aggregate %, subject failures, attendance rate, and longitudinal assessment trends.\n"
            "- **Google Gemini AI Integration**: Automated weak-topic diagnosis, score gap calculation, and weekly study plans with deterministic fallback.\n"
            "- **Automated Reporting**: Instant pixel-perfect ReportLab PDF report cards and CSV exports.\n"
            "- **Bulk Data Ingestion**: Seamless CSV & Excel spreadsheet imports with row-level validation."
        )


def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=56)
        st.title("Academic Analytics")

        user = st.session_state.get("user_info")
        role = user["role"] if user else "guest"
        role_colors = {"admin": "#dc2626", "teacher": "#2563eb", "student": "#059669"}

        st.markdown(
            f"👤 **Logged in as:** `{user['username']}`<br/>"
            f"<span style='background-color: {role_colors.get(role, '#64748b')}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;'>ROLE: {role.upper()}</span>",
            unsafe_allow_html=True
        )

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.markdown("---")

        # Role-based menu items
        if role == "admin":
            menu_options = [
                "📊 Executive Overview",
                "📋 Student Directory",
                "📥 Bulk Data Ingestion",
                "⚠️ At-Risk & Support Monitor",
                "📈 Advanced Visual Analytics",
                "⚙️ Manage Student Records",
                "📑 Institutional Reports"
            ]
        elif role == "teacher":
            menu_options = [
                "📊 Cohort Performance",
                "📋 Student Explorer",
                "⚠️ 3-Tier Risk Intervention",
                "📈 Comparative Analytics",
                "⚙️ Record Management",
                "📑 Export Reports"
            ]
        else:  # Student
            menu_options = [
                "🎓 My Academic Profile",
                "📊 Performance Breakdown",
                "🤖 AI Performance Diagnosis",
                "📝 My Weekly Study Plan",
                "📄 Download PDF Report Card"
            ]

        selected_menu = st.radio("Navigation Menu", menu_options)
        st.markdown("---")
        st.caption("🚀 AI Platform v2.0 • FastAPI & Gemini")
        return selected_menu


# --- Tab Renderers ---

def render_executive_overview():
    st.title("🏛️ Institutional Executive Overview")
    st.markdown("College-wide academic performance indicators, risk categories, and enrollment distribution.")

    summary, err = api_get("/api/analytics/summary")
    if err:
        st.error(f"Failed to load analytics: {err}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Enrollment</div>
            <div class="metric-value">{summary['total_students']}</div>
            <div class="metric-sub">Active registered students</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">College Average</div>
            <div class="metric-value">{summary['overall_average']}%</div>
            <div class="metric-sub">Across all courses & batches</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pass Percentage</div>
            <div class="metric-value">{summary['pass_percentage']}%</div>
            <div class="metric-sub">Threshold &ge; 50%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">At-Risk Students</div>
            <div class="metric-value" style="color: #ef4444">{summary['at_risk_count']}</div>
            <div class="metric-sub">{summary.get('needs_attention_count', 0)} in Needs Attention tier</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if summary.get("top_performer"):
        top = summary["top_performer"]
        st.success(
            f"🏆 **Top Institutional Performer**: **{top['name']}** ({top['student_id']}) — "
            f"**{top['average_marks']}%** (Grade: **{top['grade']}**) | Department: *{top['department']}*"
        )

    # Charts Row
    c1, c2 = st.columns(2)
    with c1:
        grades_data, _ = api_get("/api/analytics/grade-distribution")
        if grades_data:
            df_g = pd.DataFrame(grades_data)
            fig_g = px.bar(
                df_g, x="grade", y="count", text="percentage",
                title="Student Grade Distribution",
                labels={"grade": "Letter Grade", "count": "Students", "percentage": "%"},
                color="grade",
                color_discrete_map={"A+": "#10b981", "A": "#3b82f6", "B": "#6366f1", "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"}
            )
            fig_g.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_g.update_layout(height=340, showlegend=False)
            st.plotly_chart(fig_g, use_container_width=True)

    with c2:
        depts_data, _ = api_get("/api/analytics/departments")
        if depts_data:
            df_d = pd.DataFrame(depts_data)
            fig_d = px.pie(
                df_d, names="department", values="student_count",
                title="Department Enrollment Distribution",
                hole=0.45, color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_d.update_layout(height=340)
            st.plotly_chart(fig_d, use_container_width=True)


def render_student_directory(read_only=False):
    st.title("📋 Student Directory & Profiles Explorer")
    st.markdown("Search, filter by academic year and risk category, and inspect detailed profiles.")

    depts_list, _ = api_get("/api/students/departments") or ([], None)
    years_list, _ = api_get("/api/students/academic-years") or ([], None)

    # Filter Bar
    with st.expander("🔍 Search and Filter Options", expanded=True):
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([2, 2, 1, 1, 1])
        with fcol1:
            search_query = st.text_input("Search Name or Student ID", placeholder="e.g. STU1001 or Priya")
        with fcol2:
            selected_dept = st.selectbox("Department", ["All Departments"] + (depts_list or []))
        with fcol3:
            selected_sem = st.selectbox("Semester", ["All", 1, 2, 3, 4, 5, 6, 7, 8])
        with fcol4:
            selected_year = st.selectbox("Academic Year", ["All Years"] + (years_list or []))
        with fcol5:
            selected_risk = st.selectbox("Risk Level", ["All Tiers", "Good", "Needs Attention", "At Risk"])

    params = {"page": st.session_state["curr_page"], "page_size": 10}
    if search_query.strip(): params["search"] = search_query.strip()
    if selected_dept != "All Departments": params["department"] = selected_dept
    if selected_sem != "All": params["semester"] = int(selected_sem)
    if selected_year != "All Years": params["academic_year"] = selected_year
    if selected_risk != "All Tiers": params["risk_level"] = selected_risk

    resp, err = api_get("/api/students/", params=params)
    if err:
        st.error(f"Error: {err}")
        return

    students = resp.get("items", [])
    total_count = resp.get("total_count", 0)
    total_pages = resp.get("total_pages", 1)

    st.markdown(f"**Found {total_count} student records** (Page {st.session_state['curr_page']} of {max(total_pages, 1)})")

    if students:
        display_data = []
        for s in students:
            display_data.append({
                "Student ID": s["student_id"],
                "Full Name": s["name"],
                "Department": s["department"],
                "Sem": s["semester"],
                "Year": s["academic_year"],
                "Attendance": f"{s['attendance_percentage']}%",
                "Average %": f"{s['average_marks']}%",
                "Grade": s["grade"],
                "Risk Tier": s["risk_level"]
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("⬅️ Previous", disabled=(st.session_state["curr_page"] <= 1)):
                st.session_state["curr_page"] -= 1
                st.rerun()
        with pcol3:
            if st.button("Next ➡️", disabled=(st.session_state["curr_page"] >= total_pages)):
                st.session_state["curr_page"] += 1
                st.rerun()

        # Detailed Deep Dive Box
        st.markdown("---")
        st.subheader("🔎 Individual Profile Deep Dive")
        selected_id = st.selectbox("Select student to inspect:", [f"{s['student_id']} - {s['name']}" for s in students])

        if selected_id:
            stu_id = selected_id.split(" - ")[0]
            target = next((s for s in students if s["student_id"] == stu_id), None)
            if target:
                dcol1, dcol2 = st.columns([1, 1])
                with dcol1:
                    st.write(f"**ID:** `{target['student_id']}` | **Name:** {target['name']}")
                    st.write(f"**Email:** {target['email']}")
                    st.write(f"**Department:** {target['department']} (Sem {target['semester']}, {target['academic_year']})")
                    st.write(f"**Cumulative Average:** `{target['average_marks']}%` | **Letter Grade:** `{target['grade']}`")
                    st.write(f"**Attendance Rate:** `{target['attendance_percentage']}%`")

                    # Download PDF Button
                    pdf_bytes, pdf_err = download_file(f"/api/reports/student/{target['student_id']}/pdf")
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Download Official PDF Report Card",
                            data=pdf_bytes,
                            file_name=f"{target['student_id']}_report_card.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                with dcol2:
                    sub_scores = {
                        "Math": target["math_marks"],
                        "Python": target["programming_marks"],
                        "DSA": target["data_structures_marks"],
                        "DBMS": target["database_marks"],
                        "ML": target["machine_learning_marks"]
                    }
                    fig = px.bar(
                        x=list(sub_scores.keys()), y=list(sub_scores.values()),
                        labels={"x": "Subject", "y": "Marks (0-100)"},
                        title=f"Course Scores: {target['name']}",
                        text=list(sub_scores.values()),
                        color=list(sub_scores.values()),
                        color_continuous_scale="Teal"
                    )
                    fig.update_yaxes(range=[0, 100])
                    fig.update_layout(height=260, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)


def render_bulk_ingestion():
    st.title("📥 Bulk Student Data Ingestion")
    st.markdown("Import student records in bulk via **CSV** or **Excel (.xlsx, .xls)** spreadsheets.")

    bcol1, bcol2 = st.columns([2, 1])
    with bcol2:
        st.subheader("📑 Template")
        st.info("Download our pre-formatted CSV template containing required column headers and sample data.")
        csv_template_bytes, _ = download_file("/api/students/template/csv")
        if csv_template_bytes:
            st.download_button(
                label="⬇️ Download Sample CSV Template",
                data=csv_template_bytes,
                file_name="student_upload_template.csv",
                mime="text/csv",
                use_container_width=True
            )

    with bcol1:
        st.subheader("📤 Upload Dataset")
        uploaded_file = st.file_uploader(
            "Drag and drop your CSV or Excel file here:",
            type=["csv", "xlsx", "xls"]
        )

        if uploaded_file is not None:
            st.write(f"**File Selected:** `{uploaded_file.name}` ({round(uploaded_file.size / 1024, 1)} KB)")
            if st.button("🚀 Process & Ingest File", type="primary", use_container_width=True):
                with st.spinner("Validating and importing student records..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    result, err = api_post("/api/students/upload", files=files)

                if err:
                    st.error(f"Upload failed: {err}")
                elif result:
                    st.success(f"🎉 Import Completed! Successfully created **{result['created_records']}** records out of {result['total_records']}.")
                    if result["skipped_records"] > 0:
                        st.warning(f"⚠️ **{result['skipped_records']} records skipped** due to validation errors or duplicates.")
                        with st.expander("Inspect Ingestion Warnings / Errors"):
                            for err_msg in result["errors"]:
                                st.write(f"- {err_msg}")


def render_at_risk_monitor():
    st.title("⚠️ Academic Support & 3-Tier Early Warning System")
    st.markdown(
        "Identifies students requiring academic counseling based on **aggregate marks**, **subject failures**, **attendance deficits**, and **performance trends**."
    )

    t1, t2 = st.columns([3, 1])
    with t2:
        pdf_at_risk, _ = download_file("/api/reports/at-risk/pdf")
        if pdf_at_risk:
            st.download_button(
                label="📄 Export At-Risk PDF Dossier",
                data=pdf_at_risk,
                file_name="institutional_at_risk_dossier.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    evaluations, err = api_get("/api/analytics/risk-evaluations")
    if err:
        st.error(err)
        return

    # Count by category
    at_risk_list = [e for e in evaluations if e["category"] == "At Risk"]
    attention_list = [e for e in evaluations if e["category"] == "Needs Attention"]
    good_list = [e for e in evaluations if e["category"] == "Good"]

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #ef4444;">
            <div class="metric-label">High Priority: At Risk</div>
            <div class="metric-value" style="color: #ef4444">{len(at_risk_list)}</div>
            <div class="metric-sub">Immediate faculty advisement needed</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #f59e0b;">
            <div class="metric-label">Moderate: Needs Attention</div>
            <div class="metric-value" style="color: #f59e0b">{len(attention_list)}</div>
            <div class="metric-sub">Borderline scores or attendance warnings</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #10b981;">
            <div class="metric-label">Good Academic Standing</div>
            <div class="metric-value" style="color: #10b981">{len(good_list)}</div>
            <div class="metric-sub">Satisfying all academic requirements</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    selected_tier = st.radio("Filter Tier:", ["All Tiers", "🚨 At Risk Only", "⚠️ Needs Attention Only"], horizontal=True)

    display_evals = evaluations
    if selected_tier == "🚨 At Risk Only":
        display_evals = at_risk_list
    elif selected_tier == "⚠️ Needs Attention Only":
        display_evals = attention_list

    for student in display_evals:
        badge_class = "badge-risk" if student["category"] == "At Risk" else ("badge-attention" if student["category"] == "Needs Attention" else "badge-good")
        with st.expander(f"{student['student_id']} - {student['name']} ({student['department']}) — Tier: {student['category']} (Risk Score: {student['risk_score']})"):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Identified Risk Drivers:**")
                for factor in student["factors"]:
                    st.write(f"• {factor}")
            with c2:
                st.markdown(f"**Targeted Action Items:**")
                for rec in student["recommendations"]:
                    st.write(f"• {rec}")


def render_visual_analytics():
    st.title("📈 Academic Analytics & Statistical Modeling")
    st.markdown("Longitudinal progression trends, student benchmarking, and attendance correlation.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Semester Progression Trends",
        "🎯 Attendance vs. Marks Correlation",
        "👥 Student Comparison Matrix",
        "🏆 Top & Lowest Performers"
    ])

    with tab1:
        st.subheader("Semester Progression Dynamics (Semesters 1 - 8)")
        trends_data, _ = api_get("/api/analytics/trends")
        if trends_data:
            df_t = pd.DataFrame(trends_data)
            fig_t = go.Figure()
            fig_t.add_trace(go.Bar(
                name="Average Score (%)",
                x=df_t["semester_label"], y=df_t["average_marks"],
                marker_color="#3b82f6", text=df_t["average_marks"], textposition="outside"
            ))
            fig_t.add_trace(go.Scatter(
                name="Pass Rate (%)",
                x=df_t["semester_label"], y=df_t["pass_percentage"],
                mode="lines+markers", line=dict(color="#10b981", width=3)
            ))
            fig_t.update_layout(height=400, yaxis_range=[0, 105], title="Semester Performance & Pass Rate Trends")
            st.plotly_chart(fig_t, use_container_width=True)
            st.dataframe(df_t, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Attendance Rate vs. Academic Performance Correlation")
        att_data, _ = api_get("/api/analytics/attendance-insights")
        if att_data:
            st.info(f"💡 **Statistical Insight:** {att_data['summary']}")
            if att_data["tiers"]:
                df_att = pd.DataFrame(att_data["tiers"])
                fig_att = px.bar(
                    df_att, x="tier", y="average_marks",
                    text="average_marks", color="average_marks",
                    title="Average Marks by Attendance Tier",
                    labels={"tier": "Attendance Bracket", "average_marks": "Average Score (%)"},
                    color_continuous_scale="Teal"
                )
                fig_att.update_yaxes(range=[0, 100])
                fig_att.update_layout(height=360)
                st.plotly_chart(fig_att, use_container_width=True)
                st.dataframe(df_att, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Side-by-Side Student Comparison Matrix")
        students_resp, _ = api_get("/api/students/?page_size=100")
        if students_resp and students_resp.get("items"):
            all_stu = students_resp["items"]
            options = [f"{s['student_id']} - {s['name']}" for s in all_stu]
            selected_ids = st.multiselect(
                "Select 2 to 5 students to compare:",
                options, default=options[:2] if len(options) >= 2 else options
            )

            if selected_ids:
                clean_ids = [s.split(" - ")[0] for s in selected_ids]
                comp_data, _ = api_post("/api/analytics/compare", json_data={"student_ids": clean_ids})
                if comp_data and comp_data.get("comparison_table"):
                    df_comp = pd.DataFrame(comp_data["comparison_table"])
                    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Institutional Honors & Remedial Rankings")
        rankings, _ = api_get("/api/analytics/rankings?limit=5")
        if rankings:
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                st.markdown("### 🏆 Top Academic Performers")
                df_top = pd.DataFrame([{
                    "ID": s["student_id"], "Name": s["name"], "Dept": s["department"],
                    "Average %": f"{s['average_marks']}%", "Grade": s["grade"]
                } for s in rankings["highest_performers"]])
                st.dataframe(df_top, use_container_width=True, hide_index=True)

            with rcol2:
                st.markdown("### ⚠️ Priority Intervention Watchlist")
                df_low = pd.DataFrame([{
                    "ID": s["student_id"], "Name": s["name"], "Dept": s["department"],
                    "Average %": f"{s['average_marks']}%", "Attendance": f"{s['attendance_percentage']}%",
                    "Risk": s["risk_level"]
                } for s in rankings["lowest_performers"]])
                st.dataframe(df_low, use_container_width=True, hide_index=True)


def render_manage_students():
    st.title("⚙️ Student Record Management")
    st.markdown("Create new records, modify scores, or remove records.")

    action = st.radio("Select Action:", ["➕ Add New Student", "✏️ Edit Student", "🗑️ Delete Student"], horizontal=True)

    if action == "➕ Add New Student":
        with st.form("add_student"):
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("Student ID *", placeholder="e.g. STU2050")
                new_name = st.text_input("Full Name *", placeholder="e.g. Rohini Sen")
                new_dept = st.selectbox("Department *", [
                    "Artificial Intelligence & Machine Learning",
                    "Computer Science & Engineering",
                    "Data Science",
                    "Information Technology",
                    "Electronics & Communication"
                ])
                new_sem = st.number_input("Semester *", min_value=1, max_value=8, value=4)
                new_year = st.selectbox("Academic Year *", ["2024-2025", "2023-2024", "2025-2026"])
                new_email = st.text_input("Email Address *", placeholder="rohini.sen@university.edu")
                new_att = st.number_input("Attendance Rate (%) *", min_value=0.0, max_value=100.0, value=85.0)

            with col2:
                st.markdown("**Subject Course Marks (0.0 - 100.0)**")
                m_math = st.number_input("Mathematics", 0.0, 100.0, 75.0, 0.5)
                m_prog = st.number_input("Programming / Python", 0.0, 100.0, 80.0, 0.5)
                m_ds = st.number_input("Data Structures", 0.0, 100.0, 78.0, 0.5)
                m_db = st.number_input("Database Systems", 0.0, 100.0, 82.0, 0.5)
                m_ml = st.number_input("Machine Learning", 0.0, 100.0, 85.0, 0.5)

            submitted = st.form_submit_button("🚀 Create Student Record", use_container_width=True)
            if submitted:
                payload = {
                    "student_id": new_id.strip(),
                    "name": new_name.strip(),
                    "department": new_dept,
                    "semester": int(new_sem),
                    "academic_year": new_year,
                    "email": new_email.strip(),
                    "attendance_percentage": float(new_att),
                    "math_marks": float(m_math),
                    "programming_marks": float(m_prog),
                    "data_structures_marks": float(m_ds),
                    "database_marks": float(m_db),
                    "machine_learning_marks": float(m_ml)
                }
                res, err = api_post("/api/students/", json_data=payload)
                if err:
                    st.error(f"Creation failed: {err}")
                else:
                    st.success(f"✅ Student {res['name']} ({res['student_id']}) created! Average: {res['average_marks']}%, Risk Tier: {res['risk_level']}")


def render_institutional_reports():
    st.title("📑 Institutional Reporting Center")
    st.markdown("Download official PDF dossiers, cohort CSV exports, and AI recommendation logs.")

    r1, r2 = st.columns(2)
    with r1:
        st.subheader("📄 PDF Dossiers")
        pdf_risk, _ = download_file("/api/reports/at-risk/pdf")
        if pdf_risk:
            st.download_button(
                label="⬇️ Download Institutional At-Risk PDF Dossier",
                data=pdf_risk,
                file_name="institutional_at_risk_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with r2:
        st.subheader("📊 CSV Data Exports")
        csv_cohort, _ = download_file("/api/reports/class/csv")
        if csv_cohort:
            st.download_button(
                label="⬇️ Export Full Student Cohort (CSV)",
                data=csv_cohort,
                file_name="student_cohort_data.csv",
                mime="text/csv",
                use_container_width=True
            )

        csv_sub, _ = download_file("/api/reports/subject-analytics/csv")
        if csv_sub:
            st.download_button(
                label="⬇️ Export Subject Performance Analytics (CSV)",
                data=csv_sub,
                file_name="subject_analytics.csv",
                mime="text/csv",
                use_container_width=True
            )

        csv_ai, _ = download_file("/api/reports/ai-recommendations/csv")
        if csv_ai:
            st.download_button(
                label="⬇️ Export Historical AI Recommendations (CSV)",
                data=csv_ai,
                file_name="ai_recommendations_archive.csv",
                mime="text/csv",
                use_container_width=True
            )


# --- Student Dedicated Views ---

def render_student_portal():
    user = st.session_state["user_info"]
    # Look up student matching either assigned student_id or username
    stu_lookup = user.get("student_id") or user.get("username").upper()

    student, err = api_get(f"/api/students/{stu_lookup}")
    if err or not student:
        # Fallback to STU1001 for demo student
        student, _ = api_get("/api/students/STU1001")

    if not student:
        st.warning("No student profile linked to your user account.")
        return

    st.title(f"🎓 Welcome, {student['name']}!")
    st.markdown(f"**Department:** {student['department']} | **Semester:** {student['semester']} | **Academic Year:** {student['academic_year']}")

    # KPI Banner
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cumulative Average</div>
            <div class="metric-value">{student['average_marks']}%</div>
            <div class="metric-sub">Across 5 Curriculum Courses</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Letter Grade</div>
            <div class="metric-value">{student['grade']}</div>
            <div class="metric-sub">Total: {student['total_marks']}/500</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Attendance Rate</div>
            <div class="metric-value">{student['attendance_percentage']}%</div>
            <div class="metric-sub">Institutional requirement &ge; 75%</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        risk_color = "#10b981" if student['risk_level'] == "Good" else ("#f59e0b" if student['risk_level'] == "Needs Attention" else "#ef4444")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Academic Standing</div>
            <div class="metric-value" style="color: {risk_color}">{student['risk_level']}</div>
            <div class="metric-sub">Evaluated by 3-Tier Risk Engine</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for Student Portal
    s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs([
        "📊 Course Marks & Class Benchmark",
        "🤖 AI Performance Diagnosis",
        "📝 My Weekly Study Plan & Checklist",
        "📄 Official PDF Report Card"
    ])

    with s_tab1:
        st.subheader("Your Scores vs. Department Average")
        bench_data, _ = api_get(f"/api/analytics/compare/{student['student_id']}")
        if bench_data and bench_data.get("breakdown"):
            df_b = pd.DataFrame(bench_data["breakdown"])
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(
                name="Your Score", x=df_b["subject"], y=df_b["student_score"],
                marker_color="#38bdf8", text=df_b["student_score"], textposition="outside"
            ))
            fig_b.add_trace(go.Bar(
                name="Class Average", x=df_b["subject"], y=df_b["department_average"],
                marker_color="#94a3b8", text=df_b["department_average"], textposition="outside"
            ))
            fig_b.update_layout(barmode="group", height=380, yaxis_range=[0, 105], title="Performance Benchmark")
            st.plotly_chart(fig_b, use_container_width=True)
            st.dataframe(df_b, use_container_width=True, hide_index=True)

    with s_tab2:
        st.subheader("🤖 Gemini AI Academic Diagnostic Analysis")
        st.markdown("Generate personalized learning evaluations and weak topic identification powered by Google Gemini.")

        if st.button("🚀 Run Live AI Diagnostic Analysis", type="primary"):
            with st.spinner("Analyzing your academic records with Google Gemini AI..."):
                ai_res, ai_err = api_post(f"/api/ai/analyze/{student['student_id']}")
            if ai_err:
                st.error(f"AI diagnosis failed: {ai_err}")
            elif ai_res:
                st.session_state["latest_ai"] = ai_res
                st.success("✅ AI Diagnostic Evaluation Completed!")

        # Display AI Result if available
        ai_res = st.session_state.get("latest_ai")
        if not ai_res:
            # Check historical recommendations
            hist, _ = api_get(f"/api/ai/history/{student['student_id']}")
            if hist and len(hist) > 0:
                h = hist[0]
                st.markdown(f"""
                <div class="ai-box">
                    <h4>📝 Executive Diagnostic Summary</h4>
                    <p>{h['overall_summary']}</p>
                    <p><b>Strong Courses:</b> {h['strong_subjects']}</p>
                    <p><b>Priority Focus Areas:</b> {h['weak_subjects']}</p>
                    <p><b>Actionable Advice:</b> {h['actionable_plan']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            analysis = ai_res["analysis"]
            st.markdown(f"""
            <div class="ai-box">
                <h4>📝 Executive Diagnostic Summary (Source: {ai_res['source']})</h4>
                <p>{analysis['overall_summary']}</p>
                <p><b>🌟 Strong Courses:</b> {', '.join(analysis['strong_subjects'])}</p>
                <p><b>💡 Personalized Study Advice:</b> {analysis['personalized_advice']}</p>
                <p><b>⏱️ Recommended Weekly Study Commitment:</b> <b>{analysis['recommended_weekly_hours']} Hours</b></p>
            </div>
            """, unsafe_allow_html=True)

            if analysis.get("weak_subjects"):
                st.subheader("🎯 Priority Focus Curriculum Topics")
                for w in analysis["weak_subjects"]:
                    st.write(f"- **{w['subject']}** (Current Score: {w['score']}% | Gap: {w['gap']} pts):")
                    for t in w["priority_topics"]:
                        st.write(f"  • {t}")

    with s_tab3:
        st.subheader("📝 Personalized Weekly Study Plan")
        st.markdown("Track and complete your tailored study activities. Progress updates in real time.")

        plan, plan_err = api_get(f"/api/study-plans/{student['student_id']}")
        if plan:
            st.markdown(f"**Plan Title:** *{plan['title']}* (Status: `{plan['status'].upper()}`)")

            items = plan.get("items", [])
            total_items = len(items)
            completed_items = sum(1 for i in items if i["is_completed"])
            progress_pct = (completed_items / total_items) if total_items > 0 else 0.0

            st.progress(progress_pct, text=f"Progress: {completed_items}/{total_items} Tasks Completed ({round(progress_pct * 100)}%)")

            for item in items:
                col_box, col_txt = st.columns([1, 10])
                with col_box:
                    checked = st.checkbox(
                        label=f"Done {item['id']}",
                        value=item["is_completed"],
                        key=f"task_{item['id']}",
                        label_visibility="collapsed"
                    )
                    if checked != item["is_completed"]:
                        api_patch(f"/api/study-plans/items/{item['id']}/toggle")
                        st.rerun()

                with col_txt:
                    status_prefix = "~~" if item["is_completed"] else "**"
                    status_suffix = "~~ ✅" if item["is_completed"] else f"** ({item['estimated_minutes']} mins)"
                    st.markdown(f"{status_prefix}{item['day_of_week']}: {item['topic']}{status_suffix}")
                    st.caption(f"Task: {item['activity']}")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Generate Fresh Weekly Study Plan"):
                api_post(f"/api/study-plans/generate/{student['student_id']}")
                st.success("Generated new study roadmap!")
                st.rerun()

    with s_tab4:
        st.subheader("📄 Official Academic Grade Card Download")
        st.markdown("Download your certified PDF report card generated with institutional seal, marks breakdown, and AI diagnostic notes.")

        pdf_bytes, pdf_err = download_file(f"/api/reports/student/{student['student_id']}/pdf")
        if pdf_bytes:
            st.download_button(
                label="⬇️ Download Official Grade Card (PDF)",
                data=pdf_bytes,
                file_name=f"{student['student_id']}_report_card.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


# --- Main Application Router ---

def main():
    if not st.session_state.get("token"):
        render_login_view()
    else:
        role = st.session_state["user_info"]["role"]
        selected_menu = render_sidebar()

        if role == "student":
            render_student_portal()
        elif role == "admin":
            if selected_menu == "📊 Executive Overview":
                render_executive_overview()
            elif selected_menu == "📋 Student Directory":
                render_student_directory()
            elif selected_menu == "📥 Bulk Data Ingestion":
                render_bulk_ingestion()
            elif selected_menu == "⚠️ At-Risk & Support Monitor":
                render_at_risk_monitor()
            elif selected_menu == "📈 Advanced Visual Analytics":
                render_visual_analytics()
            elif selected_menu == "⚙️ Manage Student Records":
                render_manage_students()
            elif selected_menu == "📑 Institutional Reports":
                render_institutional_reports()
        elif role == "teacher":
            if selected_menu == "📊 Cohort Performance":
                render_executive_overview()
            elif selected_menu == "📋 Student Explorer":
                render_student_directory()
            elif selected_menu == "⚠️ 3-Tier Risk Intervention":
                render_at_risk_monitor()
            elif selected_menu == "📈 Comparative Analytics":
                render_visual_analytics()
            elif selected_menu == "⚙️ Record Management":
                render_manage_students()
            elif selected_menu == "📑 Export Reports":
                render_institutional_reports()


if __name__ == "__main__":
    main()
