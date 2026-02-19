# MCQ Support & Image-Based Question Paper Upload

## Feature 1: MCQ Pattern Questions

### Backend Implementation

**Database Changes:**
```sql
ALTER TABLE questions 
ADD COLUMN options JSON,
ADD COLUMN correct_answer VARCHAR(10);
```

**Model Updates:**
- `QuestionType` enum: Added `MCQ = "mcq"`
- `Question` model: Added `options` (JSON) and `correct_answer` (String) fields
- Schema: Updated `QuestionBase` to include MCQ fields

**MCQ Evaluator Service** (`mcq_evaluator.py`):
- `extract_mcq_choice()`: Extracts student's choice (A/B/C/D) from answer text
- `evaluate_mcq()`: Compares student choice with correct answer
- Returns structured feedback with score, correct/incorrect indication

**Evaluation Logic:**
- MCQ questions: Direct comparison, instant grading
- Descriptive questions: LLM-based evaluation with RAG
- Mixed paper support: Handles both types in same paper

### Frontend Implementation

**CreatePaper Component:**
- Added MCQ option in question type dropdown
- Dynamic MCQ options form (A, B, C, D)
- Correct answer selector
- Auto-sets marks to 1 for MCQ
- Validates all options are filled

**Features:**
- Manual entry with MCQ support
- Options A, B, C, D input fields
- Correct answer dropdown
- Validation for required fields

---

## Feature 2: Image-Based Question Paper Upload

### Backend Implementation

**Question Paper OCR Service** (`question_paper_ocr_service.py`):

**Question Extraction:**
- Patterns supported:
  - `Q1. Question text [5 marks]`
  - `1) Question text (5 marks)`
  - `Question 1: Question text - 5 marks`
- Extracts: question number, text, marks
- Infers question type from marks (≤2: short, >2: long)

**MCQ Extraction:**
- Detects MCQ format with options A-D
- Parses question and all options
- Returns structured MCQ data

**API Endpoint:**
```
POST /api/teacher/papers/from-image
- Accepts: image file (JPG/PNG)
- Parameters: title, subject, duration_minutes
- Returns: paper_id, questions_count, total_marks
```

**Process Flow:**
1. Upload image to temp directory
2. Extract text using Google Cloud Vision OCR
3. Parse questions with regex patterns
4. Calculate total marks
5. Create question paper in database
6. Clean up temp file

### Frontend Implementation

**CreatePaper Component - Image Mode:**

**Two Modes:**
1. **Manual Entry**: Traditional form-based entry
2. **Upload Image**: OCR-based extraction

**Image Upload Interface:**
- Tab-based mode selection
- Basic info form (title, subject, duration)
- Drag-and-drop style upload area
- Supported formats: JPG, PNG
- Processing indicator
- Success/error feedback

**User Flow:**
1. Select "Upload Image" tab
2. Fill optional title, subject, duration
3. Click "Choose Image"
4. System processes image
5. Questions extracted automatically
6. Paper created with all questions

---

## Combined Features

### Question Paper Creation Options

**Option 1: Manual Entry**
- Add questions one by one
- Support for Short/Long/MCQ types
- MCQ: Enter options A-D + correct answer
- Full control over all fields

**Option 2: Image Upload**
- Upload photo of printed question paper
- Automatic question extraction
- Automatic marks calculation
- Quick paper creation

**Option 3: Mixed Approach**
- Create from image
- Edit manually if needed (future enhancement)

---

## Technical Details

### MCQ Evaluation

**Student Answer Parsing:**
```python
# Accepts formats:
- "A"
- "(A)"
- "A)"
- "[A]"
- "A."
- "The answer is A"
```

**Evaluation Result:**
```json
{
  "score": 1,
  "overall_feedback": "Your answer: A. Correct answer: B. Incorrect.",
  "correct_points": [],
  "errors": [{
    "what": "Selected A instead of B",
    "why": "Incorrect option",
    "impact": "No marks awarded"
  }],
  "correct_answer_should_include": ["Option B: Photosynthesis"]
}
```

### Image OCR Patterns

**Question Detection:**
```regex
^Q\.?\s*(\d+)\.?\s+(.*?)[\[\(](\d+)\s*marks?[\]\)]
^(\d+)[\.\)]\s+(.*?)[\[\(](\d+)\s*marks?[\]\)]
^Question\s+(\d+)[:\.]\s+(.*?)[-–]\s*(\d+)\s*marks?
```

**Example Inputs:**
```
Q1. What is photosynthesis? [5 marks]
1) Explain Newton's laws (10 marks)
Question 3: Define velocity - 3 marks
```

---

## File Changes

### Backend Files Created:
1. `/app/services/question_paper_ocr_service.py` - OCR extraction
2. `/app/services/mcq_evaluator.py` - MCQ evaluation logic

### Backend Files Modified:
1. `/app/models/question.py` - Added MCQ fields
2. `/app/schemas/question_paper.py` - Added MCQ schema fields
3. `/app/crud/question_paper.py` - Handle MCQ fields in CRUD
4. `/app/api/teachers.py` - Added image upload endpoint
5. `/app/api/students.py` - Added MCQ evaluation logic

### Frontend Files Modified:
1. `/src/services/api.js` - Added createPaperFromImage()
2. `/src/components/teacher/CreatePaper.jsx` - Added MCQ + image modes

### Database Changes:
```sql
ALTER TABLE questions 
ADD COLUMN options JSON,
ADD COLUMN correct_answer VARCHAR(10);
```

---

## Usage Examples

### Creating MCQ Question (Manual):

1. Go to Create Paper
2. Select "Manual Entry"
3. Add question
4. Select "MCQ" type
5. Enter question text
6. Fill options A, B, C, D
7. Select correct answer
8. Save paper

### Creating Paper from Image:

1. Go to Create Paper
2. Select "Upload Image"
3. Enter title (optional)
4. Select subject
5. Set duration
6. Click "Choose Image"
7. Select clear photo of question paper
8. Wait for processing
9. Paper created automatically

### Student Answering MCQ:

1. View paper with MCQ questions
2. Write answer: "A" or "(A)" or "Answer: A"
3. Submit answer sheet
4. System extracts choice
5. Compares with correct answer
6. Instant grading

---

## Benefits

### MCQ Support:
- Instant grading (no LLM needed)
- Objective evaluation
- Reduced evaluation time
- Support for mixed papers (MCQ + descriptive)
- Clear feedback on correct/incorrect

### Image Upload:
- Quick paper creation
- No manual typing needed
- Reduces teacher workload
- Supports existing printed papers
- Automatic question numbering
- Automatic marks calculation

---

## Limitations & Future Enhancements

### Current Limitations:
1. Image OCR requires clear, well-formatted questions
2. MCQ extraction from images not yet implemented
3. No editing of OCR-extracted papers
4. Supports only A-D options (not A-E)

### Future Enhancements:
1. Edit OCR-extracted papers before saving
2. Extract MCQ questions from images
3. Support for True/False questions
4. Support for fill-in-the-blank
5. Batch image upload (multiple pages)
6. Preview extracted questions before creation
7. Manual correction of OCR errors

---

## Testing

### Test MCQ Creation:
1. Create paper with MCQ questions
2. Verify options saved correctly
3. Submit answer with choice "A"
4. Verify evaluation shows correct/incorrect
5. Check marks awarded

### Test Image Upload:
1. Create clear image with questions
2. Format: "Q1. Question text [5 marks]"
3. Upload via Create Paper → Upload Image
4. Verify questions extracted correctly
5. Check total marks calculated
6. Verify paper appears in dashboard

### Test Mixed Paper:
1. Create paper with MCQ + descriptive
2. Submit answers for both types
3. Verify MCQ graded instantly
4. Verify descriptive uses LLM
5. Check total score calculation
