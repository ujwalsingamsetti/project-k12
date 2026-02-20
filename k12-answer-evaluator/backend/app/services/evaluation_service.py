import os
import re
import json
import logging
from typing import Dict, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvaluationService:
    """Gemini-based answer evaluation service (FREE tier)"""
    
    def __init__(self):
        """Initialize the Gemini client using the new SDK"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file. Get free key from https://aistudio.google.com/app/apikey")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-pro'
        logger.info(f"✅ Initialized GenAI client with {self.model_name}")
    
    def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        textbook_context: str,
        subject: str,
        class_level: str = "12",
        max_score: int = 10,
        diagram_info: dict = None,
        marking_scheme: dict = None,
        rag_scores: List[float] = None
    ) -> Dict:
        """Evaluate student answer using Gemini API"""
        
        logger.info(f"Evaluating {subject} Q (max: {max_score} marks)")
        
        try:
            prompt = self._create_prompt(
                question, student_answer, textbook_context,
                subject, max_score, class_level, marking_scheme
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            raw_response = response.text
            evaluation = self._parse_response(raw_response, max_score)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                evaluation, student_answer, rag_scores or [], marking_scheme
            )
            
            # Apply confidence-based leniency overrides
            original_score = float(evaluation.get("score", 0))
            if confidence > 0.65:
                evaluation["score"] = max_score
                logger.info(f"Confidence {confidence:.2f} > 0.65: Boosted score from {original_score} to {max_score}")
            elif confidence > 0.50:
                boosted_score = max(0, max_score - 1)
                evaluation["score"] = max(original_score, boosted_score)
                logger.info(f"Confidence {confidence:.2f} > 0.50: Boosted score from {original_score} to {evaluation['score']}")
            elif confidence > 0.30:
                boosted_score = max_score / 2.0
                evaluation["score"] = max(original_score, boosted_score)
                logger.info(f"Confidence {confidence:.2f} > 0.30: Boosted score from {original_score} to {evaluation['score']}")
            elif confidence > 0.20:
                boosted_score = max(0, (max_score / 2.0) - 1.0) # Gives less than half mark
                evaluation["score"] = max(original_score, boosted_score)
                logger.info(f"Confidence {confidence:.2f} > 0.20: Boosted score from {original_score} to {evaluation['score']}")
            
            evaluation["confidence"] = confidence
            evaluation["metadata"] = {
                "model": self.model_name,
                "provider": "google",
                "confidence": confidence
            }
            
            logger.info(f"✅ Score: {evaluation['score']}/{max_score}, Confidence: {confidence:.2f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Gemini evaluation failed: {e}")
            return self._create_fallback_evaluation(max_score, str(e))
    
    def _create_prompt(self, question, student_answer, textbook_context, 
                      subject, max_score, class_level, marking_scheme):
        """Create evaluation prompt"""
        
        correctness = int(max_score * 0.5)
        completeness = int(max_score * 0.3)
        understanding = max_score - correctness - completeness
        
        marking_text = ""
        if marking_scheme:
            marking_text = "\n\nMARKING SCHEME:\n"
            for item in marking_scheme.get("breakdown", []):
                marking_text += f"- {item['point']} ({item['marks']} mark)\n"
            if "keywords" in marking_scheme:
                marking_text += f"\nKeywords: {', '.join(marking_scheme['keywords'])}\n"
        
        return f"""You are a very lenient and supportive CBSE Class {class_level} {subject} teacher.
        
Goal: Help the student succeed. If the student shows even a partial understanding or mentions relevant keywords, be generous with marks. 

QUESTION:
{question}
{marking_text}

REFERENCE:
{textbook_context}

STUDENT ANSWER:
{student_answer}

Evaluate and return ONLY valid JSON:

{{
  "score": <0-{max_score}>,
  "score_breakdown": {{"correctness": <0-{correctness}>, "completeness": <0-{completeness}>, "understanding": <0-{understanding}>}},
  "correct_points": ["What they got right"],
  "errors": [{{"what": "mistake", "why": "reason", "impact": "minor reduction"}}],
  "missing_concepts": ["Concepts to review"],
  "correct_answer_should_include": ["Expected points"],
  "improvement_guidance": [{{"suggestion": "Encouraging tip", "resource": "Chapter", "practice": "Exercise"}}],
  "overall_feedback": "Helpful, lenient summary."
}}

Return ONLY the JSON, no other text."""
    
    def _parse_response(self, text: str, max_score: int) -> Dict:
        """Parse Gemini response"""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                evaluation = json.loads(json_str)
                
                # Validate
                if 0 <= evaluation.get('score', -1) <= max_score:
                    return evaluation
            
            return self._create_fallback_evaluation(max_score, "Invalid JSON")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._create_fallback_evaluation(max_score, str(e))
    
    def _calculate_confidence(self, evaluation, student_answer, rag_scores, marking_scheme):
        """Calculate confidence score"""
        factors = []
        
        # RAG relevance (40%)
        if rag_scores:
            factors.append(sum(rag_scores) / len(rag_scores) * 0.4)
        else:
            factors.append(0.2)
        
        # Answer length (20%)
        expected_len = evaluation.get('max_score', 10) * 30
        actual_len = len(student_answer.strip())
        if actual_len > 0:
            factors.append(min(actual_len / expected_len, 1.0) * 0.2)
        
        # Keywords (20%)
        if marking_scheme and 'keywords' in marking_scheme:
            keywords = marking_scheme['keywords']
            answer_lower = student_answer.lower()
            found = sum(1 for kw in keywords if kw.lower() in answer_lower)
            factors.append((found / len(keywords)) * 0.2 if keywords else 0.1)
        else:
            factors.append(0.1)
        
        # Score consistency (20%)
        score = evaluation.get('score', 0)
        breakdown = evaluation.get('score_breakdown', {})
        if abs(score - sum(breakdown.values())) <= 1:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        return round(min(sum(factors), 1.0), 2)
    
    def _create_fallback_evaluation(self, max_score: int, error: str) -> Dict:
        """Fallback evaluation"""
        return {
            "score": max_score // 2,
            "score_breakdown": {
                "correctness": max_score // 4,
                "completeness": max_score // 6,
                "understanding": max_score // 4
            },
            "correct_points": ["Unable to analyze automatically"],
            "errors": [{"what": "Evaluation failed", "why": error, "impact": "Manual review needed"}],
            "missing_concepts": ["Manual review required"],
            "correct_answer_should_include": ["Review textbook"],
            "improvement_guidance": [{"suggestion": "Manual review", "resource": "Textbook", "practice": "Practice"}],
            "overall_feedback": "Manual teacher review recommended.",
            "confidence": 0.3,
            "metadata": {"error": True, "error_message": error}
        }
