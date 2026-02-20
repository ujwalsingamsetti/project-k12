# MCQ Detection & PDF Viewing Enhancements

## Changes Implemented

### 1. Enhanced MCQ Detection in Section-Based Parsing

**File**: `app/services/question_paper_ocr_service.py`

#### New Method: `_detect_question_type_from_text()`
Intelligently detects question type based on:
- **Options present**: If options dict has 2+ entries → MCQ
- **Option patterns in text**: Detects `A)`, `B)`, `C)`, `D)` or `1)`, `2)`, `3)`, `4)` → MCQ
- **Marks-based fallback**: Uses marks to infer type (≤2 marks = short, >2 marks = long)

#### Enhanced `_parse_section_based()`
Now properly:
- **Extracts marks from section headers**: "Section A (16x1=16 marks)" → 16 questions of 1 mark each
- **Detects MCQ options**: Recognizes both `A)` and `1)` formats
- **Converts numeric options**: Automatically converts `1)` → `A)`, `2)` → `B)`, etc.
- **Stores options**: Saves options dict for MCQ questions
- **Determines question type**: Uses new detection method instead of just marks

### 2. MCQ Option Detection Patterns

**Supported formats**:
```
A) Option text
B) Option text
C) Option text
D) Option text
```

OR

```
1) Option text
2) Option text
3) Option text
4) Option text
```

**Auto-conversion**: Numeric options (1,2,3,4) are automatically converted to letters (A,B,C,D)

### 3. Section-Based Marks Extraction

**Example**: `SECTION A (16x1=16 marks)`
- Creates 16 questions
- Each question: 1 mark
- Section: A
- Type: Determined by content (MCQ if options found, otherwise based on marks)

**Example**: `Section B: 8 x 2 = 16 marks`
- Creates 8 questions
- Each question: 2 marks
- Section: B
- Type: short (since 2 marks)

**Example**: `SECTION C - 7×3=21 marks`
- Creates 7 questions
- Each question: 3 marks
- Section: C
- Type: long (since 3 marks)

### 4. PDF Viewing for Students

#### Backend Endpoint (Already exists)
- `GET /api/student/papers/{paper_id}/pdf`
- Returns PDF file with proper content type
- Accessible to all students

#### Frontend - Student Dashboard
**File**: `frontend/src/components/student/Dashboard.jsx`

Added PDF view button (📄 icon) next to "Submit Answer" button:
- Only shows if `paper.pdf_path` exists
- Opens PDF in new tab
- Blue button with document icon

#### Frontend - Submit Answer Page
**File**: `frontend/src/components/student/SubmitAnswer.jsx`

Already has "📄 View Question Paper PDF" button at top of page

### 5. Question Data Structure

Enhanced question objects now include:
```json
{
  "question_number": 1,
  "question_text": "What is photosynthesis?",
  "marks": 1,
  "question_type": "mcq",
  "section": "A",
  "has_diagram": false,
  "has_or_option": false,
  "options": {
    "A": "Process of making food",
    "B": "Process of respiration",
    "C": "Process of digestion",
    "D": "Process of excretion"
  },
  "correct_answer": null
}
```

## Example Question Paper Format

```
SECTION A (16x1=16 marks)

1. What is the chemical formula of water?
A) H2O
B) CO2
C) O2
D) N2

2. What is the value of π?
A) 3.14
B) 2.71
C) 1.41
D) 1.73

... (14 more questions)

SECTION B (8x2=16 marks)

1. Explain photosynthesis OR respiration. (2 marks)

2. Calculate the area of a circle with radius 5 cm. (2 marks)

... (6 more questions)

SECTION C (7x3=21 marks)

1. Derive the quadratic formula. (3 marks)

2. Explain the process of mitosis in detail. (3 marks)

... (5 more questions)
```

## Detection Logic Flow

1. **Section Header Detected** → Extract num_questions × marks_per_question
2. **Question Number Found** → Start new question
3. **Option Pattern Found** (A) or 1)) → Add to options dict
4. **Question Complete** → Determine type:
   - If options present → MCQ
   - If option patterns in text → MCQ
   - Otherwise → Use marks (≤2: short, >2: long)

## Benefits

1. **Accurate MCQ Detection**: No longer defaults to "long" for 1-mark questions
2. **Proper Marks Extraction**: Correctly reads section format (16x1, 8x2, etc.)
3. **Option Capture**: Stores MCQ options for proper evaluation
4. **Student PDF Access**: Students can view original question paper anytime
5. **Dashboard Integration**: Quick PDF access from dashboard
6. **Flexible Format Support**: Handles both A/B/C/D and 1/2/3/4 option formats

## Testing Checklist

- [ ] Upload question paper with "SECTION A (16x1=16 marks)"
- [ ] Verify 16 questions created with 1 mark each
- [ ] Check questions with A) B) C) D) options detected as MCQ
- [ ] Check questions with 1) 2) 3) 4) options detected as MCQ
- [ ] Verify numeric options converted to A/B/C/D
- [ ] Confirm PDF button appears in student dashboard
- [ ] Test PDF opens in new tab when clicked
- [ ] Verify section badges show correctly (A, B, C)
- [ ] Check question types are correct (mcq, short, long)
