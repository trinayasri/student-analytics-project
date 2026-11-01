"""
dashboard.py - Streamlit Interactive Frontend Dashboard

Communicates with the FastAPI backend strictly via HTTP REST endpoints.
Features:
- Executive Overview KPI Cards
- Student Directory with pagination, real-time search, and department/semester filters
- Academic Analytics with interactive Plotly visualizations
- Academic Support & At-Risk Early Warning System
- Student Management Forms (Add, Edit, Delete with confirmation)
"""

import os
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure Backend API endpoint from environment or default local port
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Student Performance Analytics System",
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
        padding: 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        margin-top: 4px;
        color: #38bdf8;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 2px;
    }
    .badge-pass {
        background-color: #065f46;
        color: #6ee7b7;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-risk {
        background-color: #991b1b;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- HTTP Client API Helpers ---

def api_get(endpoint: str, params: dict = None):
    """Performs HTTP GET request to FastAPI backend with error handling."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable. Please ensure FastAPI is running on port 8000."
    except requests.exceptions.HTTPError as e:
        detail = response.json().get("detail", str(e)) if response.content else str(e)
        return None, f"HTTP {response.status_code}: {detail}"
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, json_data: dict):
    """Performs HTTP POST request to FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=json_data, timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable. Please check backend service."
    except requests.exceptions.HTTPError:
        detail = response.json().get("detail", "Error creating record")
        return None, detail
    except Exception as e:
        return None, str(e)


def api_put(endpoint: str, json_data: dict):
    """Performs HTTP PUT request to FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.put(url, json=json_data, timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError:
        detail = response.json().get("detail", "Error updating record")
        return None, detail
    except Exception as e:
        return None, str(e)


def api_delete(endpoint: str):
    """Performs HTTP DELETE request to FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.delete(url, timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend API is unreachable."
    except requests.exceptions.HTTPError:
        detail = response.json().get("detail", "Error deleting record")
        return None, detail
    except Exception as e:
        return None, str(e)


# --- Sidebar & Navigation ---

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("Academic Analytics")
    st.caption("AI-Powered Student Performance & Early Intervention")

    # Check backend health
    health_data, health_err = api_get("/health")
    if health_err:
        st.error("● Backend Offline")
        st.info("Start FastAPI server in terminal:\n`python -m uvicorn app.main:app --reload`")
    else:
        st.success("● Backend Operational (FastAPI v1.0.0)")

    st.markdown("---")
    menu = st.radio(
        "Navigation Menu",
        [
            "📊 Executive Dashboard",
            "📋 Student Directory",
            "📈 Visual Analytics",
            "⚠️ Support & At-Risk Monitor",
            "⚙️ Manage Students"
        ]
    )

    st.markdown("---")
    st.caption("💡 **Tip**: In interview discussions, emphasize the clear architectural separation between this Streamlit frontend and the FastAPI REST backend.")


# --- Tab 1: Executive Dashboard ---

if menu == "📊 Executive Dashboard":
    st.title("🎓 Institutional Performance Overview")
    st.markdown("Real-time academic performance KPIs and institutional enrollment metrics.")

    summary, err = api_get("/api/analytics/summary")
    if err:
        st.error(f"Unable to load summary metrics: {err}")
    elif summary:
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
                <div class="metric-label">Overall Pass Rate</div>
                <div class="metric-value">{summary['pass_percentage']}%</div>
                <div class="metric-sub">Passing threshold &ge; 50%</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            risk_color = "#ef4444" if summary['at_risk_count'] > 0 else "#22c55e"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Students Needing Support</div>
                <div class="metric-value" style="color: {risk_color}">{summary['at_risk_count']}</div>
                <div class="metric-sub">Avg &lt; 50% or subject &lt; 40</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Highlight top performer
        if summary.get("top_performer"):
            top = summary["top_performer"]
            st.success(
                f"🏆 **Top Institutional Performer**: **{top['name']}** ({top['student_id']}) — "
                f"**{top['average_marks']}%** (Grade: **{top['grade']}**) | Department: *{top['department']}*"
            )

        # Quick charts row
        st.markdown("### Quick Analytics Snapshots")
        c1, c2 = st.columns(2)

        with c1:
            grades_data, _ = api_get("/api/analytics/grade-distribution")
            if grades_data:
                df_grades = pd.DataFrame(grades_data)
                fig_grades = px.bar(
                    df_grades,
                    x="grade",
                    y="count",
                    text="count",
                    title="Student Grade Distribution",
                    labels={"grade": "Letter Grade", "count": "Number of Students"},
                    color="grade",
                    color_discrete_map={
                        "A+": "#10b981", "A": "#3b82f6", "B": "#6366f1",
                        "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"
                    }
                )
                fig_grades.update_layout(showlegend=False, height=340)
                st.plotly_chart(fig_grades, use_container_width=True)

        with c2:
            depts_data, _ = api_get("/api/analytics/departments")
            if depts_data:
                df_depts = pd.DataFrame(depts_data)
                fig_depts = px.pie(
                    df_depts,
                    names="department",
                    values="student_count",
                    title="Department Enrollment Distribution",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_depts.update_layout(height=340)
                st.plotly_chart(fig_depts, use_container_width=True)


# --- Tab 2: Student Directory ---

elif menu == "📋 Student Directory":
    st.title("📋 Student Directory & Records Explorer")
    st.markdown("Search, filter, and inspect detailed academic profiles.")

    # Fetch departments for filter dropdown
    depts_list, _ = api_get("/api/students/departments")
    if not depts_list:
        depts_list = []

    # Filter Controls Bar
    with st.expander("🔍 Search and Filter Options", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 1, 1])
        with fcol1:
            search_query = st.text_input("Search by Name or Student ID", placeholder="e.g. STU1001 or Aarav")
        with fcol2:
            selected_dept = st.selectbox("Filter Department", ["All Departments"] + depts_list)
        with fcol3:
            selected_sem = st.selectbox("Filter Semester", ["All", 1, 2, 3, 4, 5, 6, 7, 8])
        with fcol4:
            page_size = st.selectbox("Rows per page", [10, 20, 50], index=0)

    # Prepare Query Parameters
    params = {"page": st.session_state.get("curr_page", 1), "page_size": page_size}
    if search_query.strip():
        params["search"] = search_query.strip()
    if selected_dept != "All Departments":
        params["department"] = selected_dept
    if selected_sem != "All":
        params["semester"] = int(selected_sem)

    # Pagination state
    if "curr_page" not in st.session_state:
        st.session_state["curr_page"] = 1

    params["page"] = st.session_state["curr_page"]

    with st.spinner("Fetching student records from API..."):
        resp, err = api_get("/api/students/", params=params)

    if err:
        st.error(f"Error fetching students: {err}")
    elif resp:
        students = resp.get("items", [])
        total_count = resp.get("total_count", 0)
        total_pages = resp.get("total_pages", 1)

        st.markdown(f"**Found {total_count} student records** (Page {st.session_state['curr_page']} of {max(total_pages, 1)})")

        if students:
            # Format student table dataframe
            display_data = []
            for s in students:
                display_data.append({
                    "ID": s["student_id"],
                    "Name": s["name"],
                    "Department": s["department"],
                    "Semester": s["semester"],
                    "Math": s["math_marks"],
                    "Python": s["programming_marks"],
                    "DSA": s["data_structures_marks"],
                    "DBMS": s["database_marks"],
                    "ML": s["machine_learning_marks"],
                    "Total (/500)": s["total_marks"],
                    "Average %": f"{s['average_marks']}%",
                    "Grade": s["grade"],
                    "Status": "⚠️ Needs Support" if s["needs_support"] else "✅ Good Standing"
                })

            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Pagination Controls
            pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
            with pcol1:
                if st.button("⬅️ Previous Page", disabled=(st.session_state["curr_page"] <= 1)):
                    st.session_state["curr_page"] -= 1
                    st.rerun()
            with pcol3:
                if st.button("Next Page ➡️", disabled=(st.session_state["curr_page"] >= total_pages)):
                    st.session_state["curr_page"] += 1
                    st.rerun()

            # Detailed Single Student Inspector
            st.markdown("---")
            st.subheader("🔎 Individual Student Deep Dive")
            selected_id = st.selectbox(
                "Select a student from the current page to inspect individual performance:",
                [f"{s['student_id']} - {s['name']}" for s in students]
            )

            if selected_id:
                stu_id = selected_id.split(" - ")[0]
                target = next((s for s in students if s["student_id"] == stu_id), None)
                if target:
                    dcol1, dcol2 = st.columns([1, 1])
                    with dcol1:
                        st.write(f"**Registration ID:** `{target['student_id']}`")
                        st.write(f"**Full Name:** {target['name']}")
                        st.write(f"**Email:** {target['email']}")
                        st.write(f"**Department:** {target['department']}")
                        st.write(f"**Semester:** {target['semester']}")
                        st.write(f"**Letter Grade:** `{target['grade']}`")
                        if target["needs_support"]:
                            st.warning("⚠️ Flagged for Academic Intervention (Low Aggregate or Failed Course)")
                        else:
                            st.success("✅ Student in Good Academic Standing")

                    with dcol2:
                        # Subject scores radar / bar chart
                        subject_scores = {
                            "Mathematics": target["math_marks"],
                            "Programming": target["programming_marks"],
                            "Data Structures": target["data_structures_marks"],
                            "Database Systems": target["database_marks"],
                            "Machine Learning": target["machine_learning_marks"]
                        }
                        fig_stu = px.bar(
                            x=list(subject_scores.keys()),
                            y=list(subject_scores.values()),
                            labels={"x": "Subject", "y": "Marks (0-100)"},
                            title=f"Course Marks: {target['name']}",
                            text=list(subject_scores.values()),
                            color=list(subject_scores.values()),
                            color_continuous_scale="Blues"
                        )
                        fig_stu.update_yaxes(range=[0, 100])
                        fig_stu.update_layout(height=280, showlegend=False)
                        st.plotly_chart(fig_stu, use_container_width=True)
        else:
            st.info("No student records found matching the given criteria.")


# --- Tab 3: Visual Analytics ---

elif menu == "📈 Visual Analytics":
    st.title("📈 Academic Analytics & Insights")
    st.markdown("Interactive visualizations generated from live SQLite data via REST endpoints.")

    t1, t2, t3 = st.tabs(["🏛️ Department Performance", "📊 Grade Distribution", "📚 Subject Performance"])

    with t1:
        st.subheader("Department-wise Performance & Enrollment Analysis")
        dept_data, err = api_get("/api/analytics/departments")
        if err:
            st.error(err)
        elif dept_data:
            df_dept = pd.DataFrame(dept_data)

            col1, col2 = st.columns([3, 2])
            with col1:
                fig_dbar = px.bar(
                    df_dept,
                    x="department",
                    y="average_marks",
                    text="average_marks",
                    title="Average Marks by Academic Department",
                    labels={"department": "Department", "average_marks": "Average Score (%)"},
                    color="average_marks",
                    color_continuous_scale="Viridis"
                )
                fig_dbar.update_layout(height=380)
                st.plotly_chart(fig_dbar, use_container_width=True)

            with col2:
                fig_dpie = px.pie(
                    df_dept,
                    names="department",
                    values="student_count",
                    title="Student Count by Department",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                fig_dpie.update_layout(height=380)
                st.plotly_chart(fig_dpie, use_container_width=True)

            st.dataframe(df_dept, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("Overall Grade Distribution")
        grades_data, err = api_get("/api/analytics/grade-distribution")
        if err:
            st.error(err)
        elif grades_data:
            df_g = pd.DataFrame(grades_data)
            fig_g = px.bar(
                df_g,
                x="grade",
                y="count",
                text="percentage",
                title="Institutional Grade Tier Breakdown (% of student body)",
                labels={"grade": "Grade", "count": "Student Count", "percentage": "% of Students"},
                color="grade",
                color_discrete_map={
                    "A+": "#10b981", "A": "#3b82f6", "B": "#6366f1",
                    "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"
                }
            )
            fig_g.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_g.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_g, use_container_width=True)
            st.dataframe(df_g, use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Subject-Level Performance Comparison")
        sub_data, err = api_get("/api/analytics/subject-averages")
        if err:
            st.error(err)
        elif sub_data:
            df_sub = pd.DataFrame(sub_data)
            fig_sub = go.Figure()
            fig_sub.add_trace(go.Bar(
                name="Average Score",
                x=df_sub["subject"],
                y=df_sub["average_score"],
                marker_color="#3b82f6"
            ))
            fig_sub.add_trace(go.Bar(
                name="Highest Score",
                x=df_sub["subject"],
                y=df_sub["highest_score"],
                marker_color="#10b981"
            ))
            fig_sub.add_trace(go.Bar(
                name="Lowest Score",
                x=df_sub["subject"],
                y=df_sub["lowest_score"],
                marker_color="#ef4444"
            ))
            fig_sub.update_layout(
                barmode="group",
                title="Subject Score Dynamics (Average vs Max vs Min)",
                yaxis_range=[0, 100],
                height=400
            )
            st.plotly_chart(fig_sub, use_container_width=True)
            st.dataframe(df_sub, use_container_width=True, hide_index=True)


# --- Tab 4: Support & At-Risk Monitor ---

elif menu == "⚠️ Support & At-Risk Monitor":
    st.title("⚠️ Academic Support & Early Warning System")
    st.markdown(
        "Identifies students who may require academic counseling or remedial support.\n\n"
        "> **Criteria Defined**:\n"
        "> 1. Aggregate percentage is below **50.0%** (Grade F), OR\n"
        "> 2. Score in any individual subject is below **40.0%** (Passing cutoff)."
    )

    at_risk_list, err = api_get("/api/analytics/at-risk")
    if err:
        st.error(err)
    elif at_risk_list:
        st.error(f"🚨 **{len(at_risk_list)} Students** currently flagged for academic intervention.")

        risk_rows = []
        for s in at_risk_list:
            failed_subjects = []
            if s["math_marks"] < 40: failed_subjects.append(f"Math ({s['math_marks']})")
            if s["programming_marks"] < 40: failed_subjects.append(f"Programming ({s['programming_marks']})")
            if s["data_structures_marks"] < 40: failed_subjects.append(f"DSA ({s['data_structures_marks']})")
            if s["database_marks"] < 40: failed_subjects.append(f"DBMS ({s['database_marks']})")
            if s["machine_learning_marks"] < 40: failed_subjects.append(f"ML ({s['machine_learning_marks']})")

            reason = []
            if s["average_marks"] < 50.0:
                reason.append(f"Low aggregate average ({s['average_marks']}%)")
            if failed_subjects:
                reason.append("Failed subject(s): " + ", ".join(failed_subjects))

            risk_rows.append({
                "Student ID": s["student_id"],
                "Name": s["name"],
                "Department": s["department"],
                "Semester": s["semester"],
                "Average %": f"{s['average_marks']}%",
                "Grade": s["grade"],
                "Intervention Reason": " | ".join(reason)
            })

        df_risk = pd.DataFrame(risk_rows)
        st.dataframe(df_risk, use_container_width=True, hide_index=True)

        st.markdown("### 📩 Recommended Intervention Actions")
        st.info(
            "1. Schedule one-on-one academic mentoring sessions with department faculty advisors.\n"
            "2. Offer focused remedial problem-solving workshops for core subjects with scores < 40.\n"
            "3. Monitor performance progression in subsequent internal assessments."
        )
    else:
        st.success("🎉 Excellent! Zero students are currently flagged as at-risk.")


# --- Tab 5: Manage Students ---

elif menu == "⚙️ Manage Students":
    st.title("⚙️ Student Record Management")
    st.markdown("Add new student records, modify details, or remove records with validation.")

    action = st.radio("Select Action:", ["➕ Add New Student", "✏️ Edit Student", "🗑️ Delete Student"], horizontal=True)

    # Sub-Action 1: Add Student
    if action == "➕ Add New Student":
        st.subheader("Add a New Student Record")
        with st.form("add_student_form", clear_on_submit=False):
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
                new_email = st.text_input("Email Address *", placeholder="rohini.sen@university.edu")

            with col2:
                st.markdown("**Subject Marks (0.0 to 100.0)**")
                m_math = st.number_input("Mathematics", min_value=0.0, max_value=100.0, value=75.0, step=0.5)
                m_prog = st.number_input("Programming / Python", min_value=0.0, max_value=100.0, value=80.0, step=0.5)
                m_ds = st.number_input("Data Structures", min_value=0.0, max_value=100.0, value=78.0, step=0.5)
                m_db = st.number_input("Database Systems", min_value=0.0, max_value=100.0, value=82.0, step=0.5)
                m_ml = st.number_input("Machine Learning", min_value=0.0, max_value=100.0, value=85.0, step=0.5)

            submitted = st.form_submit_button("🚀 Submit Student Record", use_container_width=True)

            if submitted:
                if not new_id.strip() or not new_name.strip() or not new_email.strip():
                    st.error("Please fill in all required fields (Student ID, Name, Email).")
                else:
                    payload = {
                        "student_id": new_id.strip(),
                        "name": new_name.strip(),
                        "department": new_dept,
                        "semester": int(new_sem),
                        "email": new_email.strip(),
                        "math_marks": float(m_math),
                        "programming_marks": float(m_prog),
                        "data_structures_marks": float(m_ds),
                        "database_marks": float(m_db),
                        "machine_learning_marks": float(m_ml)
                    }
                    res, err = api_post("/api/students/", payload)
                    if err:
                        st.error(f"Failed to add student: {err}")
                    else:
                        st.success(f"✅ Student {res['name']} ({res['student_id']}) created successfully with Average {res['average_marks']}% (Grade: {res['grade']})!")

    # Sub-Action 2: Edit Student
    elif action == "✏️ Edit Student":
        st.subheader("Edit Existing Student Details & Marks")
        lookup_id = st.text_input("Enter Student ID to edit:", placeholder="e.g. STU1001")

        if lookup_id.strip():
            stu, err = api_get(f"/api/students/{lookup_id.strip()}")
            if err:
                st.error(f"Student not found: {err}")
            elif stu:
                st.info(f"Editing profile for: **{stu['name']}** (Current Average: {stu['average_marks']}%)")
                with st.form("edit_student_form"):
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        e_name = st.text_input("Full Name", value=stu["name"])
                        e_dept = st.text_input("Department", value=stu["department"])
                        e_sem = st.number_input("Semester", min_value=1, max_value=8, value=stu["semester"])
                        e_email = st.text_input("Email", value=stu["email"])

                    with ecol2:
                        st.markdown("**Subject Marks**")
                        e_math = st.number_input("Mathematics", min_value=0.0, max_value=100.0, value=float(stu["math_marks"]), step=0.5)
                        e_prog = st.number_input("Programming", min_value=0.0, max_value=100.0, value=float(stu["programming_marks"]), step=0.5)
                        e_ds = st.number_input("Data Structures", min_value=0.0, max_value=100.0, value=float(stu["data_structures_marks"]), step=0.5)
                        e_db = st.number_input("Database Systems", min_value=0.0, max_value=100.0, value=float(stu["database_marks"]), step=0.5)
                        e_ml = st.number_input("Machine Learning", min_value=0.0, max_value=100.0, value=float(stu["machine_learning_marks"]), step=0.5)

                    save_btn = st.form_submit_button("💾 Save Updated Information", use_container_width=True)
                    if save_btn:
                        update_payload = {
                            "name": e_name.strip(),
                            "department": e_dept.strip(),
                            "semester": int(e_sem),
                            "email": e_email.strip(),
                            "math_marks": float(e_math),
                            "programming_marks": float(e_prog),
                            "data_structures_marks": float(e_ds),
                            "database_marks": float(e_db),
                            "machine_learning_marks": float(e_ml)
                        }
                        up_res, up_err = api_put(f"/api/students/{stu['student_id']}", update_payload)
                        if up_err:
                            st.error(f"Failed to update student: {up_err}")
                        else:
                            st.success(f"✅ Record updated! New Average: {up_res['average_marks']}% | Grade: {up_res['grade']}")

    # Sub-Action 3: Delete Student
    elif action == "🗑️ Delete Student":
        st.subheader("Delete a Student Record")
        del_target = st.text_input("Enter Student ID to delete:", placeholder="e.g. STU1011")

        if del_target.strip():
            stu, err = api_get(f"/api/students/{del_target.strip()}")
            if err:
                st.error(f"Student not found: {err}")
            elif stu:
                st.warning(f"⚠️ Are you sure you want to permanently delete **{stu['name']}** ({stu['student_id']}) from department *{stu['department']}*?")
                confirm_check = st.checkbox("I confirm that I want to permanently delete this student record.")

                if st.button("🗑️ Permanently Delete Record", disabled=not confirm_check, type="primary"):
                    del_res, del_err = api_delete(f"/api/students/{stu['student_id']}")
                    if del_err:
                        st.error(f"Delete failed: {del_err}")
                    else:
                        st.success(del_res["message"])
