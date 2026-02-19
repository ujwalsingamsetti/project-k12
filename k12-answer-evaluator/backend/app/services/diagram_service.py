import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple
import os
from google.cloud import vision

logger = logging.getLogger(__name__)

class DiagramService:
    """Extract and analyze geometric diagrams from images"""
    
    def __init__(self, vision_client=None):
        self.vision_client = vision_client
    
    def extract_diagrams(self, image_path: str, question_regions: List[Dict] = None) -> Dict:
        """Extract diagrams using both Google Vision and OpenCV
        
        Args:
            image_path: Path to image
            question_regions: Optional list of {"question_number": int, "bbox": [x, y, w, h]}
        """
        
        result = {
            "has_diagrams": False,
            "shapes_detected": [],
            "diagram_regions": [],
            "diagram_paths": [],
            "question_diagrams": {}  # Maps question_number to shapes
        }
        
        # Method 1: Google Cloud Vision Object Localization
        vision_shapes = self._detect_with_vision(image_path)
        
        # Method 2: OpenCV geometric detection
        opencv_shapes = self._detect_with_opencv(image_path)
        
        # Combine results
        all_shapes = vision_shapes + opencv_shapes
        
        if all_shapes:
            result["has_diagrams"] = True
            result["shapes_detected"] = all_shapes
            
            # Map shapes to questions if regions provided
            if question_regions:
                result["question_diagrams"] = self._map_shapes_to_questions(all_shapes, question_regions)
            
            # Extract and save diagram regions
            diagram_paths = self._extract_regions(image_path, opencv_shapes)
            result["diagram_paths"] = diagram_paths
        
        return result
    
    def _map_shapes_to_questions(self, shapes: List[Dict], question_regions: List[Dict]) -> Dict:
        """Map detected shapes to question numbers based on spatial proximity"""
        question_diagrams = {}
        
        for shape in shapes:
            if "bbox" not in shape:
                continue
            
            shape_x, shape_y, shape_w, shape_h = shape["bbox"]
            shape_center_y = shape_y + shape_h // 2
            
            # Find closest question region
            min_distance = float('inf')
            closest_question = None
            
            for q_region in question_regions:
                q_num = q_region["question_number"]
                q_x, q_y, q_w, q_h = q_region["bbox"]
                
                # Check if shape is within question region
                if (q_x <= shape_x <= q_x + q_w and 
                    q_y <= shape_center_y <= q_y + q_h):
                    closest_question = q_num
                    break
                
                # Calculate distance to question region
                q_center_y = q_y + q_h // 2
                distance = abs(shape_center_y - q_center_y)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_question = q_num
            
            if closest_question:
                if closest_question not in question_diagrams:
                    question_diagrams[closest_question] = []
                question_diagrams[closest_question].append(shape)
        
        return question_diagrams
    
    def _detect_with_vision(self, image_path: str) -> List[Dict]:
        """Use Google Vision API for object localization"""
        shapes = []
        
        if not self.vision_client:
            return shapes
        
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.vision_client.object_localization(image=image)
            
            geometric_objects = ['Triangle', 'Circle', 'Rectangle', 'Square', 'Polygon', 
                               'Line', 'Angle', 'Shape', 'Diagram', 'Graph']
            
            for obj in response.localized_object_annotations:
                if any(geo in obj.name for geo in geometric_objects):
                    shapes.append({
                        "type": obj.name.lower(),
                        "confidence": obj.score,
                        "method": "vision_api"
                    })
            
        except Exception as e:
            logger.warning(f"Vision API object detection failed: {e}")
        
        return shapes
    
    def _detect_with_opencv(self, image_path: str) -> List[Dict]:
        """Detect geometric shapes using OpenCV"""
        shapes = []
        
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Preprocessing
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter small noise (min 500 pixels)
                if area < 500:
                    continue
                
                # Approximate polygon
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                vertices = len(approx)
                
                shape_type = self._classify_shape(vertices, contour, area)
                
                if shape_type:
                    x, y, w, h = cv2.boundingRect(contour)
                    shapes.append({
                        "type": shape_type,
                        "vertices": vertices,
                        "area": int(area),
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "method": "opencv"
                    })
            
            # Detect lines using Hough Transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                   minLineLength=50, maxLineGap=10)
            
            if lines is not None and len(lines) > 3:
                shapes.append({
                    "type": "lines",
                    "count": len(lines),
                    "method": "opencv"
                })
            
        except Exception as e:
            logger.error(f"OpenCV detection failed: {e}")
        
        return shapes
    
    def _classify_shape(self, vertices: int, contour, area: float) -> str:
        """Classify shape based on vertices and properties"""
        
        if vertices == 3:
            return "triangle"
        elif vertices == 4:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if 0.95 <= aspect_ratio <= 1.05:
                return "square"
            return "rectangle"
        elif vertices > 4 and vertices < 8:
            return "polygon"
        elif vertices >= 8:
            # Check if it's a circle
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.8:
                return "circle"
            return "ellipse"
        
        return None
    
    def _extract_regions(self, image_path: str, shapes: List[Dict]) -> List[str]:
        """Extract and save diagram regions as separate images"""
        diagram_paths = []
        
        try:
            img = cv2.imread(image_path)
            base_name = os.path.splitext(image_path)[0]
            
            for idx, shape in enumerate(shapes):
                if "bbox" in shape:
                    x, y, w, h = shape["bbox"]
                    
                    # Add padding
                    padding = 10
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(img.shape[1] - x, w + 2*padding)
                    h = min(img.shape[0] - y, h + 2*padding)
                    
                    # Extract region
                    region = img[y:y+h, x:x+w]
                    
                    # Save
                    diagram_path = f"{base_name}_diagram_{idx}.png"
                    cv2.imwrite(diagram_path, region)
                    diagram_paths.append(diagram_path)
            
        except Exception as e:
            logger.error(f"Region extraction failed: {e}")
        
        return diagram_paths
    
    def analyze_triangle(self, image_path: str) -> Dict:
        """Detailed triangle analysis"""
        result = {
            "is_triangle": False,
            "triangle_type": None,
            "angles": [],
            "sides": []
        }
        
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                
                if len(approx) == 3:
                    result["is_triangle"] = True
                    
                    # Calculate sides
                    pts = approx.reshape(3, 2)
                    sides = [
                        np.linalg.norm(pts[0] - pts[1]),
                        np.linalg.norm(pts[1] - pts[2]),
                        np.linalg.norm(pts[2] - pts[0])
                    ]
                    result["sides"] = [float(s) for s in sides]
                    
                    # Classify triangle type
                    sides_sorted = sorted(sides)
                    if abs(sides_sorted[0] - sides_sorted[1]) < 5 and abs(sides_sorted[1] - sides_sorted[2]) < 5:
                        result["triangle_type"] = "equilateral"
                    elif abs(sides_sorted[0] - sides_sorted[1]) < 5 or abs(sides_sorted[1] - sides_sorted[2]) < 5:
                        result["triangle_type"] = "isosceles"
                    else:
                        result["triangle_type"] = "scalene"
                    
                    # Check for right triangle (Pythagorean theorem)
                    if abs(sides_sorted[0]**2 + sides_sorted[1]**2 - sides_sorted[2]**2) < 100:
                        result["triangle_type"] = "right_" + result["triangle_type"]
                    
                    break
        
        except Exception as e:
            logger.error(f"Triangle analysis failed: {e}")
        
        return result
