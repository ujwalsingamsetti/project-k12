# K12 Answer Sheet Evaluator - Project Documentation

## 1. Core Planning Documents

### 1.1 Project Charter
*   **Purpose:** To automate and streamline the evaluation of K12 handwritten answer sheets using OCR and AI, reducing educator workload and providing rapid, detailed feedback to students.
*   **Objectives:** 
    *   Achieve an AI grading accuracy comparable to human teachers.
    *   Reduce evaluation time per paper from minutes to seconds.
    *   Provide a robust RAG (Retrieval-Augmented Generation) system to anchor AI evaluations to specific textbook curricula.
*   **Scope:** The system covers teacher assignment creation, student answer submission (image/PDF uploads), AI-driven evaluation using Google Cloud Vision and Gemini AI, report card generation, and real-time notifications.
*   **Stakeholders:**
    *   **Teachers/Educators:** End-users creating papers and reviewing AI grades.
    *   **Students:** End-users submitting answers and reviewing performance.
    *   **School Administrators:** Overseeing system usage and metrics.
*   **High-Level Risks:**
    *   *Risk:* Inaccurate OCR extraction due to poor student handwriting.
    *   *Risk:* AI hallucinations or incorrect grading penalizing students.
    *   *Mitigation:* Mandatory teacher review overrides; robust RAG context injection.

### 1.2 Requirements Specification
*   **Functional:**
    *   Teachers can upload textbooks to build a vector knowledge base.
    *   Students can submit images of physical answer sheets.
    *   System automatically detects questions, handwriting, and diagrams.
    *   System matches answers against the answer key and textbook data.
    *   System generates PDF report cards and Leaderboards.
*   **Non-Functional:**
    *   High availability, real-time sync (polling/websockets), low latency for the UI.
    *   Secure JWT authentication and role-based access control (RBAC).

---

## 2. Technical Specifications

### 2.1 System Architecture
*   **Client-Server Model:** Frontend built in React communicating with a Python FastAPI backend via REST APIs.
*   **Asynchronous Processing:** Heavy AI/OCR tasks are offloaded to FastAPI `BackgroundTasks` to avoid blocking the HTTP request thread.
*   **RAG Architecture:** Textbooks are parsed (`PyMuPDF`), chunked, embedded (`sentence-transformers`), and stored in Qdrant. Context is retrieved dynamically during answer evaluation.

### 2.2 Technology Stack & Dependencies
*   **Backend:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, Alembic.
*   **AI/ML:** Google Cloud Vision, Gemini API (`google-genai`), Qdrant, LangChain.
*   **Frontend:** React 19, Tailwind CSS, Vite, React Router v7, Axios.

### 2.3 Data Design & Database Schema Operations
*   **Users:** Stores `id`, `email`, `role` (Teacher/Student), `full_name`, `grade`.
*   **Textbooks:** Stores metadata and file paths for RAG vector embeddings.
*   **QuestionPapers / Questions:** Relational storage for paper structures, answer keys, and max marks.
*   **AnswerSubmissions / Evaluations:** Tracks student upload statuses, total marks, and granular per-question evaluations.
*   **Notifications:** polymorphic target tracking (unread, read, clears).

### 2.4 Code Structure Overview
```text
k12-answer-evaluator/
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI Controllers (routers)
│   │   ├── core/               # App config, DB session, security logic
│   │   ├── models/             # SQLAlchemy DB schemas
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Heavy lifting (OCR, Evaluator AI, RAG ingestion)
│   │   └── main.py             # FastAPI App definition
├── frontend/
│   ├── src/
│   │   ├── components/         # React Views (Auth, Teacher UI, Student UI)
│   │   ├── context/            # Global States (Auth, Theme, Notifications)
│   │   ├── services/           # API handlers (Axios interface)
```

---

## 3. Usage and Deployment Guides

### 3.1 Setup / Installation Steps
1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-org/project-k12.git
    cd project-k12
    ```
2.  **Backend Setup:**
    ```bash
    cd k12-answer-evaluator/backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Environment Variables (`backend/.env`):**
    Ensure you specify `DATABASE_URL`, `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, and `SECRET_KEY`.
4.  **Database Migrations:**
    ```bash
    alembic upgrade head
    ```
5.  **Frontend Setup:**
    ```bash
    cd ../../frontend
    npm install
    ```

### 3.2 Running the Application
*   **Start Backend:** `uvicorn app.main:app --reload` (Runs on port 8000)
*   **Start Frontend:** `npm run dev` (Runs on port 5173/5174)

### 3.3 Quick Start Tutorial & End-User Workflow
1.  **Teacher Setup:** Sign up as a Teacher, navigate to "Add Textbook" and upload a reference PDF. Then, create a new Question Paper.
2.  **Student Action:** Sign up as a Student. Go to Dashboard -> Profiles to specify your Grade. Then navigate to Assessments and upload an Answer Sheet image.
3.  **Completion:** The teacher logs in, reviews the auto-graded sheet, makes overrides if necessary. The student downloads the PDF Report.

### 3.4 Troubleshooting FAQs
*   **Q:** Why is the AI taking 20+ seconds to evaluate? 
    *   **A:** Network latency with Gemini API. Heavy OCR extractions inherently take time. It runs in the background.
*   **Q:** Why is Enum data corrupting operations?
    *   **A:** Ensure PostgreSQL DB Enum cases match Python schemas exactly (we force everything to lowercase).

---

## 4. API Documentation
*Full reference of REST endpoints:*

*   `/api/auth/register` (POST) - Account creation
*   `/api/auth/login` (POST) - Token retrieval
*   `/api/auth/profile` (PATCH) - Update user data (Name, Grade)
*   `/api/teacher/papers` (GET, POST, PUT, DELETE) - Paper CRUD
*   `/api/teacher/papers/from-image` (POST) - OCR/AI Paper generation
*   `/api/teacher/extract-questions` (POST) - Test OCR parsing
*   `/api/student/papers` (GET) - View assigned papers
*   `/api/student/submit/{paper_id}` (POST) - File upload & eval trigger
*   `/api/v2/notifications` (GET, PATCH, DELETE) - Real-time alerts
*   `/api/v2/papers/{id}/leaderboard` (GET) - Rank listings
*   `/api/v2/submissions/{id}/report` (GET) - PDF stream

---

## 5. Maintenance Essentials

*   **Contribution Guidelines:** All contributors must branch from `main`, use standard commit messages (`feat:`, `fix:`, `docs:`), and submit a Pull Request.
*   **License:** MIT License.
*   **Documentation Linkage:**
    *   [README.md](./README.md) - Quick Overview.
    *   [CHANGELOG.md](./CHANGELOG.md) - Tracked version changes.
    *   [TEST_PLAN.md](./TEST_PLAN.md) - Testing QA strategies.
    *   **Risk Register:** Kept internally by the project manager.
