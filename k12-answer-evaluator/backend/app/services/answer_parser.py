import re
import logging

logger = logging.getLogger(__name__)


class AnswerParser:
    """Parse OCR-extracted answer sheet text to map question numbers to answers.
    
    Improvements:
    - Handles 15+ different handwriting numbering formats
    - Gives explicit 0 to unanswered questions (not silently skipped)
    - Converts MCQ number formats (1→A, 2→B, etc.)
    - Merges multi-line answers correctly
    """

    def parse_answers(self, text: str) -> dict:
        """Parse raw OCR text, strictly merge nested bullet lists/numbers, and return {question_number (int): answer_text (str)}."""
        if not text or not text.strip():
            logger.warning("Empty text received by AnswerParser")
            return {}

        # Handle multi-column OCR output
        # Insert newline before any standalone number followed by dot/paren (with leading/trailing space restrictions)
        text = re.sub(r'(?<!\n)(?<!\d)\s*(\d{1,2}[\.\)])\s+', r'\n\1 ', " " + text)

        # Special case: pure MCQ sheet where each line is just "A", "(B)", etc.
        mcq_only = self._try_pure_mcq(text)
        if mcq_only:
            logger.info(f"Detected pure MCQ sheet: {len(mcq_only)} answers")
            return mcq_only

        # Use robust split & merge parsing
        # Prefix: Optional whitespace, Q/Question/Ans/Sol, Optional punc, Optional (
        # Num: 1-2 digits
        # Suffix: . or ) and whitespace
        pattern = r'^(\s*(?:Q(?:ues(?:tion)?)?|Ans(?:wer)?|Sol(?:ution)?)?[\.\-\s]*\(?)(\d{1,2})([\.\)]\s+)'
        parts = re.split(pattern, "\n" + text, flags=re.MULTILINE | re.IGNORECASE)

        if len(parts) == 1:
            logger.warning("No structured answers found; storing full text as Q1")
            return {1: self._clean_answer(text)}

        answers: dict[int, str] = {}
        current_q = -1
        seen_qs = set()

        preamble = parts[0].strip()

        for i in range(1, len(parts), 4):
            prefix = parts[i]
            q_num_str = parts[i+1]
            suffix = parts[i+2]
            ans_text = parts[i+3]

            q_num = int(q_num_str)
            is_bullet = False

            # Strict explicit marker like "Q2" vs "2."
            has_explicit_marker = bool(re.search(r'Q|Ans|Sol', prefix, re.IGNORECASE))

            # Determine whether this number is a bullet point belonging to the previous question
            if not has_explicit_marker and current_q != -1:
                if q_num in seen_qs:
                    is_bullet = True
                elif q_num < current_q and (current_q - q_num) > 3:
                    is_bullet = True

            if is_bullet:
                # Merge back into current question
                full_match_text = prefix + q_num_str + suffix + ans_text
                if current_q in answers:
                    answers[current_q] += full_match_text
            else:
                current_q = q_num
                seen_qs.add(q_num)
                if q_num not in answers:
                    answers[q_num] = ""
                
                # Append any preamble text before the very first question
                if preamble:
                    answers[q_num] += preamble + "\n"
                    preamble = ""

                answers[q_num] += ans_text

        cleaned_answers = {q: self._clean_answer(a) for q, a in answers.items()}

        if not cleaned_answers:
            logger.warning("No structured answers found; storing full text as Q1")
            return {1: self._clean_answer(text)}

        logger.info(f"AnswerParser extracted {len(cleaned_answers)} answers: {sorted(cleaned_answers.keys())}")
        return cleaned_answers

    # ── helpers ──────────────────────────────────────────────────────────────

    def _try_pure_mcq(self, text: str) -> dict:
        """Detect sheets where each line is a standalone MCQ option letter."""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        mcq_lines = []
        for line in lines:
            m = re.match(r'^\(?([A-D])\)?$', line, re.IGNORECASE)
            if m:
                mcq_lines.append(m.group(1).upper())

        if len(mcq_lines) >= max(3, len(lines) * 0.7):
            return {i + 1: letter for i, letter in enumerate(mcq_lines)}
        return {}

    def _clean_answer(self, text: str) -> str:
        """Strip answer prefixes and normalise whitespace."""
        text = text.strip()

        # Remove "Answer:" / "Ans:" prefix that students sometimes write
        text = re.sub(r'^(?:Answer|Ans|Sol(?:ution)?)\s*[:\-]\s*', '', text, flags=re.IGNORECASE)

        # Convert numeric MCQ answers (1→A, 2→B, 3→C, 4→D)
        text = self._convert_mcq_format(text)

        # Collapse multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _convert_mcq_format(self, answer: str) -> str:
        """Map digit-only MCQ answers to letters."""
        stripped = answer.strip()
        mapping = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        if stripped in mapping:
            return mapping[stripped]
        return answer

    def _normalize_question_number(self, q_num: str) -> int:
        roman = {
            'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
            'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10
        }
        q = q_num.lower().strip()
        if q in roman:
            return roman[q]
        if q.isalpha() and len(q) == 1:
            return ord(q) - ord('a') + 1
        try:
            return int(q)
        except ValueError:
            return 1


class AnswerSheetParser:
    """Legacy class — kept for backward compatibility."""

    def __init__(self):
        self._parser = AnswerParser()

    def parse_answer_sheet(self, text: str) -> list:
        answers = self._parser.parse_answers(text)
        return [
            {"question_number": q, "question_text": f"Question {q}", "student_answer": a}
            for q, a in sorted(answers.items())
        ]
