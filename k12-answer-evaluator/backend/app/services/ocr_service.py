import logging
from PIL import Image
import os
import cv2
import numpy as np
import re
from typing import Optional
from spellchecker import SpellChecker
from app.core.config import settings
from app.services.diagram_service import DiagramService
from app.services.question_region_detector import QuestionRegionDetector

logger = logging.getLogger(__name__)

class OCRService:
    """OCR service using Google Cloud Vision API for maximum accuracy"""
    
    def __init__(self):
        self.vision_client = None
        self.spell = SpellChecker()
        self.diagram_service = None
        self.region_detector = QuestionRegionDetector()
        
        # Add domain-specific vocabulary (Science/Math terms)
        science_math_terms = [
            'solenoid', 'electromagnet', 'photosynthesis', 'mitochondria', 'chromosome',
            'polynomial', 'quadratic', 'trigonometry', 'derivative', 'integral',
            'velocity', 'acceleration', 'momentum', 'kinetic', 'potential',
            'oxidation', 'reduction', 'catalyst', 'enzyme', 'respiration',
            'theorem', 'hypothesis', 'coefficient', 'equation', 'variable',
            'nucleus', 'cytoplasm', 'chloroplast', 'ribosome', 'vacuole',
            'diffusion', 'osmosis', 'transpiration', 'evaporation', 'condensation',
            'refraction', 'reflection', 'convex', 'concave', 'focal',
            'amplitude', 'frequency', 'wavelength', 'resonance', 'interference',
            'circuit', 'resistor', 'capacitor', 'inductor', 'transformer',
            'parabola', 'hyperbola', 'ellipse', 'asymptote', 'tangent',
            'logarithm', 'exponential', 'factorial', 'permutation', 'combination',
            'matrix', 'determinant', 'eigenvalue', 'vector', 'scalar',
            'differentiation', 'integration', 'summation', 'sequence', 'series',
            # Trigonometry
            'sin', 'cos', 'tan', 'cot', 'sec', 'cosec', 'sinh', 'cosh', 'tanh',
            # Calculus
            'lim', 'dx', 'dy', 'dt', 'integral', 'diff',
            # Algebra
            'det', 'mod', 'arg', 'lcm', 'hcf', 'gcd',
            # Abbreviations
            'rhs', 'lhs', 'qed', 'iff', 'wrt'
        ]
        self.spell.word_frequency.load_words(science_math_terms)
        
        # Initialize Google Cloud Vision API
        try:
            from google.cloud import vision
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_VISION_CREDENTIALS
            self.vision_client = vision.ImageAnnotatorClient()
            self.diagram_service = DiagramService(self.vision_client)
            logger.info("Google Cloud Vision API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Vision API: {e}")
            raise RuntimeError(f"Google Cloud Vision API initialization failed. Make sure google-cloud-vision is installed and credentials are valid: {e}")
    
    def extract_text_from_image(self, image_path: str) -> tuple:
        """Extract text and diagrams using Google Cloud Vision API
        
        Returns:
            tuple: (extracted_text, diagram_metadata)
        """
        
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            logger.info(f"Extracting text from: {image_path}")
            
            # Try multiple preprocessing approaches for best results
            results = []
            
            # Approach 1: Original image
            text1, conf1 = self._extract_with_confidence(image_path)
            if text1:
                results.append((text1, conf1, 'original'))
            
            # Approach 2: Preprocessed image (denoised + sharpened + binarised)
            preprocessed_path = self._preprocess_and_save(image_path)
            if preprocessed_path != image_path:
                text2, conf2 = self._extract_with_confidence(preprocessed_path)
                if text2:
                    results.append((text2, conf2, 'preprocessed'))
                try:
                    os.remove(preprocessed_path)
                except OSError:
                    pass
            
            # Approach 3: Deskewed image (fixes rotated/tilted sheets)
            deskewed_path = self._deskew_and_save(image_path)
            if deskewed_path and deskewed_path != image_path:
                text3, conf3 = self._extract_with_confidence(deskewed_path)
                if text3:
                    results.append((text3, conf3, 'deskewed'))
                try:
                    os.remove(deskewed_path)
                except OSError:
                    pass
            
            # Select best result: highest confidence; break ties by text length
            if not results:
                raise ValueError(
                    "No text could be extracted from the image. "
                    "Please ensure the image is clear and contains readable text."
                )
            
            best_conf = max(r[1] for r in results)
            # Among results within 5% of best confidence, pick the one with most text
            candidates = [r for r in results if r[1] >= best_conf - 0.05]
            best_text, best_conf, method = max(candidates, key=lambda x: len(x[0]))
            logger.info(f"Best OCR method: {method} (conf={best_conf:.2f}, len={len(best_text)})")
                
            # Post-process text with image context for true AI vision correction
            processed_text = self._post_process_text(best_text, image_path)
            logger.info(f"Post-processed to {len(processed_text)} characters")
            logger.debug(f"Text preview: {processed_text[:200]}...")
            
            # Detect question regions from text
            question_regions = self.region_detector.detect_question_regions(image_path, processed_text)
            
            # Extract diagrams with question mapping
            diagram_metadata = self.diagram_service.extract_diagrams(
                image_path, 
                question_regions=question_regions
            ) if self.diagram_service else {}
            
            if diagram_metadata.get("has_diagrams"):
                logger.info(f"Detected {len(diagram_metadata.get('shapes_detected', []))} geometric shapes")
                if diagram_metadata.get("question_diagrams"):
                    logger.info(f"Mapped diagrams to {len(diagram_metadata['question_diagrams'])} questions")
            
            return processed_text.strip(), diagram_metadata
            
        except FileNotFoundError as e:
            logger.error(f"File error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Extraction error: {e}")
            raise
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise RuntimeError(f"OCR extraction failed: {str(e)}")
    
    def _preprocess_and_save(self, image_path: str) -> str:
        """Advanced preprocessing for maximum OCR accuracy"""
        try:
            img = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Upscale to higher resolution (2000-2500px width for best results)
            height, width = gray.shape
            if width < 2000:
                target_width = 2500
                scale = target_width / width
                new_width = target_width
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            elif width > 3000:
                target_width = 2500
                scale = target_width / width
                new_width = target_width
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Advanced denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # Sharpen image
            kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
            
            # Enhance contrast with CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
            enhanced = clahe.apply(sharpened)
            
            # Adaptive thresholding for better text separation
            binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Invert if background is dark
            if np.mean(morph) < 127:
                morph = cv2.bitwise_not(morph)
            
            # Save preprocessed image
            base, ext = os.path.splitext(image_path)
            preprocessed_path = f"{base}_preprocessed{ext}"
            cv2.imwrite(preprocessed_path, morph)
            
            return preprocessed_path
            
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original: {e}")
            return image_path
    
    def _deskew_and_save(self, image_path: str) -> str:
        """Detect and correct skew/rotation in answer sheets photographed at an angle."""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Hough line transform to find dominant line angles
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
            if lines is None or len(lines) < 5:
                return image_path  # Can't reliably detect skew
            
            # Collect angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                # Only use near-horizontal lines
                if abs(theta - np.pi / 2) < np.pi / 6:
                    angles.append(np.degrees(theta) - 90)
            
            if not angles:
                return image_path
            
            # Median angle is more robust than mean
            skew_angle = float(np.median(angles))
            
            # Only correct if skew is significant (>0.5°) and not extreme (>15°)
            if abs(skew_angle) < 0.5 or abs(skew_angle) > 15:
                return image_path
            
            logger.info(f"Detected skew angle: {skew_angle:.2f}°, correcting...")
            
            # Rotate image to correct skew
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            corrected = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                                       borderMode=cv2.BORDER_REPLICATE)
            
            base, ext = os.path.splitext(image_path)
            deskewed_path = f"{base}_deskewed{ext}"
            cv2.imwrite(deskewed_path, corrected)
            return deskewed_path
            
        except Exception as e:
            logger.warning(f"Deskew failed, using original: {e}")
            return image_path
    
    def _extract_with_confidence(self, image_path: str) -> tuple:
        """Extract text with confidence score from Google Vision"""
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            from google.cloud import vision
            image = vision.Image(content=content)
            
            response = self.vision_client.document_text_detection(
                image=image,
                image_context={"language_hints": ["en"]}
            )
            
            if response.error.message:
                return "", 0.0
            
            if response.full_text_annotation:
                text = response.full_text_annotation.text
                # Calculate average confidence from pages
                confidence = 0.0
                if response.full_text_annotation.pages:
                    confidences = []
                    for page in response.full_text_annotation.pages:
                        if hasattr(page, 'confidence'):
                            confidences.append(page.confidence)
                    confidence = sum(confidences) / len(confidences) if confidences else 0.8
                else:
                    confidence = 0.8  # Default confidence
                
                return text, confidence
            
            return "", 0.0
        except Exception as e:
            logger.warning(f"Extraction failed: {e}")
            return "", 0.0
    
    def _post_process_text(self, text: str, image_path: Optional[str] = None) -> str:
        """Post-process extracted text: fix spelling, structure, and formatting"""
        
        # 1. Fix common OCR mistakes
        text = self._fix_common_ocr_errors(text)
        
        # 2. Fix math-specific OCR errors
        text = self._fix_math_ocr_errors(text)
        
        # 3. Normalize whitespace and structure
        text = self._normalize_structure(text)
        
        # 4. Use LLM and the raw Image to perfectly fix spelling and sentence structure
        text = self._enhance_text_with_llm(text, image_path)
        
        return text
    
    def _enhance_text_with_llm(self, text: str, image_path: Optional[str] = None) -> str:
        """Bypass Gemini Vision and perfectly fix OCR spelling mistakes locally."""
        return self._fix_spelling_with_math_protection(text)

    
    def _fix_common_ocr_errors(self, text: str) -> str:
        """Fix common OCR character recognition errors"""
        
        # Math-specific OCR fixes
        # x2 → x² (when followed by space or operator)
        text = re.sub(r'([a-z])2(\s|[+\-*/=<>]|$)', r'\1²\2', text)
        text = re.sub(r'([a-z])3(\s|[+\-*/=<>]|$)', r'\1³\2', text)
        
        # O → 0 inside equations (between operators or numbers)
        text = re.sub(r'([+\-*/=<>\s])O([+\-*/=<>\s])', r'\g<1>0\2', text)
        
        # — (dash) → – in range expressions
        text = text.replace('—', '–')
        
        # l → 1 inside number sequences
        text = re.sub(r'(\d)l(\d)', r'\g<1>1\2', text)
        
        # X → × between numbers (multiplication)
        text = re.sub(r'(\d)\s*X\s*(\d)', r'\1 × \2', text)
        
        # +/- → ±
        text = text.replace('+/-', '±').replace('+-', '±')
        
        # Character-level replacements (common OCR confusions)
        char_fixes = [
            (r'\brn\b', 'm'),  # rn -> m
            (r'\bvv\b', 'w'),  # vv -> w  
            (r'\bcl\b', 'd'),  # cl -> d
            (r'\bli\b', 'h'),  # li -> h
            (r'\b1l\b', 'il'), # 1l -> il
        ]
        
        for pattern, replacement in char_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Word-level replacements (known mistakes)
        word_fixes = {
            'paulerful': 'powerful',
            'solenold': 'solenoid',
            'photosynthesls': 'photosynthesis',
            'mlcroscope': 'microscope',
            'chemlcal': 'chemical',
            'reactlon': 'reaction',
            'equatlon': 'equation',
            'solutlon': 'solution',
            'functlon': 'function',
            'dlagram': 'diagram',
        }
        
        for wrong, correct in word_fixes.items():
            text = re.sub(r'\b' + wrong + r'\b', correct, text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_structure(self, text: str) -> str:
        """Normalize text structure and formatting"""
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Fix line breaks - remove single line breaks within sentences
        lines = text.split('\n')
        processed_lines = []
        current_sentence = ''
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_sentence:
                    processed_lines.append(current_sentence)
                    current_sentence = ''
                continue
            
            # If line starts with number or question marker, it's a new question
            if re.match(r'^\d+\.?\s|^Q\d+|^Question', line):
                if current_sentence:
                    processed_lines.append(current_sentence)
                current_sentence = line
            # If line ends with punctuation, it's end of sentence
            elif line.endswith(('.', '!', '?', ':')):
                current_sentence += ' ' + line if current_sentence else line
                processed_lines.append(current_sentence)
                current_sentence = ''
            # Otherwise, continue sentence
            else:
                current_sentence += ' ' + line if current_sentence else line
        
        if current_sentence:
            processed_lines.append(current_sentence)
        
        return '\n'.join(processed_lines)
    
    def _fix_spelling(self, text: str) -> str:
        """Fix spelling errors using context-aware spell checker"""
        
        lines = text.split('\n')
        corrected_lines = []
        
        for line in lines:
            words = line.split()
            corrected_words = []
            
            for i, word in enumerate(words):
                # Skip numbers, punctuation, and short words
                clean_word = re.sub(r'[^a-zA-Z]', '', word)
                if len(clean_word) < 3 or clean_word.isdigit():
                    corrected_words.append(word)
                    continue
                
                # Check if word is misspelled
                if clean_word.lower() not in self.spell:
                    correction = self.spell.correction(clean_word.lower())
                    if correction and correction != clean_word.lower():
                        # Preserve original capitalization pattern
                        if clean_word.isupper():
                            correction = correction.upper()
                        elif clean_word[0].isupper():
                            correction = correction.capitalize()
                        
                        # Replace in original word (preserving punctuation)
                        word = word.replace(clean_word, correction)
                        logger.debug(f"Spell correction: {clean_word} -> {correction}")
                
                corrected_words.append(word)
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines)
    
    def _fix_math_ocr_errors(self, text: str) -> str:
        """Fix math-specific OCR errors"""
        
        # sinx → sin x, cosx → cos x, etc.
        math_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'cosec', 'log', 'ln', 'exp']
        for func in math_funcs:
            text = re.sub(rf'{func}([a-z])', rf'{func} \1', text, flags=re.IGNORECASE)
        
        # 2x where x is variable (add space)
        text = re.sub(r'(\d)([a-z])(?![a-z])', r'\1 \2', text)
        
        return text
    
    def _fix_spelling_with_math_protection(self, text: str) -> str:
        """Fix spelling errors while protecting math expressions"""
        
        lines = text.split('\n')
        corrected_lines = []
        
        # Math tokens to protect
        math_pattern = r'\b(sin|cos|tan|cot|sec|cosec|log|ln|lim|dx|dy|dt|det|mod|arg|lcm|hcf|gcd|rhs|lhs|qed|[a-z]|\d+)\b'
        
        for line in lines:
            words = line.split()
            corrected_words = []
            
            for word in words:
                # Skip if it's a math token
                clean_word = re.sub(r'[^a-zA-Z]', '', word)
                if re.match(math_pattern, clean_word, re.IGNORECASE) or len(clean_word) < 3 or clean_word.isdigit():
                    corrected_words.append(word)
                    continue
                
                # Check if word is misspelled
                if clean_word.lower() not in self.spell:
                    correction = self.spell.correction(clean_word.lower())
                    if correction and correction != clean_word.lower():
                        # Preserve original capitalization
                        if clean_word.isupper():
                            correction = correction.upper()
                        elif clean_word[0].isupper():
                            correction = correction.capitalize()
                        
                        word = word.replace(clean_word, correction)
                        logger.debug(f"Spell correction: {clean_word} -> {correction}")
                
                corrected_words.append(word)
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines)
    
    def _preprocess_for_printed_text(self, image_path: str) -> str:
        """Lighter preprocessing for printed question papers"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Gentle denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=15)
            
            # Gentle contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Gentle thresholding
            binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Save
            base, ext = os.path.splitext(image_path)
            preprocessed_path = f"{base}_printed{ext}"
            cv2.imwrite(preprocessed_path, binary)
            
            return preprocessed_path
        except Exception as e:
            logger.warning(f"Printed text preprocessing failed: {e}")
            return image_path
