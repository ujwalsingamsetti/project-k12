import re

def extract_mcq_choice(student_answer: str) -> str:
    """Extract MCQ choice (A, B, C, D) from student answer"""
    
    if not student_answer:
        return ""
    
    # Clean answer
    answer = student_answer.strip().upper()
    
    # Direct match: A, B, C, D
    if answer in ['A', 'B', 'C', 'D']:
        return answer
    
    # Match patterns: (A), A), [A], A.
    match = re.search(r'[\(\[]?([A-D])[\)\]]?', answer)
    if match:
        return match.group(1)
    
    # First letter if it's A-D
    if answer and answer[0] in ['A', 'B', 'C', 'D']:
        return answer[0]
    
    return ""

def evaluate_mcq(question, student_answer: str) -> dict:
    """Evaluate MCQ question"""
    
    student_choice = extract_mcq_choice(student_answer)
    is_correct = (student_choice == question.correct_answer)
    marks_obtained = question.marks if is_correct else 0
    
    return {
        "score": marks_obtained,
        "overall_feedback": f"Your answer: {student_choice}. Correct answer: {question.correct_answer}. {'Correct!' if is_correct else 'Incorrect.'}",
        "correct_points": [f"Selected option {student_choice}"] if is_correct else [],
        "errors": [] if is_correct else [{
            "what": f"Selected {student_choice} instead of {question.correct_answer}",
            "why": "Incorrect option",
            "impact": "No marks awarded"
        }],
        "missing_concepts": [],
        "correct_answer_should_include": [f"Option {question.correct_answer}: {question.options.get(question.correct_answer, '')}"] if question.options else [],
        "improvement_guidance": [],
        "score_breakdown": {
            "correctness": marks_obtained,
            "completeness": 0,
            "understanding": 0
        }
    }
