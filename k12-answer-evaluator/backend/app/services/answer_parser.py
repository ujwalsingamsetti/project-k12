import re
import logging

logger = logging.getLogger(__name__)

class AnswerParser:
    """Parse extracted text to map answers to questions"""
    
    def parse_answers(self, text: str) -> dict:
        """Parse text and return dict of {question_number: answer_only}"""
        answers = {}
        
        # Pattern to detect question numbers: Q1, Q.1, 1), 1., Question 1, etc.
        patterns = [
            r'(?:Q\.?|Question)\s*(\d+)[:\.)\s]+(.+?)(?=(?:Q\.?|Question)\s*\d+|$)',
            r'(\d+)[:\.)\s]+(.+?)(?=\d+[:\.)\s]+|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                for q_num, content in matches:
                    # Remove question text if student rewrote it
                    answer = self._extract_answer_only(content)
                    if answer:
                        answers[int(q_num)] = answer
                break
        
        if not answers:
            # Fallback: treat entire text as answer to Q1
            answers[1] = self._extract_answer_only(text)
        
        return answers
    
    def _extract_answer_only(self, content: str) -> str:
        """Extract only the answer, removing question text if present"""
        # Remove common question patterns
        question_indicators = [
            r'^.*?(?:what|why|how|explain|describe|define|calculate|find|prove|show|derive).*?[\?\.]\s*',
            r'^.*?Answer[:\s]+',
            r'^.*?Ans[:\s]+',
            r'^.*?Solution[:\s]+',
            r'^.*?A[:\)]\s*'
        ]
        
        answer = content.strip()
        for pattern in question_indicators:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE | re.DOTALL)
        
        return answer.strip()

class AnswerSheetParser:
    """Parse answer sheets to extract questions and answers"""
    
    def __init__(self):
        logger.info("AnswerSheetParser initialized")
    
    def parse_answer_sheet(self, text: str) -> list:
        """Parse text to extract questions and answers"""
        
        if not text or not text.strip():
            logger.error("Empty text provided for parsing")
            raise ValueError("Cannot parse empty text")
        
        logger.info(f"Parsing text of length {len(text)}")
        logger.debug(f"Text preview: {text[:300]}...")
        
        questions = []
        
        # Try multiple patterns for flexibility
        patterns = [
            r'Q\)\s*(.*?)(?:\n\s*A\)\s*(.+?)(?=\n\s*Q\)|$))',  # Q) ... A) format
            r'Q\.?\s*(\d+)\.?\s*(.*?)(?=Q\.?\s*\d+|$)',  # Q1. or Q.1 or Q 1
            r'(\d+)\.\s*(.*?)(?=\d+\.|$)',  # 1. 2. 3.
            r'Question\s*(\d+)[:\.]?\s*(.*?)(?=Question\s*\d+|$)',  # Question 1:
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                logger.info(f"Found {len(matches)} questions using pattern {i}: {pattern}")
                # Special handling for Q) A) format
                if i == 0 and matches:
                    questions.append({
                        "question_number": 1,
                        "question_text": matches[0][0].strip(),
                        "student_answer": matches[0][1].strip() if len(matches[0]) > 1 else matches[0][0].strip()
                    })
                    logger.info(f"Parsed Q) A) format successfully")
                    return questions
                break
        
        if not matches:
            logger.warning("No structured questions found, attempting to extract question from text")
            
            # Try to find question keywords in the text
            question_keywords = ['what', 'why', 'how', 'explain', 'describe', 'define', 'calculate']
            lines = text.split('\n')
            question_text = "Answer"
            
            # Look for lines containing question keywords
            for line in lines[:10]:  # Check first 10 lines
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in question_keywords):
                    question_text = line.strip()
                    logger.info(f"Detected question from text: {question_text}")
                    break
            
            questions.append({
                "question_number": 1,
                "question_text": question_text,
                "student_answer": text.strip()
            })
            return questions
        
        for match in matches:
            q_num = int(match[0])
            content = match[1].strip()
            
            # Split into question and answer if possible
            answer_patterns = ['Answer:', 'Ans:', 'A:', 'Solution:']
            question_text = f"Question {q_num}"
            student_answer = content
            
            for ans_pattern in answer_patterns:
                if ans_pattern in content:
                    parts = content.split(ans_pattern, 1)
                    question_text = parts[0].strip() or f"Question {q_num}"
                    student_answer = parts[1].strip()
                    break
            
            if not student_answer:
                logger.warning(f"Q{q_num}: No answer found, using full content")
                student_answer = content
            
            questions.append({
                "question_number": q_num,
                "question_text": question_text,
                "student_answer": student_answer
            })
            
            logger.debug(f"Q{q_num}: {question_text[:50]}... | Answer: {student_answer[:50]}...")
        
        logger.info(f"Successfully parsed {len(questions)} questions")
        return questions
