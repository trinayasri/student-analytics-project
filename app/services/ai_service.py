"""
ai_service.py - Google Gemini AI Diagnostic & Study Plan Service

Integrates with the Google Gemini API to produce personalized academic diagnostics,
identify weak curriculum topics, and structure actionable weekly study plans.

Resilience & Security Design:
- Reads GEMINI_API_KEY from configuration (never hardcoded).
- Enforces strict JSON Schema prompts and validates output against Pydantic models.
- Gracefully handles missing API keys, rate limits, timeouts, and network outages with
  an intelligent deterministic pedagogical fallback engine.
- Persists recommendations to AIRecommendation and StudyPlan database tables.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models import Student, AIRecommendation, StudyPlan, StudyPlanItem
from app.schemas import (
    AIPerformanceAnalysis,
    WeakSubjectDetail,
    StudyPlanItemCreate,
    FullAIAnalysisResponse
)

logger = logging.getLogger(__name__)

# Subject syllabus topic repository for realistic curriculum targeting
SUBJECT_SYLLABUS = {
    "Mathematics": [
        "Linear Algebra & Matrix Decompositions",
        "Multivariate Calculus & Optimization",
        "Probability Distributions & Bayes Theorem",
        "Differential Equations & Fourier Transforms"
    ],
    "Programming / Python": [
        "Object-Oriented Programming & Design Patterns",
        "Memory Management & Generators",
        "Asynchronous Programming (asyncio)",
        "Exception Handling & Unit Testing"
    ],
    "Data Structures": [
        "Binary Search Trees & AVL Trees",
        "Graph Algorithms (Dijkstra, BFS, DFS)",
        "Dynamic Programming & Memoization",
        "Hash Tables & Collision Resolution"
    ],
    "Database Systems": [
        "Relational Schema Normalization (3NF/BCNF)",
        "Complex SQL Queries & Index Optimization",
        "ACID Transactions & Concurrency Control",
        "NoSQL Architecture & Document Stores"
    ],
    "Machine Learning": [
        "Supervised Learning (Regression & Classification)",
        "Neural Networks & Backpropagation",
        "Model Regularization & Cross-Validation",
        "Unsupervised Clustering (K-Means & PCA)"
    ]
}


def _deterministic_pedagogical_analysis(student: Student) -> Tuple[AIPerformanceAnalysis, List[StudyPlanItemCreate]]:
    """
    Fallback deterministic diagnostic engine.
    Analyzes actual student marks to produce targeted pedagogical summaries
    and a weekly study plan without requiring external API access.
    """
    scores = {
        "Mathematics": float(student.math_marks),
        "Programming / Python": float(student.programming_marks),
        "Data Structures": float(student.data_structures_marks),
        "Database Systems": float(student.database_marks),
        "Machine Learning": float(student.machine_learning_marks)
    }

    # Identify strong subjects (>= 75.0) and weak subjects (< 65.0)
    strong = [sub for sub, score in scores.items() if score >= 75.0]
    weak_candidates = sorted([(sub, score) for sub, score in scores.items() if score < 70.0], key=lambda x: x[1])

    weak_details: List[WeakSubjectDetail] = []
    for sub, score in weak_candidates:
        gap = round(75.0 - score, 1) if score < 75.0 else 0.0
        topics = SUBJECT_SYLLABUS.get(sub, ["Fundamental Concepts", "Problem Solving"])[:3]
        weak_details.append(WeakSubjectDetail(
            subject=sub,
            score=score,
            gap=gap,
            priority_topics=topics
        ))

    # If student scored well in all courses, target the lowest relatively
    if not weak_details:
        lowest_sub = min(scores.items(), key=lambda x: x[1])
        weak_details.append(WeakSubjectDetail(
            subject=lowest_sub[0],
            score=lowest_sub[1],
            gap=round(90.0 - lowest_sub[1], 1) if lowest_sub[1] < 90.0 else 5.0,
            priority_topics=SUBJECT_SYLLABUS.get(lowest_sub[0], ["Advanced Topics"])[:2]
        ))

    avg = float(student.average_marks)
    att = float(student.attendance_percentage or 85.0)

    # Narrative Summary
    if avg >= 80.0:
        summary = (
            f"{student.name} demonstrates exemplary academic comprehension with a cumulative average of {avg}% "
            f"and strong command in {', '.join(strong) if strong else 'core subjects'}. "
            f"Focus should be directed toward advanced project development and research."
        )
        recommended_hours = 6
        advice = "Maintain high-level problem-solving consistency. Mentor peers and explore competitive coding and research papers."
    elif avg >= 60.0:
        weak_names = [w.subject for w in weak_details]
        summary = (
            f"{student.name} displays satisfactory academic progress with an overall average of {avg}%. "
            f"Performance is solid, but noticeable variance exists in {', '.join(weak_names)}. "
            f"Targeted review of foundational principles will elevate academic standing."
        )
        recommended_hours = 10
        advice = "Allocate 45 minutes daily to your weakest subject before tackling homework in stronger subjects."
    else:
        weak_names = [w.subject for w in weak_details]
        summary = (
            f"{student.name} requires structured remedial intervention. With an average of {avg}% "
            f"and critical gaps in {', '.join(weak_names)}, intensive revision of core topics is urgently recommended."
        )
        recommended_hours = 16
        advice = "Prioritize daily scheduled revision blocks. Meet faculty mentors weekly and solve 5 practice problems every evening."

    analysis = AIPerformanceAnalysis(
        overall_summary=summary,
        strong_subjects=strong if strong else ["Consistent Across Curriculum"],
        weak_subjects=weak_details,
        personalized_advice=advice,
        recommended_weekly_hours=recommended_hours
    )

    # Generate 5-day structured study plan
    primary_weak = weak_details[0].subject if weak_details else "Mathematics"
    primary_topics = SUBJECT_SYLLABUS.get(primary_weak, ["Core Concepts", "Practice Questions", "Revision"])

    study_plan_items = [
        StudyPlanItemCreate(
            day_of_week="Monday",
            topic=f"{primary_weak}: {primary_topics[0]}",
            activity="Read lecture slides, summarize formulas and core theorems in notes.",
            estimated_minutes=45
        ),
        StudyPlanItemCreate(
            day_of_week="Tuesday",
            topic=f"{primary_weak}: Conceptual Application",
            activity="Implement 3 textbook practice problems and verify step-by-step solutions.",
            estimated_minutes=60
        ),
        StudyPlanItemCreate(
            day_of_week="Wednesday",
            topic=f"{primary_weak}: {primary_topics[1] if len(primary_topics) > 1 else 'Intermediate Theory'}",
            activity="Review difficult quiz questions from previous assessments and rewrite answers.",
            estimated_minutes=45
        ),
        StudyPlanItemCreate(
            day_of_week="Thursday",
            topic=f"Secondary Review: {weak_details[1].subject if len(weak_details) > 1 else primary_weak}",
            activity="Solve 2 past exam question papers under timed 45-minute conditions.",
            estimated_minutes=60
        ),
        StudyPlanItemCreate(
            day_of_week="Friday",
            topic="Weekly Synthesis & Self-Assessment",
            activity="Review errors made during the week, update summary cheat-sheet, and consult faculty advisor if doubts persist.",
            estimated_minutes=45
        )
    ]

    return analysis, study_plan_items


def _call_gemini_api(student: Student) -> Optional[Tuple[AIPerformanceAnalysis, List[StudyPlanItemCreate]]]:
    """
    Invokes the Google Gemini API using structured JSON output prompts.
    Returns (analysis, study_plan_items) on success, or None on any API error.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
You are an expert university academic advisor and learning diagnostician.
Analyze the following student performance data and produce an objective, encouraging diagnostic evaluation and a 5-day weekly study roadmap.

Student Profile:
- Name: {student.name}
- Student ID: {student.student_id}
- Department: {student.department}
- Semester: {student.semester}
- Cumulative Average: {student.average_marks}%
- Attendance Rate: {student.attendance_percentage}%
- Academic Grade: {student.grade}
- Risk Level: {student.risk_level}

Course Scores (out of 100):
- Mathematics: {student.math_marks}
- Programming / Python: {student.programming_marks}
- Data Structures: {student.data_structures_marks}
- Database Systems: {student.database_marks}
- Machine Learning: {student.machine_learning_marks}

Return a valid JSON object strictly matching this JSON schema:
{{
  "overall_summary": "Comprehensive 2-3 sentence academic overview analyzing performance and trajectory.",
  "strong_subjects": ["List of subjects where student scored well (>= 75)"],
  "weak_subjects": [
    {{
      "subject": "Subject name",
      "score": 45.0,
      "gap": 30.0,
      "priority_topics": ["Specific curriculum topic 1", "Specific curriculum topic 2"]
    }}
  ],
  "personalized_advice": "Actionable, motivating study habit advice tailored to this student.",
  "recommended_weekly_hours": 12,
  "study_plan": [
    {{
      "day_of_week": "Monday",
      "topic": "Focused topic name",
      "activity": "Specific practical task (e.g., solve 5 binary tree problems)",
      "estimated_minutes": 60
    }},
    {{
      "day_of_week": "Tuesday",
      "topic": "...",
      "activity": "...",
      "estimated_minutes": 45
    }},
    {{
      "day_of_week": "Wednesday",
      "topic": "...",
      "activity": "...",
      "estimated_minutes": 60
    }},
    {{
      "day_of_week": "Thursday",
      "topic": "...",
      "activity": "...",
      "estimated_minutes": 45
    }},
    {{
      "day_of_week": "Friday",
      "topic": "...",
      "activity": "...",
      "estimated_minutes": 45
    }}
  ]
}}
DO NOT wrap in markdown formatting. Return raw JSON only.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        raw_text = response.text
        if not raw_text:
            return None

        # Clean any accidental markdown code fences
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        data = json.loads(clean_text)

        # Validate with Pydantic
        analysis = AIPerformanceAnalysis(
            overall_summary=data["overall_summary"],
            strong_subjects=data.get("strong_subjects", []),
            weak_subjects=[WeakSubjectDetail(**w) for w in data.get("weak_subjects", [])],
            personalized_advice=data.get("personalized_advice", "Review weak topics consistently."),
            recommended_weekly_hours=int(data.get("recommended_weekly_hours", 10))
        )

        study_plan_items = [
            StudyPlanItemCreate(
                day_of_week=item["day_of_week"],
                topic=item["topic"],
                activity=item["activity"],
                estimated_minutes=int(item.get("estimated_minutes", 45))
            )
            for item in data.get("study_plan", [])
        ]

        return analysis, study_plan_items

    except Exception as e:
        logger.warning(f"Gemini API invocation failed ({str(e)}). Falling back to deterministic engine.")
        return None


def generate_and_save_ai_analysis(db: Session, student: Student) -> FullAIAnalysisResponse:
    """
    Executes AI analysis for a student (via Gemini API with automatic fallback),
    persists recommendations and study plan items to the database, and returns the response.
    """
    source = "gemini_api"
    api_result = _call_gemini_api(student)

    if api_result:
        analysis, plan_items = api_result
    else:
        source = "resilient_fallback"
        analysis, plan_items = _deterministic_pedagogical_analysis(student)

    # 1. Persist to AIRecommendation table
    weak_str = ", ".join([f"{w.subject} ({w.score})" for w in analysis.weak_subjects])
    strong_str = ", ".join(analysis.strong_subjects)
    topics_str = json.dumps({w.subject: w.priority_topics for w in analysis.weak_subjects})

    recommendation = AIRecommendation(
        student_id=student.student_id,
        overall_summary=analysis.overall_summary,
        strong_subjects=strong_str,
        weak_subjects=weak_str,
        recommended_topics=topics_str,
        actionable_plan=analysis.personalized_advice,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(recommendation)

    # 2. Persist new StudyPlan
    # Deactivate existing active study plans for this student
    existing_plans = db.query(StudyPlan).filter(
        StudyPlan.student_id == student.student_id,
        StudyPlan.status == "active"
    ).all()
    for p in existing_plans:
        p.status = "archived"

    focus_sub = analysis.weak_subjects[0].subject if analysis.weak_subjects else "General Revision"
    new_plan = StudyPlan(
        student_id=student.student_id,
        week_number=1,
        title=f"Weekly Roadmap: Targeted {focus_sub} Improvement",
        focus_subject=focus_sub,
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_plan)
    db.flush()  # Obtain new_plan.id

    for item in plan_items:
        plan_item = StudyPlanItem(
            study_plan_id=new_plan.id,
            day_of_week=item.day_of_week,
            topic=item.topic,
            activity=item.activity,
            estimated_minutes=item.estimated_minutes,
            is_completed=False
        )
        db.add(plan_item)

    db.commit()
    db.refresh(new_plan)

    return FullAIAnalysisResponse(
        student_id=student.student_id,
        name=student.name,
        analysis=analysis,
        study_plan_id=new_plan.id,
        study_plan_items_count=len(plan_items),
        source=source
    )
