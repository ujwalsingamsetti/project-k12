import re
import logging
from typing import List, Dict
import PyPDF2
from pdf2image import convert_from_path
import os
from app.services.ocr_service import OCRService
from app.services.diagram_service import DiagramService

logger = logging.getLogger(__name__)

class QuestionPaperOCRService:
    """Extract questions from question paper images/PDFs"""
    
    def __init__(self):
        self.ocr_service = OCRService()
        try:
            if hasattr(self.ocr_service, 'vision_client') and self.ocr_service.vision_client:
                self.diagram_service = DiagramService(self.ocr_service.vision_client)
            else:
                self.diagram_service = None
                logger.warning("DiagramService not initialized - vision_client not available")
        except Exception as e:
            self.diagram_service = None
            logger.warning(f"DiagramService initialization failed: {e}")
    
    def extract_questions_from_image(self, image_path: str) -> List[Dict]:
        """Extract questions from question paper image"""
        
        try:
            # Extract text and diagrams
            text, diagram_metadata = self.ocr_service.extract_text_from_image(image_path)
            
            # Parse questions
            questions = self._parse_questions(text)
            
            # Add diagram info
            if diagram_metadata and diagram_metadata.get("has_diagrams"):
                question_diagrams = diagram_metadata.get("question_diagrams", {})
                for q in questions:
                    q_num = str(q["question_number"])
                    q["has_diagram"] = q_num in question_diagrams
            
            return questions
        except Exception as e:
            logger.error(f"Error extracting questions from image {image_path}: {e}")
            raise
    
    def extract_questions_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract questions from PDF question paper"""
        
        all_questions = []
        temp_images = []
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            # Save as temp images and process
            temp_dir = os.path.dirname(pdf_path)
            
            for idx, image in enumerate(images):
                temp_image_path = os.path.join(temp_dir, f"temp_page_{idx}.png")
                image.save(temp_image_path, 'PNG')
                temp_images.append(temp_image_path)
                
                # Extract questions from this page
                page_questions = self.extract_questions_from_image(temp_image_path)
                all_questions.extend(page_questions)
            
            # Renumber questions sequentially
            for idx, q in enumerate(all_questions, 1):
                q['question_number'] = idx
            
            return all_questions
            
        finally:
            # Clean up temp images
            for temp_img in temp_images:
                if os.path.exists(temp_img):
                    os.remove(temp_img)
    
    def extract_questions_from_multiple_images(self, image_paths: List[str]) -> List[Dict]:
        """Extract questions from multiple image pages"""
        
        all_questions = []
        
        for image_path in image_paths:
            page_questions = self.extract_questions_from_image(image_path)
            all_questions.extend(page_questions)
        
        # Renumber questions sequentially
        for idx, q in enumerate(all_questions, 1):
            q['question_number'] = idx
        
        return all_questions
    
    def extract_questions_from_mixed_files(self, file_paths: List[str]) -> List[Dict]:
        """Extract questions from mixed file types (images and PDFs)"""
        
        all_questions = []
        
        for file_path in file_paths:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                pdf_questions = self.extract_questions_from_pdf(file_path)
                all_questions.extend(pdf_questions)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                image_questions = self.extract_questions_from_image(file_path)
                all_questions.extend(image_questions)
        
        # Renumber questions sequentially
        for idx, q in enumerate(all_questions, 1):
            q['question_number'] = idx
        
        return all_questions
    
    def _parse_questions(self, text: str) -> List[Dict]:
        """Parse questions from extracted text with section support"""
        
        # First check for section-based format
        section_questions = self._parse_section_based(text)
        if section_questions:
            return section_questions
        
        # Fallback to regular parsing
        questions = []
        lines = text.split('\n')
        
        current_question = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new question
            question_match = self._match_question_start(line)
            
            if question_match:
                # Save previous question
                if current_question:
                    question_text = ' '.join(current_text).strip()
                    current_question['question_text'] = self._preserve_math_notation(question_text)
                    current_question['has_or_option'] = self._detect_or_option(question_text)
                    questions.append(current_question)
                
                # Start new question
                current_question = {
                    'question_number': question_match['number'],
                    'marks': question_match['marks'],
                    'question_type': self._infer_question_type(question_match['marks']),
                    'has_diagram': False,
                    'section': question_match.get('section')
                }
                current_text = [question_match['text']]
            
            elif current_question:
                # Continue current question
                current_text.append(line)
        
        # Save last question
        if current_question:
            question_text = ' '.join(current_text).strip()
            current_question['question_text'] = self._preserve_math_notation(question_text)
            current_question['has_or_option'] = self._detect_or_option(question_text)
            questions.append(current_question)
        
        return questions
    
    def _match_question_start(self, line: str) -> Dict:
        """Match question start patterns including section headers"""
        
        # Section header pattern: "Section A" or "SECTION A"
        section_match = re.match(r'^SECTION\s+([A-Z])\s*[:\-]?', line, re.IGNORECASE)
        if section_match:
            return {'section': section_match.group(1), 'is_section_header': True}
        
        patterns = [
            r'^Q\.?\s*(\d+)\.?\s+(.*?)[\[\(](\d+)\s*marks?[\]\)]',
            r'^(\d+)[\.\)]\s+(.*?)[\[\(](\d+)\s*marks?[\]\)]',
            r'^Question\s+(\d+)[:\.]\s+(.*?)[-–]\s*(\d+)\s*marks?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'number': int(match.group(1)),
                    'text': match.group(2).strip(),
                    'marks': int(match.group(3))
                }
        
        # Fallback: just question number
        simple_match = re.match(r'^Q\.?\s*(\d+)\.?\s+(.+)', line, re.IGNORECASE)
        if simple_match:
            return {
                'number': int(simple_match.group(1)),
                'text': simple_match.group(2).strip(),
                'marks': 5
            }
        
        number_match = re.match(r'^(\d+)[\.\)]\s+(.+)', line)
        if number_match:
            return {
                'number': int(number_match.group(1)),
                'text': number_match.group(2).strip(),
                'marks': 5
            }
        
        return None
    
    def _infer_question_type(self, marks: int) -> str:
        """Infer question type from marks"""
        if marks <= 2:
            return "short"
        else:
            return "long"
    
    def extract_mcq_from_image(self, image_path: str) -> List[Dict]:
        """Extract MCQ questions from image"""
        
        text, _ = self.ocr_service.extract_text_from_image(image_path)
        mcqs = self._parse_mcqs(text)
        return mcqs
    
    def _parse_mcqs(self, text: str) -> List[Dict]:
        """Parse MCQ questions from text"""
        
        mcqs = []
        lines = text.split('\n')
        
        current_mcq = None
        current_options = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for question start
            q_match = re.match(r'^Q?\.?\s*(\d+)\.?\s+(.+)', line, re.IGNORECASE)
            if q_match and not re.match(r'^[A-D][\.\)]\s+', line):
                # Save previous MCQ
                if current_mcq and current_options:
                    current_mcq['options'] = current_options
                    mcqs.append(current_mcq)
                
                # Start new MCQ
                current_mcq = {
                    'question_number': int(q_match.group(1)),
                    'question_text': q_match.group(2).strip(),
                    'marks': 1,
                    'question_type': 'mcq'
                }
                current_options = {}
            
            # Check for options
            opt_match = re.match(r'^([A-D])[\.\)]\s+(.+)', line)
            if opt_match and current_mcq:
                option_letter = opt_match.group(1)
                option_text = opt_match.group(2).strip()
                current_options[option_letter] = option_text
        
        # Save last MCQ
        if current_mcq and current_options:
            current_mcq['options'] = current_options
            mcqs.append(current_mcq)
        
        return mcqs
    
    def _parse_section_based(self, text: str) -> List[Dict]:
        """Parse section-based question papers (e.g., Section A: 16x1=16 marks)"""
        
        questions = []
        lines = text.split('\n')
        current_section = None
        section_config = None
        question_counter = 1
        current_question_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match section header with marks info: "Section A (16x1=16 marks)" or "SECTION A: 16 x 1 = 16 marks"
            section_match = re.match(
                r'^SECTION\s+([A-Z])\s*[:\-]?\s*(?:\()?\s*(\d+)\s*[xX×]\s*(\d+)\s*=\s*(\d+)\s*marks?',
                line, re.IGNORECASE
            )
            
            if section_match:
                current_section = section_match.group(1)
                num_questions = int(section_match.group(2))
                marks_per_question = int(section_match.group(3))
                section_config = {
                    'section': current_section,
                    'num_questions': num_questions,
                    'marks_per_question': marks_per_question,
                    'questions_added': 0
                }
                continue
            
            # If we're in a section, try to match questions
            if section_config:
                # Simple numbered question: "1. Question text" or "1) Question text"
                q_match = re.match(r'^(\d+)[\.\)]\s+(.+)', line)
                
                if q_match:
                    # Save previous question if exists
                    if current_question_text and section_config['questions_added'] < section_config['num_questions']:
                        question_text = ' '.join(current_question_text).strip()
                        questions.append({
                            'question_number': question_counter,
                            'question_text': self._preserve_math_notation(question_text),
                            'marks': section_config['marks_per_question'],
                            'question_type': self._infer_question_type(section_config['marks_per_question']),
                            'section': section_config['section'],
                            'has_diagram': False,
                            'has_or_option': self._detect_or_option(question_text)
                        })
                        question_counter += 1
                        section_config['questions_added'] += 1
                    
                    # Start new question
                    current_question_text = [q_match.group(2).strip()]
                    
                    # Check if we've reached the section limit
                    if section_config['questions_added'] >= section_config['num_questions']:
                        section_config = None
                        current_section = None
                
                elif current_question_text:
                    # Continue current question
                    current_question_text.append(line)
        
        # Save last question
        if current_question_text and section_config and section_config['questions_added'] < section_config['num_questions']:
            question_text = ' '.join(current_question_text).strip()
            questions.append({
                'question_number': question_counter,
                'question_text': self._preserve_math_notation(question_text),
                'marks': section_config['marks_per_question'],
                'question_type': self._infer_question_type(section_config['marks_per_question']),
                'section': section_config['section'],
                'has_diagram': False,
                'has_or_option': self._detect_or_option(question_text)
            })
        
        return questions if questions else None
    
    def _preserve_math_notation(self, text: str) -> str:
        """Preserve mathematical notation like powers, subscripts, division, square roots"""
        
        # Preserve superscripts (powers): x^2, a^n
        text = re.sub(r'(\w)\^([\w\d]+)', r'\1^{\2}', text)
        
        # Preserve subscripts: H_2O, x_1
        text = re.sub(r'(\w)_([\w\d]+)', r'\1_{\2}', text)
        
        # Preserve fractions: a/b → a÷b or keep as is
        # Keep division as-is for now
        
        # Preserve square root: √ symbol
        text = text.replace('√', '√')
        
        # Preserve common math symbols
        text = text.replace('≤', '≤').replace('≥', '≥')
        text = text.replace('≠', '≠').replace('≈', '≈')
        text = text.replace('∈', '∈').replace('∉', '∉')
        text = text.replace('⊂', '⊂').replace('⊃', '⊃')
        text = text.replace('⊆', '⊆').replace('⊇', '⊇')
        text = text.replace('∪', '∪').replace('∩', '∩')
        text = text.replace('∞', '∞').replace('π', 'π')
        text = text.replace('°', '°')  # degree symbol
        
        return text
    
    def _detect_or_option(self, text: str) -> bool:
        """Detect if question has OR/Either-Or options"""
        
        # Common patterns for OR questions
        or_patterns = [
            r'\bOR\b',
            r'\bor\b',
            r'\beither\b.*\bor\b',
            r'\bEither\b.*\bor\b',
            r'\(OR\)',
            r'\[OR\]',
        ]
        
        for pattern in or_patterns:
            if re.search(pattern, text):
                return True
        
        return False
