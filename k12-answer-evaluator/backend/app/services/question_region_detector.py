import cv2
import numpy as np
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class QuestionRegionDetector:
    """Detect question regions in answer sheets for diagram mapping"""
    
    def detect_question_regions(self, image_path: str, extracted_text: str) -> List[Dict]:
        """Detect regions for each question in the image
        
        Returns:
            List of {"question_number": int, "bbox": [x, y, w, h]}
        """
        
        # Parse question numbers from text
        question_numbers = self._extract_question_numbers(extracted_text)
        
        if not question_numbers:
            return []
        
        # Detect text regions in image
        text_regions = self._detect_text_regions(image_path)
        
        # Map question numbers to regions
        question_regions = self._map_questions_to_regions(
            question_numbers, 
            text_regions, 
            image_path
        )
        
        return question_regions
    
    def _extract_question_numbers(self, text: str) -> List[int]:
        """Extract question numbers from text"""
        question_numbers = []
        
        # Patterns: Q1, Q.1, 1), 1., Question 1
        patterns = [
            r'Q\.?\s*(\d+)',
            r'Question\s+(\d+)',
            r'^(\d+)\)',
            r'^(\d+)\.',
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    q_num = int(match.group(1))
                    if q_num not in question_numbers:
                        question_numbers.append(q_num)
                    break
        
        return sorted(question_numbers)
    
    def _detect_text_regions(self, image_path: str) -> List[Dict]:
        """Detect text regions using EAST or contour detection"""
        regions = []
        
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Threshold to get text regions
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Dilate to connect text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 10))
            dilated = cv2.dilate(binary, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter small regions
                if w > 100 and h > 30:
                    regions.append({
                        "bbox": [x, y, w, h],
                        "center_y": y + h // 2
                    })
            
            # Sort by vertical position
            regions.sort(key=lambda r: r["center_y"])
            
        except Exception as e:
            logger.error(f"Text region detection failed: {e}")
        
        return regions
    
    def _map_questions_to_regions(
        self, 
        question_numbers: List[int], 
        text_regions: List[Dict],
        image_path: str
    ) -> List[Dict]:
        """Map question numbers to detected regions"""
        
        if not text_regions:
            # Fallback: divide image into equal regions
            return self._create_fallback_regions(question_numbers, image_path)
        
        question_regions = []
        
        # Simple approach: assign regions sequentially
        regions_per_question = max(1, len(text_regions) // len(question_numbers))
        
        for idx, q_num in enumerate(question_numbers):
            start_idx = idx * regions_per_question
            end_idx = start_idx + regions_per_question
            
            if idx == len(question_numbers) - 1:
                # Last question gets remaining regions
                end_idx = len(text_regions)
            
            # Merge regions for this question
            if start_idx < len(text_regions):
                merged_bbox = self._merge_bboxes([
                    r["bbox"] for r in text_regions[start_idx:end_idx]
                ])
                
                question_regions.append({
                    "question_number": q_num,
                    "bbox": merged_bbox
                })
        
        return question_regions
    
    def _merge_bboxes(self, bboxes: List[List[int]]) -> List[int]:
        """Merge multiple bounding boxes into one"""
        if not bboxes:
            return [0, 0, 0, 0]
        
        x_min = min(bbox[0] for bbox in bboxes)
        y_min = min(bbox[1] for bbox in bboxes)
        x_max = max(bbox[0] + bbox[2] for bbox in bboxes)
        y_max = max(bbox[1] + bbox[3] for bbox in bboxes)
        
        return [x_min, y_min, x_max - x_min, y_max - y_min]
    
    def _create_fallback_regions(
        self, 
        question_numbers: List[int], 
        image_path: str
    ) -> List[Dict]:
        """Create fallback regions by dividing image equally"""
        
        try:
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            
            region_height = height // len(question_numbers)
            
            regions = []
            for idx, q_num in enumerate(question_numbers):
                y = idx * region_height
                h = region_height if idx < len(question_numbers) - 1 else height - y
                
                regions.append({
                    "question_number": q_num,
                    "bbox": [0, y, width, h]
                })
            
            return regions
            
        except Exception as e:
            logger.error(f"Fallback region creation failed: {e}")
            return []
