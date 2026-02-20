import re

def extract_mcq_choice(student_answer: str) -> str:
    """Extract MCQ choice letter (A, B, C, D) from student answer.
    Handles formats like: A, (A), A), [A], A., 'Option A', etc.
    """
    
    if not student_answer:
        return ""
    
    # Clean and uppercase
    answer = student_answer.strip().upper()
    
    # Direct single letter match
    if answer in ['A', 'B', 'C', 'D']:
        return answer
    
    # Match any pattern where A-D appears as a standalone option indicator:
    # (A), A), [A], A., A:, "Option A", "ans: B", etc.
    # Prioritize letters that are surrounded by non-letter chars (i.e., option labels)
    match = re.search(r'(?<![A-Z])([A-D])(?![A-Z])', answer)
    if match:
        return match.group(1)
    
    # Fallback: first character if it's A-D
    if answer and answer[0] in ['A', 'B', 'C', 'D']:
        return answer[0]
    
    return ""

def extract_correct_answer(correct_answer) -> str:
    """Normalize the stored correct_answer to a single letter (A/B/C/D)."""
    if not correct_answer:
        return ""
    val = str(correct_answer).strip().upper()
    if val in ['A', 'B', 'C', 'D']:
        return val
    # Extract letter if stored as something like "(B)" or "Option C"
    match = re.search(r'([A-D])', val)
    return match.group(1) if match else val

def evaluate_mcq(question, student_answer: str) -> dict:
    """Evaluate an MCQ question.
    
    Awards full marks if the student wrote the correct option letter (A/B/C/D).
    Does NOT compare option text — only the selected letter matters.
    """
    
    student_choice = extract_mcq_choice(student_answer)
    correct_choice = extract_correct_answer(question.correct_answer)
    
    # Guard: if no correct answer stored, can't evaluate
    if not correct_choice:
        return {
            "score": 0,
            "overall_feedback": "Cannot evaluate: correct answer not set for this question.",
            "correct_points": [],
            "errors": [{"what": "No correct answer configured", "why": "Teacher must set the correct option", "impact": "Question skipped"}],
            "missing_concepts": [],
            "correct_answer_should_include": [],
            "improvement_guidance": [],
            "score_breakdown": {"correctness": 0, "completeness": 0, "understanding": 0}
        }
    
    # Lenient check: if the correct choice is IN the student's answer text at all
    # e.g., if correct is 'B' and answer is '(b) something else', or just 'B.', or 'option B'
    # We check if the letter exists as a word or option-like character
    # Get the text of the correct option for display
    correct_option_text = ""
    if hasattr(question, 'options') and isinstance(question.options, dict):
        correct_option_text = question.options.get(correct_choice, "")

    is_correct = False
    if correct_choice and student_answer:
        # Lenient check: if the correct choice is IN the student's answer text at all
        # Look for the letter bounded by anything that isn't another letter (case-insensitive)
        pattern = r"(?i)(?<![A-Z])" + correct_choice + r"(?![A-Z])"
        if re.search(pattern, student_answer) or str(correct_choice).lower() == str(student_answer).strip().lower():
             is_correct = True
        
        # Textual match check: if they wrote the full text of the option instead of the letter (e.g., 'Ragpicker')
        if not is_correct and correct_option_text:
            cleaned_correct = re.sub(r'[^a-zA-Z0-9\s]', '', correct_option_text.lower()).strip()
            cleaned_student = re.sub(r'[^a-zA-Z0-9\s]', '', student_answer.lower()).strip()
            # If the option text is meaningful (> 2 chars) and appears in the student's answer
            if cleaned_correct and len(cleaned_correct) > 2 and cleaned_correct in cleaned_student:
                is_correct = True
                student_choice = correct_choice # Fake it so the feedback makes sense
    
    marks_obtained = question.marks if is_correct else 0
    
    return {
        "score": marks_obtained,
        "overall_feedback": (
            f"Your answer: {student_choice or 'Not answered'}. "
            f"Correct answer: {correct_choice}. "
            f"{'✓ Correct!' if is_correct else '✗ Incorrect.'}"
        ),
        "correct_points": [f"Selected option {student_choice} — correct!"] if is_correct else [],
        "errors": [] if is_correct else [{
            "what": f"Selected '{student_choice or 'nothing'}' instead of '{correct_choice}'",
            "why": "Incorrect option chosen",
            "impact": "No marks awarded"
        }],
        "missing_concepts": [],
        "correct_answer_should_include": (
            [f"Option {correct_choice}: {correct_option_text}"] if correct_option_text
            else [f"Option {correct_choice}"]
        ),
        "improvement_guidance": [],
        "score_breakdown": {
            "correctness": marks_obtained,
            "completeness": 0,
            "understanding": 0
        }
    }
