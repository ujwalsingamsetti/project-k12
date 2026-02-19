import os
import json
import logging
from typing import Dict, List, Optional, Callable
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvaluationService:
    """LLM-based answer evaluation service optimized for Llama 3.2:3b via Ollama"""
    
    EVALUATION_PROMPT = """You are a {subject} teacher evaluating a Class {class_level} student's answer.

Question: {question}

Textbook Reference:
{textbook_context}

Student Answer:
{student_answer}

Evaluate and return JSON:
{{
  "score": <0-{max_score}>,
  "score_breakdown": {{"correctness": <0-{correctness_points}>, "completeness": <0-{completeness_points}>, "understanding": <0-{understanding_points}>}},
  "correct_points": ["what student got right"],
  "errors": [{{"what": "error", "why": "reason", "impact": "effect"}}],
  "missing_concepts": ["missing key points"],
  "correct_answer_should_include": ["essential points"],
  "improvement_guidance": [{{"suggestion": "how to improve", "resource": "where to study", "practice": "exercise"}}],
  "overall_feedback": "summary"
}}

Return only valid JSON."""
    
    def __init__(self):
        """Initialize evaluation service with local LLM configuration"""
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "not-needed")
        )
        self.model = os.getenv("OPENAI_MODEL", "llama3.2:3b")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        logger.info(f"Initialized EvaluationService with {self.model} via Ollama")
    
    def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        textbook_context: str,
        subject: str,
        class_level: str = "10",
        max_score: int = 10,
        diagram_info: dict = None
    ) -> Dict:
        """Evaluate student answer using local LLM with optional diagram context"""
        
        logger.info(f"Evaluating {subject} question...")
        logger.debug(f"Question: {question[:100]}...")
        logger.debug(f"Student answer: {student_answer[:100]}...")
        
        # Add diagram context if available
        diagram_context = ""
        if diagram_info and diagram_info.get("has_diagrams"):
            shapes = diagram_info.get("shapes_detected", [])
            if shapes:
                shape_list = ", ".join([s.get("type", "unknown") for s in shapes])
                diagram_context = f"\n\nDIAGRAM DETECTED: Student included geometric shapes: {shape_list}"
                logger.info(f"Including diagram context: {shape_list}")
        
        try:
            prompt = self._create_evaluation_prompt(
                question=question,
                student_answer=student_answer + diagram_context,
                textbook_context=self._optimize_context_length(textbook_context),
                subject=subject,
                max_score=max_score,
                class_level=class_level
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert teacher who evaluates student answers and provides constructive feedback in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            raw_response = response.choices[0].message.content
            evaluation = self._parse_evaluation_response(raw_response, max_score)
            
            evaluation["metadata"] = {
                "model": self.model,
                "tokens_used": getattr(response.usage, 'total_tokens', 0),
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(response.usage, 'completion_tokens', 0)
            }
            
            logger.info(f"Evaluation complete. Score: {evaluation['score']}/{max_score}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            return self._create_fallback_evaluation(max_score, str(e))
    
    def evaluate_answer_with_retry(
        self,
        question: str,
        student_answer: str,
        textbook_context: str,
        subject: str,
        max_score: int = 10,
        max_retries: int = 2
    ) -> Dict:
        """Evaluate with retry logic for local LLM failures"""
        
        for attempt in range(max_retries + 1):
            try:
                evaluation = self.evaluate_answer(
                    question=question,
                    student_answer=student_answer,
                    textbook_context=textbook_context,
                    subject=subject,
                    max_score=max_score
                )
                
                if self._validate_evaluation(evaluation, max_score):
                    return evaluation
                else:
                    logger.warning(f"Invalid evaluation on attempt {attempt + 1}")
                    if attempt == max_retries:
                        return self._create_fallback_evaluation(max_score, "Max retries exceeded")
                        
            except Exception as e:
                logger.error(f"Evaluation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries:
                    return self._create_fallback_evaluation(max_score, str(e))
                
                import time
                time.sleep(1)
        
        return self._create_fallback_evaluation(max_score, "All retry attempts failed")
    
    def evaluate_answer_sheet_with_progress(
        self,
        questions_data: List[Dict],
        subject: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict:
        """
        Evaluate with progress callbacks for UI updates.
        
        Args:
            questions_data: List of question dicts
            subject: Subject name
            progress_callback: Function called with (current, total) after each question
        """
        
        evaluations = []
        total = len(questions_data)
        
        for idx, q_data in enumerate(questions_data, 1):
            evaluation = self.evaluate_answer_with_retry(
                question=q_data['question_text'],
                student_answer=q_data['student_answer'],
                textbook_context=q_data['textbook_context'],
                subject=subject,
                max_score=q_data.get('max_score', 10)
            )
            
            evaluation['question_number'] = q_data['question_number']
            evaluation['question_text'] = q_data['question_text']
            evaluation['student_answer'] = q_data['student_answer']
            evaluations.append(evaluation)
            
            if progress_callback:
                progress_callback(idx, total)
        
        total_score = sum(e['score'] for e in evaluations)
        max_possible = sum(e.get('max_score', 10) for e in evaluations)
        percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        summary = self._generate_overall_summary(evaluations, subject, percentage)
        
        return {
            "evaluations": evaluations,
            "overall_score": total_score,
            "max_possible_score": max_possible,
            "percentage": round(percentage, 2),
            "total_questions": total,
            "summary": summary
        }
    
    def batch_evaluate(
        self,
        questions_answers: List[Dict],
        subject: str,
        class_level: str = "10",
        max_score: int = 10
    ) -> Dict:
        """Evaluate multiple answers in batch"""
        results = []
        
        for idx, qa in enumerate(questions_answers, 1):
            logger.info(f"Evaluating question {idx}/{len(questions_answers)}")
            
            evaluation = self.evaluate_answer(
                question=qa["question"],
                student_answer=qa["student_answer"],
                textbook_context=qa.get("textbook_context", ""),
                subject=subject,
                class_level=class_level,
                max_score=max_score
            )
            
            evaluation["question_number"] = idx
            results.append(evaluation)
        
        total_score = sum(r["score"] for r in results)
        max_total = max_score * len(questions_answers)
        
        return {
            "evaluations": results,
            "summary": {
                "total_questions": len(questions_answers),
                "total_score": total_score,
                "max_total_score": max_total,
                "percentage": round((total_score / max_total) * 100, 2) if max_total > 0 else 0
            }
        }
    
    def evaluate_answer_sheet(
        self,
        questions_data: List[Dict],
        subject: str
    ) -> Dict:
        """
        Evaluate multiple questions from an answer sheet.
        
        For local LLM (Llama 3.2:3b), we evaluate questions sequentially
        rather than in a single batch to avoid context length issues.
        
        Args:
            questions_data: List of dicts with keys:
                - question_number: int
                - question_text: str
                - student_answer: str
                - textbook_context: str (from RAG)
                - max_score: int (optional, default 10)
            subject: Subject name
        
        Returns:
            Dict with overall results and individual evaluations
        """
        
        logger.info(f"Starting batch evaluation for {len(questions_data)} questions")
        
        evaluations = []
        total_score = 0
        max_possible_score = 0
        
        for idx, q_data in enumerate(questions_data, 1):
            try:
                logger.info(f"Evaluating question {idx}/{len(questions_data)}")
                
                max_score = q_data.get('max_score', 10)
                
                evaluation = self.evaluate_answer(
                    question=q_data['question_text'],
                    student_answer=q_data['student_answer'],
                    textbook_context=q_data['textbook_context'],
                    subject=subject,
                    max_score=max_score
                )
                
                evaluation['question_number'] = q_data['question_number']
                evaluation['question_text'] = q_data['question_text']
                evaluation['student_answer'] = q_data['student_answer']
                evaluation['max_score'] = max_score
                
                evaluations.append(evaluation)
                
                total_score += evaluation['score']
                max_possible_score += max_score
                
            except Exception as e:
                logger.error(f"Error evaluating question {idx}: {str(e)}")
                fallback = self._create_fallback_evaluation(q_data.get('max_score', 10), str(e))
                fallback['question_number'] = q_data['question_number']
                fallback['question_text'] = q_data['question_text']
                fallback['student_answer'] = q_data['student_answer']
                evaluations.append(fallback)
        
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        overall_summary = self._generate_overall_summary(evaluations, subject, percentage)
        
        return {
            "evaluations": evaluations,
            "overall_score": total_score,
            "max_possible_score": max_possible_score,
            "percentage": round(percentage, 2),
            "total_questions": len(questions_data),
            "summary": overall_summary
        }
    
    def _parse_evaluation_response(self, raw_response: str, max_score: int) -> Dict:
        """Parse LLM response and extract JSON"""
        
        try:
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                evaluation = json.loads(json_str)
                
                if self._validate_evaluation(evaluation, max_score):
                    return evaluation
                else:
                    logger.warning("Invalid evaluation structure, using fallback")
                    return self._create_fallback_evaluation(max_score, "Invalid structure")
            else:
                logger.warning("No JSON found in response")
                return self._create_fallback_evaluation(max_score, "No JSON found")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return self._create_fallback_evaluation(max_score, str(e))
    
    def _validate_evaluation(self, evaluation: Dict, max_score: int) -> bool:
        """Validate evaluation structure and content"""
        
        required_fields = [
            'score', 'score_breakdown', 'correct_points', 'errors',
            'missing_concepts', 'correct_answer_should_include',
            'improvement_guidance', 'overall_feedback'
        ]
        
        if not all(field in evaluation for field in required_fields):
            return False
        
        if not (0 <= evaluation['score'] <= max_score):
            return False
        
        breakdown = evaluation.get('score_breakdown', {})
        if not all(key in breakdown for key in ['correctness', 'completeness', 'understanding']):
            return False
        
        return True
    
    def _validate_and_fix_evaluation(self, evaluation: Dict, max_score: int) -> Dict:
        """Validate and fix evaluation structure"""
        if "score" not in evaluation:
            evaluation["score"] = max_score // 2
        
        evaluation["score"] = min(max(0, evaluation["score"]), max_score)
        
        if "score_breakdown" not in evaluation:
            evaluation["score_breakdown"] = {
                "correctness": 0,
                "completeness": 0,
                "understanding": 0
            }
        
        if "correct_points" not in evaluation:
            evaluation["correct_points"] = []
        
        if "errors" not in evaluation:
            evaluation["errors"] = []
        
        if "missing_concepts" not in evaluation:
            evaluation["missing_concepts"] = []
        
        if "correct_answer_should_include" not in evaluation:
            evaluation["correct_answer_should_include"] = []
        
        if "improvement_guidance" not in evaluation:
            evaluation["improvement_guidance"] = []
        
        if "overall_feedback" not in evaluation:
            evaluation["overall_feedback"] = "Evaluation completed."
        
        return evaluation
    
    def _create_fallback_evaluation(self, max_score: int, error_msg: str) -> Dict:
        """Create fallback evaluation if LLM fails"""
        
        return {
            "score": max_score // 2,
            "score_breakdown": {
                "correctness": (max_score // 2) // 2,
                "completeness": (max_score // 2) // 3,
                "understanding": (max_score // 2) - (max_score // 2) // 2 - (max_score // 2) // 3
            },
            "correct_points": ["Unable to analyze answer automatically"],
            "errors": [
                {
                    "what": "Automatic evaluation failed",
                    "why": error_msg,
                    "impact": "Manual review recommended"
                }
            ],
            "missing_concepts": ["Manual review needed"],
            "correct_answer_should_include": ["Please review textbook material"],
            "improvement_guidance": [
                {
                    "suggestion": "Manual review by teacher recommended",
                    "resource": "Refer to relevant textbook chapters",
                    "practice": "Practice more questions on this topic"
                }
            ],
            "overall_feedback": "This answer requires manual teacher review for accurate evaluation.",
            "metadata": {
                "error": True,
                "error_message": error_msg
            }
        }
    
    def _create_evaluation_prompt(
        self,
        question: str,
        student_answer: str,
        textbook_context: str,
        subject: str,
        max_score: int,
        class_level: str = "12"
    ) -> str:
        """Create optimized prompt for Llama 3.1"""
        
        correctness_points = int(max_score * 0.5)
        completeness_points = int(max_score * 0.3)
        understanding_points = max_score - correctness_points - completeness_points
        
        prompt = f"""You are a {subject} teacher evaluating a Class {class_level} CBSE student's answer.

QUESTION:
{question}

TEXTBOOK REFERENCE:
{textbook_context}

STUDENT'S ANSWER:
{student_answer}

TASK:
Evaluate the student's answer and provide detailed feedback.

SCORING (Total: {max_score} points):
- Correctness: {correctness_points} points (accuracy of facts)
- Completeness: {completeness_points} points (all key points covered)
- Understanding: {understanding_points} points (conceptual clarity)

OUTPUT FORMAT:
Provide your evaluation as a JSON object with this EXACT structure:

{{
  "score": <number between 0 and {max_score}>,
  "score_breakdown": {{
    "correctness": <0 to {correctness_points}>,
    "completeness": <0 to {completeness_points}>,
    "understanding": <0 to {understanding_points}>
  }},
  "correct_points": [
    "Point 1 the student got correct",
    "Point 2 the student got correct"
  ],
  "errors": [
    {{
      "what": "Specific error description",
      "why": "Why this is incorrect",
      "impact": "How this affects understanding"
    }}
  ],
  "missing_concepts": [
    "Key concept 1 not mentioned",
    "Key concept 2 not mentioned"
  ],
  "correct_answer_should_include": [
    "Essential point 1",
    "Essential point 2",
    "Essential point 3"
  ],
  "improvement_guidance": [
    {{
      "suggestion": "Specific improvement action",
      "resource": "Textbook chapter/page reference",
      "practice": "Practice recommendation"
    }}
  ],
  "overall_feedback": "Brief encouraging summary in 1-2 sentences"
}}

IMPORTANT:
- Respond ONLY with the JSON object
- Do not include any text before or after the JSON
- Ensure all scores sum correctly
- Be constructive and specific in feedback
- Reference the textbook content provided above

JSON Response:"""
        
        return prompt
    
    def _get_subject_specific_instructions(self, subject: str) -> str:
        """Get subject-specific evaluation guidelines"""
        
        if subject.lower() == "science":
            return """
For Science answers, focus on:
- Correct terminology and definitions
- Accurate processes and mechanisms
- Correct chemical equations/formulas (if applicable)
- Understanding of cause and effect
- Real-world applications mentioned
"""
        elif subject.lower() == "mathematics":
            return """
For Mathematics answers, focus on:
- Correct formula usage
- Proper mathematical steps shown
- Accurate calculations
- Correct final answer
- Clear reasoning and logic
"""
        else:
            return ""
    
    def _generate_overall_summary(self, evaluations: List[Dict], subject: str, percentage: float) -> Dict:
        """Generate overall performance summary"""
        
        all_correct_points = []
        all_errors = []
        all_missing_concepts = []
        
        for eval in evaluations:
            all_correct_points.extend(eval.get('correct_points', []))
            all_errors.extend([e['what'] for e in eval.get('errors', []) if isinstance(e, dict)])
            all_missing_concepts.extend(eval.get('missing_concepts', []))
        
        strengths = self._identify_strengths(all_correct_points, evaluations)
        areas_for_improvement = self._identify_improvement_areas(all_missing_concepts, all_errors)
        recommended_practice = self._generate_practice_recommendations(areas_for_improvement, subject)
        
        if percentage >= 80:
            performance_level = "Excellent"
            message = "Outstanding work! You have demonstrated strong understanding of the concepts."
        elif percentage >= 60:
            performance_level = "Good"
            message = "Good effort! You understand most concepts but there's room for improvement."
        elif percentage >= 40:
            performance_level = "Needs Improvement"
            message = "You have basic understanding but need to strengthen several concepts."
        else:
            performance_level = "Needs Significant Improvement"
            message = "This topic needs more attention. Please review the textbook and practice more."
        
        return {
            "performance_level": performance_level,
            "overall_message": message,
            "strengths": strengths[:5],
            "areas_for_improvement": areas_for_improvement[:5],
            "recommended_practice": recommended_practice
        }
    
    def _identify_strengths(self, correct_points: List[str], evaluations: List[Dict]) -> List[str]:
        """Identify student's strengths from correct points"""
        
        if not correct_points:
            return ["Showed effort in attempting the questions"]
        
        unique_strengths = list(set([point.strip() for point in correct_points if point.strip()]))
        
        return unique_strengths[:5] if len(unique_strengths) > 5 else unique_strengths
    
    def _identify_improvement_areas(self, missing_concepts: List[str], errors: List[str]) -> List[str]:
        """Identify areas needing improvement"""
        
        all_issues = missing_concepts + errors
        
        if not all_issues:
            return ["Continue practicing to maintain consistency"]
        
        unique_issues = list(set([issue.strip() for issue in all_issues if issue.strip()]))
        
        return unique_issues[:5] if len(unique_issues) > 5 else unique_issues
    
    def _generate_practice_recommendations(self, improvement_areas: List[str], subject: str) -> List[Dict]:
        """Generate practice recommendations based on weak areas"""
        
        if subject.lower() == "science":
            return [
                {
                    "topic": "Review key concepts",
                    "action": "Re-read relevant textbook chapters",
                    "resource": "NCERT Science Textbook - Specific chapters based on questions"
                },
                {
                    "topic": "Practice diagrams",
                    "action": "Draw and label important diagrams",
                    "resource": "Practice from textbook exercises"
                },
                {
                    "topic": "Memorize key terms",
                    "action": "Create flashcards for definitions",
                    "resource": "Chapter summaries and glossary"
                }
            ]
        elif subject.lower() == "mathematics":
            return [
                {
                    "topic": "Formula practice",
                    "action": "Write and memorize all relevant formulas",
                    "resource": "NCERT Math Textbook - Formula sheet"
                },
                {
                    "topic": "Problem solving",
                    "action": "Solve 10 similar practice problems",
                    "resource": "Textbook exercises and examples"
                },
                {
                    "topic": "Step-by-step solutions",
                    "action": "Practice showing all working steps clearly",
                    "resource": "Solved examples from textbook"
                }
            ]
        
        return [
            {
                "topic": "General practice",
                "action": "Review textbook and solve practice problems",
                "resource": "NCERT Textbook exercises"
            }
        ]
    
    def _optimize_context_length(self, textbook_context: str, max_chars: int = 800) -> str:
        """
        Truncate textbook context to fit within token limits.
        Llama 3.2:3b works best with shorter contexts.
        """
        
        if len(textbook_context) <= max_chars:
            return textbook_context
        
        truncated = textbook_context[:max_chars]
        last_period = truncated.rfind('.')
        
        if last_period > max_chars * 0.7:
            return truncated[:last_period + 1]
        else:
            return truncated + "..."

