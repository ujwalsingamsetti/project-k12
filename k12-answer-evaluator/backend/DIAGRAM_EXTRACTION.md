# Diagram Extraction Feature

## Overview
Automatically extracts and analyzes geometric shapes (triangles, circles, rectangles, etc.) from student answer sheets using Google Cloud Vision API and OpenCV.

## Features

### 1. Dual Detection Methods
- **Google Cloud Vision API**: Object localization for high-accuracy shape detection
- **OpenCV**: Contour detection, edge detection, and geometric analysis

### 2. Shape Detection
- Triangles (equilateral, isosceles, scalene, right-angled)
- Circles and ellipses
- Rectangles and squares
- Polygons
- Lines (using Hough Transform)

### 3. Integration
- Automatic extraction during OCR processing
- Metadata stored in `answer_submissions.diagram_metadata` (JSON)
- Passed to LLM evaluation for context

## Database Schema

```sql
ALTER TABLE answer_submissions 
ADD COLUMN diagram_metadata JSON;
```

**Structure:**
```json
{
  "diagrams": [
    {
      "page": 1,
      "shapes": [
        {
          "type": "triangle",
          "vertices": 3,
          "area": 5000,
          "bbox": [100, 200, 150, 120],
          "method": "opencv"
        }
      ],
      "diagram_paths": ["/path/to/extracted_diagram_0.png"]
    }
  ]
}
```

## Files Modified

1. **app/services/diagram_service.py** (NEW)
   - DiagramService class
   - extract_diagrams() - main extraction method
   - analyze_triangle() - detailed triangle analysis
   - _detect_with_vision() - Google Vision detection
   - _detect_with_opencv() - OpenCV detection

2. **app/services/ocr_service.py**
   - Updated extract_text_from_image() to return tuple: (text, diagram_metadata)
   - Integrated DiagramService

3. **app/models/submission.py**
   - Added diagram_metadata JSON column

4. **app/api/students.py**
   - Updated process_submission_multiple() to extract and store diagrams
   - Updated process_submission() to extract and store diagrams
   - Pass diagram_info to evaluation service

5. **app/services/evaluation_service.py**
   - Added diagram_info parameter to evaluate_answer()
   - Appends diagram context to student answer for LLM

## Usage

### Automatic (Default)
Diagrams are automatically extracted when students submit answer sheets. No code changes needed.

### Manual Analysis
```python
from app.services.diagram_service import DiagramService

service = DiagramService(vision_client)
result = service.extract_diagrams("/path/to/image.jpg")

if result["has_diagrams"]:
    print(f"Found {len(result['shapes_detected'])} shapes")
    for shape in result["shapes_detected"]:
        print(f"- {shape['type']}")
```

### Triangle Analysis
```python
triangle_info = service.analyze_triangle("/path/to/triangle.jpg")
if triangle_info["is_triangle"]:
    print(f"Type: {triangle_info['triangle_type']}")
    print(f"Sides: {triangle_info['sides']}")
```

## How It Works

1. **Student submits answer sheet** → Multiple images uploaded
2. **OCR Service processes each page**:
   - Extracts text using Google Vision
   - Extracts diagrams using DiagramService
3. **Diagram metadata stored** in database
4. **Evaluation Service** receives diagram context:
   - "DIAGRAM DETECTED: Student included geometric shapes: triangle, circle"
5. **LLM evaluates** answer with diagram awareness

## Benefits

- **Geometry Questions**: Detects if student drew required diagrams
- **Better Grading**: LLM knows student included visual elements
- **Partial Credit**: Can award marks for correct diagrams even if explanation is weak
- **Feedback**: Can mention missing or incorrect diagrams

## Configuration

No additional configuration needed. Uses existing Google Cloud Vision credentials.

## Testing

```bash
# Test diagram extraction
python -c "
from app.services.diagram_service import DiagramService
from google.cloud import vision
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/credentials.json'
client = vision.ImageAnnotatorClient()
service = DiagramService(client)

result = service.extract_diagrams('test_image.jpg')
print(result)
"
```

## Future Enhancements

- Diagram comparison (student vs expected)
- Angle measurement validation
- Label detection on diagrams
- Diagram quality scoring
- Support for graphs and charts
