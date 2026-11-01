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
from app.models import Student
from app import crud
from app.schemas import StudentCreate

DEMONSTRATION_STUDENTS = [
    # Top Performers (AI & ML)
    {
        "student_id": "STU1001",
        "name": "Aarav Sharma (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "email": "aarav.sharma.demo@university.edu",
        "math_marks": 95.0,
        "programming_marks": 98.0,
        "data_structures_marks": 92.0,
        "database_marks": 90.0,
        "machine_learning_marks": 96.0,
    },
    {
        "student_id": "STU1002",
        "name": "Priya Patel (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "email": "priya.patel.demo@university.edu",
        "math_marks": 88.0,
        "programming_marks": 92.0,
        "data_structures_marks": 85.0,
        "database_marks": 89.0,
        "machine_learning_marks": 94.0,
    },
    {
        "student_id": "STU1003",
        "name": "Rohan Verma (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "email": "rohan.verma.demo@university.edu",
        "math_marks": 82.0,
        "programming_marks": 85.0,
        "data_structures_marks": 80.0,
        "database_marks": 84.0,
        "machine_learning_marks": 78.0,
    },
    {
        "student_id": "STU1004",
        "name": "Ananya Iyer (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "email": "ananya.iyer.demo@university.edu",
        "math_marks": 91.0,
        "programming_marks": 94.0,
        "data_structures_marks": 89.0,
        "database_marks": 92.0,
        "machine_learning_marks": 88.0,
    },
    {
        "student_id": "STU1005",
        "name": "Kavya Reddy (Demo)",
        "department": "Data Science",
        "semester": 6,
        "email": "kavya.reddy.demo@university.edu",
        "math_marks": 79.0,
        "programming_marks": 83.0,
        "data_structures_marks": 75.0,
        "database_marks": 80.0,
        "machine_learning_marks": 86.0,
    },
    {
        "student_id": "STU1006",
        "name": "Aditya Nair (Demo)",
        "department": "Data Science",
        "semester": 6,
        "email": "aditya.nair.demo@university.edu",
        "math_marks": 74.0,
        "programming_marks": 78.0,
        "data_structures_marks": 72.0,
        "database_marks": 76.0,
        "machine_learning_marks": 81.0,
    },
    {
        "student_id": "STU1007",
        "name": "Sneha Kulkarni (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "email": "sneha.kulkarni.demo@university.edu",
        "math_marks": 68.0,
        "programming_marks": 72.0,
        "data_structures_marks": 65.0,
        "database_marks": 74.0,
        "machine_learning_marks": 67.0,
    },
    {
        "student_id": "STU1008",
        "name": "Vikram Singh (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "email": "vikram.singh.demo@university.edu",
        "math_marks": 62.0,
        "programming_marks": 66.0,
        "data_structures_marks": 60.0,
        "database_marks": 65.0,
        "machine_learning_marks": 63.0,
    },
    {
        "student_id": "STU1009",
        "name": "Meera Joshi (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "email": "meera.joshi.demo@university.edu",
        "math_marks": 76.0,
        "programming_marks": 70.0,
        "data_structures_marks": 68.0,
        "database_marks": 65.0,
        "machine_learning_marks": 62.0,
    },
    {
        "student_id": "STU1010",
        "name": "Arjun Das (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "email": "arjun.das.demo@university.edu",
        "math_marks": 71.0,
        "programming_marks": 64.0,
        "data_structures_marks": 62.0,
        "database_marks": 60.0,
        "machine_learning_marks": 58.0,
    },
    # At-Risk Student 1: Low average (< 50%)
    {
        "student_id": "STU1011",
        "name": "Rahul Deshmukh (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "email": "rahul.deshmukh.demo@university.edu",
        "math_marks": 42.0,
        "programming_marks": 45.0,
        "data_structures_marks": 38.0,  # Failed subject (< 40)
        "database_marks": 48.0,
        "machine_learning_marks": 40.0,
    },
    # At-Risk Student 2: Failed subject despite moderate other scores
    {
        "student_id": "STU1012",
        "name": "Divya Menon (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "email": "divya.menon.demo@university.edu",
        "math_marks": 34.0,  # Failed Math (< 40)
        "programming_marks": 70.0,
        "data_structures_marks": 65.0,
        "database_marks": 68.0,
        "machine_learning_marks": 62.0,
    },
    # Additional Diverse Students
    {
        "student_id": "STU1013",
        "name": "Manish Gupta (Demo)",
        "department": "Data Science",
        "semester": 6,
        "email": "manish.gupta.demo@university.edu",
        "math_marks": 85.0,
        "programming_marks": 89.0,
        "data_structures_marks": 82.0,
        "database_marks": 88.0,
        "machine_learning_marks": 90.0,
    },
    {
        "student_id": "STU1014",
        "name": "Pooja Hegde (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "email": "pooja.hegde.demo@university.edu",
        "math_marks": 55.0,
        "programming_marks": 58.0,
        "data_structures_marks": 52.0,
        "database_marks": 56.0,
        "machine_learning_marks": 54.0,
    },
    {
        "student_id": "STU1015",
        "name": "Nikhil Chawla (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "email": "nikhil.chawla.demo@university.edu",
        "math_marks": 58.0,
        "programming_marks": 54.0,
        "data_structures_marks": 50.0,
        "database_marks": 52.0,
        "machine_learning_marks": 48.0,
    },
    # At-Risk Student 3
    {
        "student_id": "STU1016",
        "name": "Siddharth Roy (Demo)",
        "department": "Information Technology",
        "semester": 5,
        "email": "siddharth.roy.demo@university.edu",
        "math_marks": 35.0,  # Failed Math
        "programming_marks": 38.0,  # Failed Programming
        "data_structures_marks": 42.0,
        "database_marks": 44.0,
        "machine_learning_marks": 36.0,  # Failed ML
    },
    {
        "student_id": "STU1017",
        "name": "Tanvi Kapoor (Demo)",
        "department": "Computer Science & Engineering",
        "semester": 4,
        "email": "tanvi.kapoor.demo@university.edu",
        "math_marks": 96.0,
        "programming_marks": 95.0,
        "data_structures_marks": 94.0,
        "database_marks": 92.0,
        "machine_learning_marks": 97.0,
    },
    {
        "student_id": "STU1018",
        "name": "Karthik Pillai (Demo)",
        "department": "Artificial Intelligence & Machine Learning",
        "semester": 6,
        "email": "karthik.pillai.demo@university.edu",
        "math_marks": 78.0,
        "programming_marks": 82.0,
        "data_structures_marks": 76.0,
        "database_marks": 80.0,
        "machine_learning_marks": 84.0,
    },
    {
        "student_id": "STU1019",
        "name": "Ishaan Saxena (Demo)",
        "department": "Data Science",
        "semester": 6,
        "email": "ishaan.saxena.demo@university.edu",
        "math_marks": 64.0,
        "programming_marks": 70.0,
        "data_structures_marks": 61.0,
        "database_marks": 66.0,
        "machine_learning_marks": 68.0,
    },
    {
        "student_id": "STU1020",
        "name": "Ritu Sengupta (Demo)",
        "department": "Electronics & Communication",
        "semester": 3,
        "email": "ritu.sengupta.demo@university.edu",
        "math_marks": 83.0,
        "programming_marks": 81.0,
        "data_structures_marks": 79.0,
        "database_marks": 82.0,
        "machine_learning_marks": 77.0,
    }
]


def seed_database(reset: bool = False):
    """Inserts demonstration records into the SQLite database."""
    print("=" * 70)
    print("STUDENT PERFORMANCE ANALYTICS SYSTEM - DEMONSTRATION DATA SEEDER")
    print("NOTE: All records below are synthetic demonstration data for testing.")
    print("=" * 70)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset:
            print("[INFO] Reset flag detected: clearing existing student records...")
            db.query(Student).delete()
            db.commit()

        inserted_count = 0
        skipped_count = 0

        for item in DEMONSTRATION_STUDENTS:
            existing = crud.get_student_by_student_id(db, item["student_id"])
            if existing:
                skipped_count += 1
                continue

            student_schema = StudentCreate(**item)
            crud.create_student(db, student_schema)
            inserted_count += 1

        print(f"[SUCCESS] Demonstration seeding completed!")
        print(f"  - Newly inserted records: {inserted_count}")
        print(f"  - Skipped (already existed): {skipped_count}")
        print(f"  - Total records in database: {db.query(Student).count()}")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    reset_db = "--reset" in sys.argv
    seed_database(reset=reset_db)
