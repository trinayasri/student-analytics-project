"""
seed_data.py - Demonstration / Sample Data Populator

NOTE: ALL DATA GENERATED IN THIS SCRIPT IS ENTIRELY SYNTHETIC AND LABELED
EXCLUSIVELY AS DEMONSTRATION DATA FOR TESTING AND PROJECT PRESENTATION.
NO REAL STUDENT INFORMATION IS USED.

Usage:
    python seed_data.py
    python seed_data.py --reset
"""

import sys
from app.database import SessionLocal, Base, engine
from app.models import Student, User, Subject, Teacher
from app import crud
from app.schemas import StudentCreate, UserCreate

DEMONSTRATION_USERS = [
    {
        "username": "admin",
        "email": "admin@university.edu",
        "password": "Admin@123",
        "role": "admin"
    },
    {
        "username": "teacher",
        "email": "teacher@university.edu",
        "password": "Teacher@123",
        "role": "teacher"
    },
    {
        "username": "student",
        "email": "student@university.edu",
        "password": "Student@123",
        "role": "student"
    }
]

DEMONSTRATION_SUBJECTS = [
    {"code": "MATH301", "name": "Mathematics", "department": "General Engineering", "semester": 3, "credits": 4, "min_pass_marks": 40.0},
    {"code": "PROG101", "name": "Programming / Python", "department": "Computer Science & Engineering", "semester": 1, "credits": 4, "min_pass_marks": 40.0},
    {"code": "DSA201", "name": "Data Structures & Algorithms", "department": "Computer Science & Engineering", "semester": 3, "credits": 4, "min_pass_marks": 40.0},
    {"code": "DBMS301", "name": "Database Management Systems", "department": "Information Technology", "semester": 4, "credits": 3, "min_pass_marks": 40.0},
    {"code": "ML401", "name": "Machine Learning", "department": "Artificial Intelligence & Machine Learning", "semester": 5, "credits": 4, "min_pass_marks": 40.0},
]

DEMONSTRATION_STUDENTS = [
    # Top Performers (AI & ML)
    {
        "student_id": "STU1001",
        "name": "Aarav Sharma (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "aarav.sharma.demo@university.edu",
        "math_marks": 95.0,
        "programming_marks": 98.0,
        "data_structures_marks": 92.0,
        "database_marks": 90.0,
        "machine_learning_marks": 96.0,
        "attendance_percentage": 94.5,
    },
    {
        "student_id": "STU1002",
        "name": "Priya Patel (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "priya.patel.demo@university.edu",
        "math_marks": 88.0,
        "programming_marks": 92.0,
        "data_structures_marks": 85.0,
        "database_marks": 89.0,
        "machine_learning_marks": 94.0,
        "attendance_percentage": 91.0,
    },
    {
        "student_id": "STU1003",
        "name": "Rohan Verma (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "rohan.verma.demo@university.edu",
        "math_marks": 82.0,
        "programming_marks": 85.0,
        "data_structures_marks": 80.0,
        "database_marks": 84.0,
        "machine_learning_marks": 78.0,
        "attendance_percentage": 87.0,
    },
    {
        "student_id": "STU1004",
        "name": "Ananya Iyer (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "ananya.iyer.demo@university.edu",
        "math_marks": 91.0,
        "programming_marks": 94.0,
        "data_structures_marks": 89.0,
        "database_marks": 92.0,
        "machine_learning_marks": 88.0,
        "attendance_percentage": 96.0,
    },
    {
        "student_id": "STU1005",
        "name": "Kavya Reddy (Demo)",
        "department": "Data Science",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "kavya.reddy.demo@university.edu",
        "math_marks": 79.0,
        "programming_marks": 83.0,
        "data_structures_marks": 75.0,
        "database_marks": 80.0,
        "machine_learning_marks": 86.0,
        "attendance_percentage": 82.0,
    },
    {
        "student_id": "STU1006",
        "name": "Aditya Nair (Demo)",
        "department": "Data Science",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "aditya.nair.demo@university.edu",
        "math_marks": 74.0,
        "programming_marks": 78.0,
        "data_structures_marks": 72.0,
        "database_marks": 76.0,
        "machine_learning_marks": 81.0,
        "attendance_percentage": 79.0,
    },
    {
        "student_id": "STU1007",
        "name": "Sneha Kulkarni (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "academic_year": "2023-2024",
        "email": "sneha.kulkarni.demo@university.edu",
        "math_marks": 68.0,
        "programming_marks": 72.0,
        "data_structures_marks": 65.0,
        "database_marks": 74.0,
        "machine_learning_marks": 67.0,
        "attendance_percentage": 83.0,
    },
    {
        "student_id": "STU1008",
        "name": "Vikram Singh (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "academic_year": "2023-2024",
        "email": "vikram.singh.demo@university.edu",
        "math_marks": 62.0,
        "programming_marks": 66.0,
        "data_structures_marks": 60.0,
        "database_marks": 65.0,
        "machine_learning_marks": 63.0,
        "attendance_percentage": 71.0,  # Needs Attention on attendance
    },
    {
        "student_id": "STU1009",
        "name": "Meera Joshi (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "academic_year": "2024-2025",
        "email": "meera.joshi.demo@university.edu",
        "math_marks": 76.0,
        "programming_marks": 70.0,
        "data_structures_marks": 68.0,
        "database_marks": 65.0,
        "machine_learning_marks": 62.0,
        "attendance_percentage": 80.0,
    },
    {
        "student_id": "STU1010",
        "name": "Arjun Das (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "academic_year": "2024-2025",
        "email": "arjun.das.demo@university.edu",
        "math_marks": 71.0,
        "programming_marks": 64.0,
        "data_structures_marks": 62.0,
        "database_marks": 60.0,
        "machine_learning_marks": 58.0,
        "attendance_percentage": 76.0,
    },
    # At-Risk Student 1: Low average (< 50%) and Failed subject (< 40)
    {
        "student_id": "STU1011",
        "name": "Rahul Deshmukh (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "rahul.deshmukh.demo@university.edu",
        "math_marks": 42.0,
        "programming_marks": 45.0,
        "data_structures_marks": 38.0,  # Failed subject (< 40)
        "database_marks": 48.0,
        "machine_learning_marks": 40.0,
        "attendance_percentage": 62.0,  # Low attendance (< 65) -> At Risk
    },
    # At-Risk Student 2: Failed subject despite moderate other scores
    {
        "student_id": "STU1012",
        "name": "Divya Menon (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "divya.menon.demo@university.edu",
        "math_marks": 34.0,  # Failed Math (< 40)
        "programming_marks": 70.0,
        "data_structures_marks": 65.0,
        "database_marks": 68.0,
        "machine_learning_marks": 62.0,
        "attendance_percentage": 74.0,  # Needs Attention
    },
    # Additional Diverse Students
    {
        "student_id": "STU1013",
        "name": "Manish Gupta (Demo)",
        "department": "Data Science",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "manish.gupta.demo@university.edu",
        "math_marks": 85.0,
        "programming_marks": 89.0,
        "data_structures_marks": 82.0,
        "database_marks": 88.0,
        "machine_learning_marks": 90.0,
        "attendance_percentage": 88.0,
    },
    {
        "student_id": "STU1014",
        "name": "Pooja Hegde (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "academic_year": "2023-2024",
        "email": "pooja.hegde.demo@university.edu",
        "math_marks": 55.0,
        "programming_marks": 58.0,
        "data_structures_marks": 52.0,
        "database_marks": 56.0,
        "machine_learning_marks": 54.0,
        "attendance_percentage": 69.0,  # Needs Attention
    },
    {
        "student_id": "STU1015",
        "name": "Nikhil Chawla (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "academic_year": "2024-2025",
        "email": "nikhil.chawla.demo@university.edu",
        "math_marks": 58.0,
        "programming_marks": 54.0,
        "data_structures_marks": 50.0,
        "database_marks": 52.0,
        "machine_learning_marks": 48.0,
        "attendance_percentage": 72.0,
    },
    # At-Risk Student 3: Multi-subject failure & critical attendance
    {
        "student_id": "STU1016",
        "name": "Siddharth Roy (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "academic_year": "2023-2024",
        "email": "siddharth.roy.demo@university.edu",
        "math_marks": 35.0,  # Failed Math
        "programming_marks": 38.0,  # Failed Programming
        "data_structures_marks": 42.0,
        "database_marks": 44.0,
        "machine_learning_marks": 36.0,  # Failed ML
        "attendance_percentage": 58.0,  # Critical attendance
    },
    {
        "student_id": "STU1017",
        "name": "Tanvi Kapoor (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "tanvi.kapoor.demo@university.edu",
        "math_marks": 96.0,
        "programming_marks": 95.0,
        "data_structures_marks": 94.0,
        "database_marks": 92.0,
        "machine_learning_marks": 97.0,
        "attendance_percentage": 98.0,
    },
    {
        "student_id": "STU1018",
        "name": "Karthik Pillai (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "karthik.pillai.demo@university.edu",
        "math_marks": 78.0,
        "programming_marks": 82.0,
        "data_structures_marks": 76.0,
        "database_marks": 80.0,
        "machine_learning_marks": 84.0,
        "attendance_percentage": 84.0,
    },
    {
        "student_id": "STU1019",
        "name": "Ishaan Saxena (Demo)",
        "department": "Data Science",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "ishaan.saxena.demo@university.edu",
        "math_marks": 64.0,
        "programming_marks": 70.0,
        "data_structures_marks": 61.0,
        "database_marks": 66.0,
        "machine_learning_marks": 68.0,
        "attendance_percentage": 78.0,
    },
    {
        "student_id": "STU1020",
        "name": "Ritu Sengupta (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "academic_year": "2024-2025",
        "email": "ritu.sengupta.demo@university.edu",
        "math_marks": 83.0,
        "programming_marks": 81.0,
        "data_structures_marks": 79.0,
        "database_marks": 82.0,
        "machine_learning_marks": 77.0,
        "attendance_percentage": 86.0,
    }
]


def seed_database(reset: bool = False):
    """Inserts demonstration records into the database."""
    print("=" * 70)
    print("STUDENT PERFORMANCE ANALYTICS PLATFORM - SEEDER")
    print("NOTE: All records below are synthetic demonstration data for testing.")
    print("=" * 70)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset:
            print("[INFO] Reset flag detected: recreating all tables with updated schema...")
            db.close()
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()

        # Seed Users
        print("[INFO] Seeding default authentication accounts...")
        for u in DEMONSTRATION_USERS:
            if not crud.get_user_by_username(db, u["username"]):
                crud.create_user(db, UserCreate(**u))
                print(f"  + Created user: {u['username']} ({u['role']})")

        # Seed Subjects
        print("[INFO] Seeding curriculum subjects...")
        for s in DEMONSTRATION_SUBJECTS:
            if not db.query(Subject).filter(Subject.code == s["code"]).first():
                db_subj = Subject(**s)
                db.add(db_subj)
        db.commit()

        # Seed Students
        print("[INFO] Seeding student records...")
        inserted_count = 0
        skipped_count = 0

        for item in DEMONSTRATION_STUDENTS:
            existing = crud.get_student_by_student_id(db, item["student_id"])
            if existing:
                skipped_count += 1
                continue

            student_schema = StudentCreate(**item)
            new_student = crud.create_student(db, student_schema)
            inserted_count += 1

            # Link STU1001 to student user demo account if available
            if item["student_id"] == "STU1001":
                stu_user = crud.get_user_by_username(db, "student")
                if stu_user and not stu_user.student_profile:
                    new_student.user_id = stu_user.id
                    db.commit()

        print(f"[SUCCESS] Seeding completed!")
        print(f"  - Users count: {db.query(User).count()}")
        print(f"  - Subjects count: {db.query(Subject).count()}")
        print(f"  - Newly inserted students: {inserted_count}")
        print(f"  - Skipped students: {skipped_count}")
        print(f"  - Total students in DB: {db.query(Student).count()}")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    reset_db = "--reset" in sys.argv
    seed_database(reset=reset_db)
