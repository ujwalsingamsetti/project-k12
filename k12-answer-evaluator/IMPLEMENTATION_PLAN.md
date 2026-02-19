# K12 Answer Sheet Evaluator - Complete Implementation Plan

## 🎯 Project Overview
Full-featured answer sheet evaluation system with Teacher/Student roles, question paper management, and automated grading.

---

## 📊 Database Schema (PostgreSQL)

### Tables:

1. **users**
   - id (UUID, PK)
   - email (unique)
   - password_hash
   - full_name
   - role (teacher/student)
   - created_at
   - updated_at

2. **question_papers**
   - id (UUID, PK)
   - teacher_id (FK -> users)
   - title
   - subject (science/mathematics)
   - class_level (12)
   - total_marks
   - duration_minutes
   - instructions (text)
   - created_at
   - due_date

3. **questions**
   - id (UUID, PK)
   - paper_id (FK -> question_papers)
   - question_number
   - question_text
   - question_type (short/long)
   - marks
   - expected_keywords (JSON array)

4. **answer_submissions**
   - id (UUID, PK)
   - paper_id (FK -> question_papers)
   - student_id (FK -> users)
   - image_path
   - extracted_text (text)
   - submitted_at
   - status (pending/evaluated/failed)

5. **evaluations**
   - id (UUID, PK)
   - submission_id (FK -> answer_submissions)
   - question_id (FK -> questions)
   - student_answer (text)
   - marks_obtained
   - max_marks
   - feedback (text)
   - rag_context (text)
   - evaluated_at

---

## 🏗️ Clean Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Login, register, JWT
│   │   ├── teachers.py      # Teacher endpoints
│   │   ├── students.py      # Student endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings
│   │   ├── security.py      # Password hashing, JWT
│   │   └── database.py      # PostgreSQL connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── question_paper.py
│   │   ├── question.py
│   │   ├── submission.py
│   │   └── evaluation.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py          # Pydantic models
│   │   ├── question_paper.py
│   │   ├── submission.py
│   │   └── evaluation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py   # Google Vision OCR
│   │   ├── rag_service.py   # Qdrant RAG
│   │   ├── evaluation_service.py  # LLM evaluation
│   │   └── answer_parser.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── question_paper.py
│   │   ├── submission.py
│   │   └── evaluation.py
│   └── main.py
├── alembic/                 # Database migrations
├── data/
│   ├── uploads/
│   ├── question_papers/
│   └── textbooks/
├── .env
├── requirements.txt
└── README.md

frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── teacher/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── CreatePaper.jsx
│   │   │   ├── ViewSubmissions.jsx
│   │   │   └── StudentResults.jsx
│   │   ├── student/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AvailablePapers.jsx
│   │   │   ├── SubmitAnswer.jsx
│   │   │   └── MyResults.jsx
│   │   └── common/
│   │       ├── Navbar.jsx
│   │       └── ProtectedRoute.jsx
│   ├── services/
│   │   └── api.js           # Axios API calls
│   ├── context/
│   │   └── AuthContext.jsx
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```

---

## 🔄 Implementation Steps

### STEP 1: PostgreSQL Setup (30 min)
```bash
# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb k12_evaluator

# Install Python packages
pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt]
```

### STEP 2: Database Models & Migrations (1 hour)
- Create SQLAlchemy models
- Setup Alembic migrations
- Create initial migration
- Run migrations

### STEP 3: Authentication System (1 hour)
- JWT token generation
- Password hashing
- Login/Register endpoints
- Role-based access control

### STEP 4: Teacher APIs (2 hours)
- Create question paper
- Add questions to paper
- View all submissions
- View student results dashboard

### STEP 5: Student APIs (1 hour)
- View available papers
- Submit answer sheet
- View my results

### STEP 6: Evaluation Pipeline Integration (1 hour)
- Connect OCR service
- Connect RAG service
- Connect LLM evaluation
- Store results in PostgreSQL

### STEP 7: Frontend Setup (1 hour)
- React + Vite setup
- Tailwind CSS
- React Router
- Axios setup

### STEP 8: Frontend - Auth Pages (1 hour)
- Login page
- Register page
- Auth context
- Protected routes

### STEP 9: Frontend - Teacher Dashboard (3 hours)
- Dashboard overview
- Create question paper form
- View submissions table
- Student results charts

### STEP 10: Frontend - Student Dashboard (2 hours)
- Available papers list
- Submit answer form
- My results page

### STEP 11: Testing & Deployment (2 hours)
- End-to-end testing
- Bug fixes
- Deployment preparation

---

## 📦 Required Packages

### Backend:
```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
alembic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
pydantic
pydantic-settings
google-cloud-vision
pyspellchecker
opencv-python
qdrant-client
sentence-transformers
openai
```

### Frontend:
```
react
react-router-dom
axios
tailwindcss
recharts (for charts)
react-hot-toast (notifications)
```

---

## 🎨 UI Features

### Teacher Dashboard:
- 📊 Overview: Total papers, submissions, average scores
- ➕ Create Paper: Form with questions, marks allocation
- 📝 Submissions: Table with student name, status, score
- 📈 Analytics: Charts showing class performance

### Student Dashboard:
- 📚 Available Papers: Cards showing paper details
- 📤 Submit Answer: Upload image, preview
- 🎯 My Results: List of evaluated papers with scores

---

## 🚀 Ready to Start?

I'll implement this step by step. Let me know when you're ready and I'll start with:

**STEP 1: PostgreSQL Setup + Database Models**

Type "start" and I'll begin!
