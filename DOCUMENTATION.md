# K12 Answer Sheet Evaluator - Project Documentation

## 1. Overview
The **K12 Answer Sheet Evaluator** is an automated educational platform that allows teachers to create question papers, digitize handwritten student answer sheets, and automatically evaluate them using OCR (Optical Character Recognition) and advanced AI models. It also offers a student portal to view assignments, submit answers, check their evaluation scores, and track their progress over time.

---

## 2. Technology Stack

### Backend
* **Language & Runtime:** Python 3.10+
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM & Migrations:** SQLAlchemy, Alembic
* **Data Validation:** Pydantic
* **Authentication:** JWT (JSON Web Tokens), `passlib`, `python-jose`
* **File Processing & Images:** `PyMuPDF`, `pdf2image`, `Pillow`, `opencv-python`
* **OCR System:** Google Cloud Vision API, Tesseract OCR (`pytesseract`), `textblob`, `pyspellchecker`
* **AI & Machine Learning:** 
  * `google-genai` (Google Gemini API for evaluation and question extraction)
  * `openai`, `langchain`, `qdrant-client` (Vector DB for textbook context RAG)
  * `sentence-transformers`
* **Rate Limiting:** `slowapi`
* **PDF Generation:** `reportlab` (for student report cards)

### Frontend
* **Language:** JavaScript (ES6+), React 19
* **Build Tool:** Vite
* **Styling:** Tailwind CSS (Modern, dynamic, glassmorphism UI)
* **Routing:** React Router v7
* **State Management:** React Context API (AuthContext, ThemeContext, ToastContext)
* **HTTP Client:** Axios
* **Icons:** `react-icons`

---

## 3. Core Features & Architecture

### Teacher Capabilities
* **Question Paper Generation:** Teachers can create question papers manually or generate them by extracting text/diagrams from uploaded PDFs or images.
* **Textbook Ingestion (RAG):** Teachers can upload reference textbooks. The content is chunked, embedded, and stored in Qdrant (Vector Database) to provide context when the AI evaluates student answers.
* **Automated Evaluation:** Scans student's uploaded answer sheets, extracts handwriting using Google Cloud Vision, matches answers against the rubric, and gives marks and feedback using Gemini AI.
* **Manual Override:** Teachers can review the AI evaluation and override the marks/feedback if necessary.
* **Analytics:** Visual dashboard summarizing class performance, question difficulty, and evaluation trends.

### Student Capabilities
* **Student Dashboard:** View available assessments, recently evaluated submissions, and a unified progress timeline.
* **Submitting Answers:** Upload photos or PDFs of handwritten answer sheets.
* **Detailed Results:** View question-by-question feedback from the AI evaluation, pinpointing mistakes and correct concepts.
* **Leaderboards:** Check the class ranking for specific papers. Name anonymization applies differently for peers.
* **Report Cards:** Download a neatly formatted PDF report card with marks, grades, and teacher feedback.
* **Profile Management:** Set personal details, including grade level (e.g., Grade 10).

### Notifications & UX
* Real-time polling architecture for Notification bell (evaluated papers, new assignments).
* Dark Mode / Light Mode theming.
* Fully responsive UI.

---

## 4. Application Workflow

The core lifecycle of an evaluation in the K12 Answer Sheet Evaluator follows these sequential steps:

### Phase 1: Preparation & Creation (Teacher)
1. **Knowledge Base Setup (Optional):** The teacher uploads relevant textbooks or reference materials (`PDF` format). The system extracts the text, creates vector embeddings using `sentence-transformers`, and stores them in Qdrant (RAG setup).
2. **Paper Generation:** The teacher creates a question paper. This can be done manually by typing questions and assigning marks, or automatically by uploading an image/PDF of a question paper and letting the Google Gemini Vision API extract the structured questions and sections.

### Phase 2: Assignment & Submission (Student)
3. **Paper Assignment:** The teacher assigns the created paper to a specific class section or directly to students.
4. **Student Portal:** Students log into their dashboard, see the newly assigned paper (and receive a notification), and can view the questions.
5. **Uploading Answers:** The student writes answers on physical paper, takes photos (or scans to PDF), and uploads them submitting the assignment.

### Phase 3: Automated AI Evaluation (System)
6. **Processing Queue:** The submission is queued as a background task.
7. **OCR & Extraction:** The system uses Google Cloud Vision to detect handwritten text on the uploaded images. It also detects diagrams and math formulas.
8. **Context Retrieval (RAG):** For each question, the system queries the Qdrant vector database to pull relevant context from the teacher's uploaded textbooks.
9. **AI Grading:** The extracted handwritten answer, the original question, the grading rubric/marks, and the retrieved context are passed to the Gemini AI model. The AI evaluates the answer, assigns marks, and generates descriptive feedback explaining what was correct and what was missed.

### Phase 4: Review & Results Feedback
10. **Teacher Review:** The teacher can view the AI's grading and feedback. If needed, the teacher can manually override the marks or adjust the feedback before finalizing the evaluation.
11. **Student Feedback:** Once evaluated, the student receives a notification. They can view a detailed breakdown of their results, question by question.
12. **Analytics & Reports:** Students can download a generated PDF Report Card. Teachers can view analytical dashboards showing the overall class performance and identify historically difficult questions.

---

## 5. API Endpoints Reference

### Base URLs
* Local Backend: `http://localhost:8000/api`
* Phase 3 V2 routes: `http://localhost:8000/api/v2`

### Authentication (`/api/auth`)
* `POST /register`: Register a new user (`teacher` or `student`).
* `POST /login`: Authenticate and return an access token.
* `GET /me`: Get current authenticated user details.
* `PATCH /profile`: Update the logged-in user's profile (e.g., full name, grade).

### Teacher Portal (`/api/teacher`)
* **Papers**
  * `POST /papers`: Create a new structured question paper.
  * `GET /papers`: List all papers created by the teacher.
  * `GET /papers/{id}`: Get specific paper details.
  * `PUT /papers/{id}`: Update an existing paper.
  * `DELETE /papers/{id}`: Delete a paper.
* **Data Extraction**
  * `POST /extract-questions`: Extract questions from uploaded images/PDFs using OCR without committing them automatically.
  * `POST /papers/from-image`: End-to-end extraction and creation of a paper.
* **Evaluation & Submissions**
  * `GET /papers/{id}/submissions`: Get all submissions for a designated paper.
  * `GET /papers/{id}/analytics`: Retrieve statistical performance data for a paper.
  * `POST /papers/{id}/assign`: Assign a paper to a specific section/grade.
* **Textbooks (Knowledge Base)**
  * `POST /textbooks`: Upload a PDF textbook to be ingested into the RAG vector store.
  * `GET /textbooks`: List uploaded reference textbooks.
  * `DELETE /textbooks/{id}`: Remove a textbook.

### Student Portal (`/api/student`)
* **Papers**
  * `GET /teachers`: Fetch list of teachers the student interacts with.
  * `GET /papers`: View available target papers.
  * `GET /papers/{id}`: View details of a specific assigned paper.
* **Submissions**
  * `POST /submit/{paper_id}`: Upload answer sheet images for a paper. Triggers background evaluation.
  * `GET /submissions`: Retrieve evaluation history for the student.
  * `GET /submissions/{id}`: Detailed evaluation result (marks, feedback, answers).
  * `GET /submissions/{id}/image`: View the originally uploaded raw image page.
* **Progress Dashboard**
  * `GET /progress`: Aggregated statistics, subject-wise trends, and timeline data for the student UI.

### Phase 3 Extensions (`/api/v2`)
* **Notifications**
  * `GET /notifications`: Get recent notifications and unread count.
  * `PATCH /notifications/{id}/read`: Mark single notification as read.
  * `PATCH /notifications/read-all`: Mark all as read.
  * `DELETE /notifications/clear`: Purge notification history.
* **Leaderboard**
  * `GET /papers/{id}/leaderboard`: Gets ranked list of students with scores.
* **Reports**
  * `GET /submissions/{id}/report`: Generates and streams PDF report card.

---

## 5. Directory Structure
```text
k12-answer-evaluator/
├── backend/
│   ├── alembic/                # Database migration scripts
│   ├── app/
│   │   ├── api/                # FastAPI Controllers (routers)
│   │   ├── core/               # App config, database session, security logic
│   │   ├── models/             # SQLAlchemy DB schemas
│   │   ├── schemas/            # Pydantic validation schemas (Input/Output)
│   │   ├── services/           # Heavy lifting (OCR, Evaluator AI, RAG ingestion)
│   │   └── main.py             # FastAPI App definition
│   ├── uploads/                # Local storage for images/PDFs
│   └── requirements.txt        # Python backend dependencies
│
└── frontend/
    ├── src/
    │   ├── components/         # React Views (Auth, Teacher UI, Student UI, Common)
    │   ├── context/            # Global States (Auth, Theme, Notifications)
    │   ├── services/           # API handlers (Axios interface)
    │   ├── App.jsx             # React Router definition
    │   └── index.css           # Tailwind + Custom styling system
    ├── package.json            # Node.js dependencies
    └── tailwind.config.js      # Theme UI config
```
