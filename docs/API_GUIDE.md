# REST API Specification & Consumer Guide

## 1. Overview & Base Endpoints

- **Base Service URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Technical Specification**: `http://127.0.0.1:8000/redoc`

All API endpoints return JSON responses and adhere strictly to semantic HTTP status codes.

---

## 2. API Endpoints Directory

| HTTP Method | Endpoint URI | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Check API & database health status | `200 OK` |
| `POST` | `/api/students/` | Create a new student record | `201 Created` |
| `GET` | `/api/students/` | List students with pagination, search & filters | `200 OK` |
| `GET` | `/api/students/departments` | Get distinct active department names | `200 OK` |
| `GET` | `/api/students/{identifier}` | Retrieve single student by ID or `student_id` | `200 OK` |
| `PUT` | `/api/students/{identifier}` | Update student details or subject marks | `200 OK` |
| `DELETE` | `/api/students/{identifier}` | Permanently delete a student record | `200 OK` |
| `GET` | `/api/analytics/summary` | Overall institutional performance KPIs | `200 OK` |
| `GET` | `/api/analytics/departments` | Aggregated department performance statistics | `200 OK` |
| `GET` | `/api/analytics/grade-distribution`| Student counts and percentages per letter grade | `200 OK` |
| `GET` | `/api/analytics/subject-averages` | Mean, max, and min performance per subject | `200 OK` |
| `GET` | `/api/analytics/at-risk` | List of students requiring academic intervention | `200 OK` |

---

## 3. Detailed Endpoint Documentation & Payloads

### 3.1 Create Student Record
- **Method**: `POST`
- **URL**: `/api/students/`
- **Headers**: `Content-Type: application/json`

**Sample Request Payload**:
```json
{
  "student_id": "STU1050",
  "name": "Kiran Rao",
  "department": "Artificial Intelligence & Machine Learning",
  "semester": 6,
  "email": "kiran.rao@university.edu",
  "math_marks": 92.0,
  "programming_marks": 95.0,
  "data_structures_marks": 88.0,
  "database_marks": 91.0,
  "machine_learning_marks": 94.0
}
```

**cURL Command**:
```bash
curl -X POST "http://127.0.0.1:8000/api/students/" \
     -H "Content-Type: application/json" \
     -d "{\"student_id\":\"STU1050\",\"name\":\"Kiran Rao\",\"department\":\"Artificial Intelligence & Machine Learning\",\"semester\":6,\"email\":\"kiran.rao@university.edu\",\"math_marks\":92.0,\"programming_marks\":95.0,\"data_structures_marks\":88.0,\"database_marks\":91.0,\"machine_learning_marks\":94.0}"
```

**Response (`201 Created`)**:
```json
{
  "id": 21,
  "student_id": "STU1050",
  "name": "Kiran Rao",
  "department": "Artificial Intelligence & Machine Learning",
  "semester": 6,
  "email": "kiran.rao@university.edu",
  "math_marks": 92.0,
  "programming_marks": 95.0,
  "data_structures_marks": 88.0,
  "database_marks": 91.0,
  "machine_learning_marks": 94.0,
  "total_marks": 460.0,
  "average_marks": 92.0,
  "percentage": 92.0,
  "grade": "A+",
  "needs_support": false,
  "created_at": "2026-10-13T14:40:00.000Z",
  "updated_at": "2026-10-13T14:40:00.000Z"
}
```

---

### 3.2 List Students with Pagination & Filters
- **Method**: `GET`
- **URL**: `/api/students/?page=1&page_size=2&department=Data%20Science`

**Response (`200 OK`)**:
```json
{
  "items": [
    {
      "id": 5,
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
      "total_marks": 403.0,
      "average_marks": 80.6,
      "percentage": 80.6,
      "grade": "A",
      "needs_support": false,
      "created_at": "2026-10-13T14:35:00.000Z",
      "updated_at": "2026-10-13T14:35:00.000Z"
    }
  ],
  "total_count": 4,
  "page": 1,
  "page_size": 2,
  "total_pages": 2
}
```

---

### 3.3 Get Academic Summary KPIs
- **Method**: `GET`
- **URL**: `/api/analytics/summary`

**Response (`200 OK`)**:
```json
{
  "total_students": 20,
  "overall_average": 71.67,
  "highest_average": 94.8,
  "lowest_average": 39.0,
  "pass_percentage": 85.0,
  "at_risk_count": 3,
  "top_performer": {
    "id": 17,
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
    "total_marks": 474.0,
    "average_marks": 94.8,
    "percentage": 94.8,
    "grade": "A+",
    "needs_support": false,
    "created_at": "2026-10-13T14:35:00.000Z",
    "updated_at": "2026-10-13T14:35:00.000Z"
  }
}
```

---

### 3.4 Get At-Risk Students
- **Method**: `GET`
- **URL**: `/api/analytics/at-risk`

**Response (`200 OK`)**:
```json
[
  {
    "id": 16,
    "student_id": "STU1016",
    "name": "Siddharth Roy (Demo)",
    "department": "Information Technology",
    "semester": 5,
    "email": "siddharth.roy.demo@university.edu",
    "math_marks": 35.0,
    "programming_marks": 38.0,
    "data_structures_marks": 42.0,
    "database_marks": 44.0,
    "machine_learning_marks": 36.0,
    "total_marks": 195.0,
    "average_marks": 39.0,
    "percentage": 39.0,
    "grade": "F",
    "needs_support": true,
    "created_at": "2026-10-13T14:35:00.000Z",
    "updated_at": "2026-10-13T14:35:00.000Z"
  }
]
```

---

## 4. HTTP Error Status Codes Reference

The API uses standardized error status codes:

- **`400 Bad Request`**: Malformed request syntax.
- **`404 Not Found`**: The requested student ID was not located in SQLite.
- **`409 Conflict`**: Attempted insertion of an existing `student_id` or `email`.
- **`422 Unprocessable Entity`**: Pydantic input validation failure (e.g., negative mark, malformed email).

**Example 409 Conflict Response**:
```json
{
  "detail": "Student ID 'STU1001' already exists in the system."
}
```

**Example 422 Validation Error Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "math_marks"],
      "msg": "Input should be less than or equal to 100",
      "type": "less_than_equal"
    }
  ]
}
```
