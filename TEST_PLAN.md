# Test Plan
Project: **K12 Answer Evaluator**

## 1. Quality Assurance Objective
To ensure that the application functions seamlessly across its core user personas (student and teacher). The primary objective is to guarantee the robustness of the AI Evaluation process and prevent grade falsification or authentication breaches.

## 2. Test Strategies

### 2.1 Backend Unit & Integration Tests (Pytest)
- Validating the parsing integrity of our custom OCR pipeline.
- Ensuring `google_genai` prompts safely parse structured JSON without crashing under abnormal token inputs.
- Ensuring secure multi-role JWT route protection (Students cannot access Teacher Endpoints, vice versa).

### 2.2 Frontend Functional Testing
- Route protection guards are operating correctly (`<ProtectedRoute>` component).
- Form validation effectively handles edge cases (e.g., uploading malformed images, missing text fields).
- Verifying the React State lifecycle for real-time polling updates when papers move to "Evaluated" state.

### 2.3 Evaluation Quality Testing
Testing the AI output against a benchmark suite of manual human-graded answer sheets to determine scoring drift. Ensure the `get_rag_context` effectively halts hallucinated grades by grounding answers to the supplied textbook embeddings.

## 3. Core Test Scenarios (Manual Regression)

**Authentication & Roles**
- [ ] User can register a Teacher account.
- [ ] User can register a Student account.
- [ ] User can log in with valid credentials.
- [ ] API rejects requests missing a JWT Bearer header.

**Teacher Workflow**
- [ ] Create a Question Paper manually.
- [ ] Extract question paper from an image/PDF (OCR Vision test).
- [ ] Upload a reference textbook (PDF RAG test).
- [ ] Override AI-given marks on a student submission.

**Student Workflow**
- [ ] View assigned / available papers in the dashboard.
- [ ] "Profile missing grade" badge redirects to the `student/profile` route properly.
- [ ] Uploading 1-3 images successfully initiates a background task without hitting upload timeouts.
- [ ] View granular line-by-line feedback.
- [ ] Download a PDF Report Card that accurately totals the marks.
