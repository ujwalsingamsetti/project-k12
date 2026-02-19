# Enhanced Question Paper Upload Features

## New Features Implemented

### 1. Multiple Page Support
- Teachers can upload multiple images of question paper pages
- Questions extracted from all pages and combined
- Sequential question numbering across pages

### 2. PDF Upload Support
- Direct PDF upload for question papers
- Automatic conversion to images (300 DPI)
- OCR processing on each page
- Combined question extraction

### 3. Diagram Detection in Question Papers
- Automatic detection of geometric shapes in questions
- Diagrams mapped to specific questions
- Diagram count reported after extraction
- `has_diagram` flag added to questions

---

## Backend Implementation

### QuestionPaperOCRService Updates

**New Methods:**

1. **extract_questions_from_pdf(pdf_path)**
   - Converts PDF to images using pdf2image
   - Processes each page with OCR
   - Extracts diagrams from each page
   - Combines all questions
   - Renumbers sequentially
   - Cleans up temp files

2. **extract_questions_from_multiple_images(image_paths)**
   - Processes multiple image files
   - Extracts questions from each
   - Combines and renumbers
   - Preserves diagram information

3. **extract_questions_from_image(image_path)** - Enhanced
   - Now extracts both text and diagrams
   - Maps diagrams to questions
   - Adds `has_diagram` flag to questions

**Dependencies Added:**
```python
from pdf2image import convert_from_path
from app.services.diagram_service import DiagramService
```

### API Endpoint Updates

**POST /api/teacher/papers/from-image**

**Changes:**
- Now accepts `List[UploadFile]` instead of single file
- Supports `.pdf`, `.png`, `.jpg`, `.jpeg` formats
- Detects file type and routes to appropriate processor
- Returns additional `diagrams_detected` count

**Request:**
```
files: List[UploadFile] (multiple files)
title: str (optional)
subject: str (optional)
duration_minutes: int (default 180)
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Paper title",
  "questions_count": 10,
  "total_marks": 50,
  "diagrams_detected": 3
}
```

**Processing Logic:**
1. If PDF → `extract_questions_from_pdf()`
2. If multiple images → `extract_questions_from_multiple_images()`
3. If single image → `extract_questions_from_image()`

---

## Frontend Implementation

### CreatePaper Component Updates

**New State:**
```javascript
const [uploadFiles, setUploadFiles] = useState([]);
```

**New Features:**

1. **File Selection**
   - Multiple file input with `multiple` attribute
   - Accepts `image/*,.pdf`
   - Preview selected files
   - Remove individual files before upload

2. **File Preview**
   - Shows list of selected files
   - File name display
   - Remove button for each file

3. **Two-Step Upload**
   - Step 1: Choose files (shows preview)
   - Step 2: Click "Upload & Extract" button
   - Prevents accidental uploads

**UI Flow:**
```
1. Click "Choose Files"
2. Select multiple images or PDF
3. Files appear in preview list
4. Remove unwanted files (optional)
5. Click "Upload & Extract"
6. Processing indicator
7. Success message with counts
```

### API Integration

**Updated Function:**
```javascript
createPaperFromImage(files, title, subject, duration)
```

**Changes:**
- Accepts array of files
- Appends each file to FormData
- Supports both single and multiple files

---

## Technical Details

### PDF Processing

**Conversion:**
```python
images = convert_from_path(pdf_path, dpi=300)
```

**Temp File Management:**
```python
temp_page_0.png
temp_page_1.png
temp_page_2.png
```

**Cleanup:**
- All temp files deleted after processing
- Even on error/exception

### Diagram Detection

**Per Question:**
```python
{
  "question_number": 1,
  "question_text": "Draw a triangle...",
  "marks": 5,
  "question_type": "long",
  "has_diagram": true  # NEW
}
```

**Diagram Mapping:**
- OCR extracts text and diagrams
- Diagrams mapped to question numbers
- Based on spatial proximity
- Stored in question metadata

### Multiple Image Processing

**Sequential Processing:**
```python
for image_path in image_paths:
    page_questions = extract_questions_from_image(image_path)
    all_questions.extend(page_questions)

# Renumber
for idx, q in enumerate(all_questions, 1):
    q['question_number'] = idx
```

---

## Usage Examples

### Upload Multiple Images

1. Go to Create Paper → Upload Image
2. Click "Choose Files"
3. Select page1.jpg, page2.jpg, page3.jpg
4. Files appear in preview
5. Click "Upload & Extract"
6. System processes all pages
7. Questions combined and numbered 1-N

### Upload PDF

1. Go to Create Paper → Upload Image
2. Click "Choose Files"
3. Select question_paper.pdf
4. File appears in preview
5. Click "Upload & Extract"
6. PDF converted to images
7. Each page processed
8. Questions extracted and combined

### With Diagrams

1. Upload question paper with geometry questions
2. System detects triangles, circles, etc.
3. Maps diagrams to questions
4. Success message: "10 questions extracted. 3 diagrams detected."
5. Questions with diagrams flagged

---

## File Changes

### Backend Files Modified:
1. `/app/services/question_paper_ocr_service.py`
   - Added PDF support
   - Added multiple image support
   - Added diagram detection
   - Added DiagramService integration

2. `/app/api/teachers.py`
   - Changed endpoint to accept List[UploadFile]
   - Added PDF detection logic
   - Added routing to appropriate processor
   - Added diagrams_detected to response

### Frontend Files Modified:
1. `/src/services/api.js`
   - Updated createPaperFromImage to handle arrays
   - Support for multiple files in FormData

2. `/src/components/teacher/CreatePaper.jsx`
   - Added uploadFiles state
   - Added file preview list
   - Added remove file functionality
   - Added two-step upload process
   - Updated accept attribute to include PDF

---

## Benefits

### Multiple Pages:
- No need to combine images manually
- Natural workflow for multi-page papers
- Automatic question numbering
- Preserves question order

### PDF Support:
- Direct upload of existing PDFs
- No conversion needed
- High quality extraction (300 DPI)
- Supports any number of pages

### Diagram Detection:
- Identifies geometry questions
- Helps with evaluation context
- Provides feedback to teacher
- Future: Can validate student diagrams

---

## Requirements

### Python Packages:
```bash
pip install pdf2image
```

### System Dependencies:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download poppler binaries and add to PATH
```

---

## Limitations & Future Enhancements

### Current Limitations:
1. PDF must be text-based (not scanned images)
2. Max file size depends on server config
3. Processing time increases with pages
4. Diagram detection accuracy varies

### Future Enhancements:
1. Progress bar for multi-page processing
2. Preview extracted questions before saving
3. Edit OCR results before creation
4. Batch processing multiple PDFs
5. Template-based extraction
6. Answer key extraction from images
7. Automatic MCQ option detection

---

## Testing

### Test Multiple Images:
1. Create 3 separate images with questions
2. Upload all together
3. Verify all questions extracted
4. Check sequential numbering
5. Verify total marks calculated

### Test PDF:
1. Create PDF with 2-3 pages
2. Upload PDF
3. Verify all pages processed
4. Check question extraction
5. Verify no temp files left

### Test Diagrams:
1. Upload paper with geometry questions
2. Include triangles, circles
3. Verify diagrams detected
4. Check diagram count in response
5. Verify has_diagram flag set

### Test Mixed:
1. Upload 2 images + 1 PDF (should fail - one type at a time)
2. Upload only images (should work)
3. Upload only PDF (should work)
