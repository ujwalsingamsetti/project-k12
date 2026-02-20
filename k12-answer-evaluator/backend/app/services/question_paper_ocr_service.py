import re
import logging
from typing import List, Dict, Optional, Tuple
from pdf2image import convert_from_path
import os
from app.services.ocr_service import OCRService
from app.services.diagram_service import DiagramService

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CBSE Class XII Physics (042) – standard section configuration
#
# Section A : 16 questions  × 1 mark  = 16 marks  │ 12 MCQ + 4 Assertion-Reason
# Section B :  5 questions  × 2 marks = 10 marks  │ Short  (may have OR)
# Section C :  7 questions  × 3 marks = 21 marks  │ Short  (may have OR)
# Section D :  2 questions  × 4 marks =  8 marks  │ Case study (may have OR)
# Section E :  3 questions  × 5 marks = 15 marks  │ Long   (all may have OR)
# Total     : 33 questions             = 70 marks
# ─────────────────────────────────────────────────────────────────────────────
CBSE_PHYSICS_SECTION_CONFIG = {
    'A': {
        'marks_per_question': 1,
        'num_questions': 16,
        'primary_type': 'mcq',           # first 12 are MCQ
        'ar_questions': 4,               # last 4 are Assertion-Reason
        'internal_choice': False,
    },
    'B': {
        'marks_per_question': 2,
        'num_questions': 5,
        'primary_type': 'short',
        'internal_choice': True,         # 1 question in B has OR
    },
    'C': {
        'marks_per_question': 3,
        'num_questions': 7,
        'primary_type': 'short',
        'internal_choice': True,         # 1 question in C has OR
    },
    'D': {
        'marks_per_question': 4,
        'num_questions': 2,
        'primary_type': 'case_study',
        'internal_choice': True,         # each CBQ has an internal choice
    },
    'E': {
        'marks_per_question': 5,
        'num_questions': 3,
        'primary_type': 'long',
        'internal_choice': True,         # all 3 questions in E have OR
    },
}

# Fallback marks when section header has no NxM info
CBSE_SECTION_MARKS_FALLBACK = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5,
}


class QuestionPaperOCRService:
    """
    Extract questions from CBSE Physics question papers (images / PDFs).

    Key behaviours:
    • Detects CBSE section headers in any common format.
    • Assigns the correct marks based on the section.
    • Detects MCQ vs Assertion-Reason within Section A.
    • Handles OR / internal-choice: the two alternatives become ONE question
      (question_text = "PART1\\nOR\\nPART2") with has_or_option = True.
    """

    def __init__(self):
        self.ocr_service = OCRService()
        try:
            if hasattr(self.ocr_service, 'vision_client') and self.ocr_service.vision_client:
                self.diagram_service = DiagramService(self.ocr_service.vision_client)
            else:
                self.diagram_service = None
                logger.warning("DiagramService not initialized – vision_client not available")
        except Exception as e:
            self.diagram_service = None
            logger.warning(f"DiagramService initialization failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def extract_questions_from_image(self, image_path: str) -> List[Dict]:
        text, diagram_meta = self.ocr_service.extract_text_from_image(image_path)
        questions = self._parse_questions(text)

        if diagram_meta and diagram_meta.get("has_diagrams"):
            question_diagrams = diagram_meta.get("question_diagrams", {})
            for q in questions:
                q["has_diagram"] = str(q["question_number"]) in question_diagrams

        return questions

    def extract_questions_from_pdf(self, pdf_path: str) -> List[Dict]:
        all_questions = []
        temp_images = []
        try:
            images = convert_from_path(pdf_path, dpi=300)
            temp_dir = os.path.dirname(pdf_path)
            for idx, image in enumerate(images):
                tmp = os.path.join(temp_dir, f"temp_page_{idx}.png")
                image.save(tmp, 'PNG')
                temp_images.append(tmp)
                all_questions.extend(self.extract_questions_from_image(tmp))
            for idx, q in enumerate(all_questions, 1):
                q['question_number'] = idx
            return all_questions
        finally:
            for t in temp_images:
                if os.path.exists(t):
                    os.remove(t)

    def extract_questions_from_multiple_images(self, image_paths: List[str]) -> List[Dict]:
        all_questions = []
        for path in image_paths:
            all_questions.extend(self.extract_questions_from_image(path))
        for idx, q in enumerate(all_questions, 1):
            q['question_number'] = idx
        return all_questions

    def extract_questions_from_mixed_files(self, file_paths: List[str]) -> List[Dict]:
        all_questions = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext == '.pdf':
                all_questions.extend(self.extract_questions_from_pdf(path))
            elif ext in ('.png', '.jpg', '.jpeg'):
                all_questions.extend(self.extract_questions_from_image(path))
        for idx, q in enumerate(all_questions, 1):
            q['question_number'] = idx
        return all_questions

    # ─────────────────────────────────────────────────────────────────────────
    # Core parsing
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_questions(self, text: str) -> List[Dict]:
        questions = self._parse_section_based(text)
        if questions:
            return questions
        # Fallback: assign marks by question number for physics
        questions = self._parse_plain_questions(text)
        if questions:
            # Apply physics marks structure
            for q in questions:
                q['marks'] = self._get_physics_marks_by_number(q['question_number'])
                q['question_type'] = self._infer_type_from_marks(q['marks'])
        return questions

    # ─────────────────────────────────────────────────────────────────────────
    # Section-based CBSE parser
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_section_based(self, text: str) -> Optional[List[Dict]]:
        """
        Full CBSE Physics parser.

        OR / internal-choice logic
        ──────────────────────────
        When the text between two consecutive question-start lines contains
        a standalone "OR" line, the two question texts are merged into ONE
        question dict with has_or_option=True and the question counter is NOT
        incremented for the second part (it belongs to the same question).
        """
        lines = text.split('\n')
        questions: List[Dict] = []

        current_section: Optional[str] = None
        section_cfg: Optional[Dict] = None
        section_q_count = 0          # questions finalised in current section

        # Accumulator for the current question
        cur_lines: List[str] = []    # text lines collected so far
        cur_options: Dict = {}       # MCQ option dict
        in_ar = False                # currently inside Assertion-Reason block
        after_or = False             # we just processed an OR; next q-start may be OR-alt
        or_prev_q_num: Optional[int] = None   # OCR question number before the OR line

        global_q_num = 1             # sequential output number

        def flush(is_or_alt: bool = False):
            """
            Finalise the current accumulator into a question dict.
            is_or_alt: True when this flush is for the "OR alternative" side
                       of an existing question (merges into last question).
            """
            nonlocal global_q_num, section_q_count, cur_lines, cur_options, in_ar

            if not cur_lines:
                return

            raw_text = ' '.join(cur_lines).strip()
            if not raw_text:
                cur_lines = []
                cur_options = {}
                in_ar = False
                return

            marks = section_cfg['marks_per_question'] if section_cfg else 1
            q_type = self._determine_type(
                raw_text, cur_options, marks,
                section=current_section,
                section_q_index=section_q_count,
                section_cfg=section_cfg,
            )

            if is_or_alt and questions:
                # Merge into the previous question as the OR alternative
                prev = questions[-1]
                prev['question_text'] += '\nOR\n' + self._preserve_math(raw_text)
                prev['has_or_option'] = True
                if cur_options:
                    # merge options with prefix so they don't collide
                    prev_opts = prev.get('options') or {}
                    for k, v in cur_options.items():
                        prev_opts[f"OR_{k}"] = v
                    prev['options'] = prev_opts
            else:
                # Get correct answer if detected
                correct_ans = None
                if hasattr(self, '_temp_correct') and global_q_num in self._temp_correct:
                    correct_ans = self._temp_correct.pop(global_q_num)
                
                questions.append({
                    'question_number': global_q_num,
                    'question_text': self._preserve_math(raw_text),
                    'marks': marks,
                    'question_type': q_type,
                    'section': current_section,
                    'has_diagram': False,
                    'has_or_option': False,
                    'options': cur_options if cur_options else None,
                    'correct_answer': correct_ans,
                })
                global_q_num += 1
                section_q_count += 1

            cur_lines = []
            cur_options = {}
            in_ar = False

        i = 0
        while i < len(lines):
            raw = lines[i]
            line = raw.strip()
            i += 1

            if not line:
                continue

            # ── Section header ──────────────────────────────────────────────
            sec = self._match_section_header(line)
            if sec:
                # Flush any pending question before switching sections
                flush(is_or_alt=after_or)
                after_or = False
                section_q_count = 0

                current_section = sec['section']
                marks_info = sec.get('marks_info')

                # Try next non-empty line for NxM info if not found inline
                if not marks_info:
                    for j in range(i, min(i + 4, len(lines))):
                        nxt = lines[j].strip()
                        if nxt:
                            marks_info = self._extract_marks_info(nxt)
                            if marks_info:
                                break

                defaults = CBSE_PHYSICS_SECTION_CONFIG.get(current_section, {})
                fb_marks = CBSE_SECTION_MARKS_FALLBACK.get(current_section, 1)

                section_cfg = {
                    'section': current_section,
                    'marks_per_question': (
                        marks_info['marks_per_question'] if marks_info
                        else defaults.get('marks_per_question', fb_marks)
                    ),
                    'num_questions': (
                        marks_info['num_questions'] if marks_info
                        else defaults.get('num_questions', 99)
                    ),
                    'primary_type': defaults.get('primary_type', 'short'),
                    'ar_questions': defaults.get('ar_questions', 0),
                    'internal_choice': defaults.get('internal_choice', False),
                }
                logger.info(
                    f"Section {current_section}: "
                    f"{section_cfg['marks_per_question']}m × "
                    f"{section_cfg['num_questions']}q"
                )
                continue

            # ── Skip standalone marks-spec lines (16x1=16) ─────────────────
            if self._extract_marks_info(line) and not cur_lines:
                continue

            # ── OR / internal choice line ───────────────────────────────────
            if re.match(r'^\s*(OR|or)\s*$', line):
                if section_cfg and section_cfg.get('internal_choice') and cur_lines:
                    # Flush the FIRST alternative as a normal question, remember its source number
                    flush(is_or_alt=False)
                    after_or = True   # next accumulated text is the OR-alternative
                    # or_prev_q_num is set in the qmatch branch below when we next see a Q start
                continue

            # ── Question start ──────────────────────────────────────────────
            if section_cfg:
                qmatch = self._match_question_start_line(line)
                remaining_slots = section_cfg['num_questions'] - section_q_count

                # OR-alternatives bypass the slot limit: they belong to an
                # already-counted question, so remaining_slots may be 0.
                if qmatch and (remaining_slots > 0 or after_or):
                    incoming_num = qmatch['number']

                    if after_or:
                        # This Q-start is an OR-alternative only if it has the SAME
                        # source question number as the question flushed before the OR.
                        is_same_q = (or_prev_q_num is None or incoming_num == or_prev_q_num)
                        if is_same_q:
                            # Accumulate the OR-alternative text; flush later
                            if cur_lines:
                                flush(is_or_alt=True)
                            cur_lines = [qmatch['text']]
                            cur_options = {}
                            in_ar = self._is_assertion_start(qmatch['text'])
                            # Keep after_or=True so EOF or next Q will merge it
                            continue
                        else:
                            # Different question number → flush OR-alt and start fresh
                            if cur_lines:
                                flush(is_or_alt=True)
                            after_or = False
                            or_prev_q_num = None
                            # Fall through to normal question start below only if slots remain
                            if remaining_slots <= 0:
                                continue

                    # Normal (non-OR) question start
                    if cur_lines:
                        flush(is_or_alt=False)
                    after_or = False
                    or_prev_q_num = incoming_num  # track for any subsequent OR

                    cur_lines = [qmatch['text']]
                    cur_options = {}
                    in_ar = self._is_assertion_start(qmatch['text'])
                    continue

                # ── Option lines ────────────────────────────────────────────
                if cur_lines:
                    opt_result = self._parse_options_from_line(line)
                    if opt_result:
                        if isinstance(opt_result, dict) and 'options' in opt_result:
                            cur_options.update(opt_result['options'])
                            # Track correct answer if found
                            if opt_result.get('correct') and not questions:
                                # Store for current question being built
                                if not hasattr(self, '_temp_correct'):
                                    self._temp_correct = {}
                                self._temp_correct[global_q_num] = opt_result['correct']
                        else:
                            cur_options.update(opt_result)
                        continue

                    # Assertion-Reason continuation
                    if in_ar or self._is_reason_line(line):
                        in_ar = True
                        cur_lines.append(line)
                        continue

                    # General continuation
                    cur_lines.append(line)

        # Final flush — may be an OR-alternative if we hit EOF inside an OR block
        if cur_lines:
            flush(is_or_alt=after_or)

        return questions if questions else None

    # ─────────────────────────────────────────────────────────────────────────
    # Fallback: plain numbered questions
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_plain_questions(self, text: str) -> List[Dict]:
        questions = []
        lines = text.split('\n')
        cur_q: Optional[Dict] = None
        cur_text: List[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = self._match_question_with_marks(line)
            if m:
                if cur_q:
                    qt = ' '.join(cur_text).strip()
                    cur_q['question_text'] = self._preserve_math(qt)
                    cur_q['has_or_option'] = self._detect_or(qt)
                    questions.append(cur_q)
                cur_q = {
                    'question_number': m['number'],
                    'marks': m['marks'],
                    'question_type': self._infer_type_from_marks(m['marks']),
                    'has_diagram': False,
                    'section': m.get('section'),
                    'has_or_option': False,
                    'options': None,
                    'correct_answer': None,
                }
                cur_text = [m['text']]
            elif cur_q:
                cur_text.append(line)

        if cur_q:
            qt = ' '.join(cur_text).strip()
            cur_q['question_text'] = self._preserve_math(qt)
            cur_q['has_or_option'] = self._detect_or(qt)
            questions.append(cur_q)

        return questions

    # ─────────────────────────────────────────────────────────────────────────
    # Type determination (CBSE section-aware)
    # ─────────────────────────────────────────────────────────────────────────

    def _determine_type(
        self,
        text: str,
        options: Dict,
        marks: int,
        section: Optional[str],
        section_q_index: int,
        section_cfg: Optional[Dict],
    ) -> str:
        """
        Determine question type with CBSE section knowledge.

        Section A special rules:
          • questions 0-11  (index 0–11) → MCQ
          • questions 12-15 (index 12–15) → assertion_reason
        Other sections use content signals then marks.
        """
        # ── Section A ───────────────────────────────────────────────────────
        if section == 'A':
            ar_start_idx = 12  # first 12 are MCQ, last 4 are AR
            if section_q_index >= ar_start_idx:
                return 'assertion_reason'
            # Could still be AR if content says so
            if self._is_assertion_start(text):
                return 'assertion_reason'
            return 'mcq'

        # ── Explicit MCQ options ────────────────────────────────────────────
        if options and len(options) >= 2:
            return 'mcq'
        if re.search(r'\([A-D]\)\s+\S', text):
            return 'mcq'

        # ── Assertion-Reason text signal ────────────────────────────────────
        if self._is_assertion_start(text):
            return 'assertion_reason'

        # ── Section-level primary type ───────────────────────────────────────
        if section_cfg:
            return section_cfg.get('primary_type', 'short')

        # ── Marks-based fallback ────────────────────────────────────────────
        return self._infer_type_from_marks(marks)

    def _infer_type_from_marks(self, marks: int) -> str:
        if marks == 1:
            return 'mcq'
        if marks == 4:
            return 'case_study'
        if marks >= 5:
            return 'long'
        return 'short'

    # ─────────────────────────────────────────────────────────────────────────
    # Pattern helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _match_section_header(self, line: str) -> Optional[Dict]:
        """
        Matches any of:
          [SECTION – A]   SECTION-A   SECTION A   Section  A   sec-b
        Returns {'section': 'A', 'marks_info': {...} or None}
        """
        pat = r'[\[\(]?\s*SECTION\s*[-–—]?\s*([A-E])\s*[\]\)]?'
        m = re.search(pat, line, re.IGNORECASE)
        if not m:
            return None
        return {
            'section': m.group(1).upper(),
            'marks_info': self._extract_marks_info(line),
        }

    def _extract_marks_info(self, line: str) -> Optional[Dict]:
        """Parse NxM=T  (also NXM, N×M, with optional spaces)"""
        pat = r'(\d+)\s*[xX×]\s*(\d+)\s*=\s*(\d+)'
        m = re.search(pat, line)
        if m:
            return {
                'num_questions': int(m.group(1)),
                'marks_per_question': int(m.group(2)),
                'total_marks': int(m.group(3)),
            }
        return None

    def _match_question_start_line(self, line: str) -> Optional[Dict]:
        """
        Matches: Q1.  Q1)  Q 1.  1.  1)
        Returns {'number': int, 'text': str}
        """
        patterns = [
            r'^Q\.?\s*(\d+)[\.\)]\s*(.*)',
            r'^Q\s+(\d+)[\.\)]\s*(.*)',
            r'^(\d+)[\.\)]\s+(.*)',
        ]
        for p in patterns:
            m = re.match(p, line, re.IGNORECASE)
            if m:
                return {'number': int(m.group(1)), 'text': m.group(2).strip()}
        return None

    def _match_question_with_marks(self, line: str) -> Optional[Dict]:
        """For fallback plain-question parser."""
        patterns = [
            r'^Q?\.?\s*(\d+)[\.\)]\s+(.*?)\[(\d+)\s*marks?\]',
            r'^Q?\.?\s*(\d+)[\.\)]\s+(.*?)\((\d+)\s*marks?\)',
            r'^(\d+)[\.\)]\s+(.*?)\((\d+)M\)',
            r'^(\d+)[\.\)]\s+(.*?)\s+(\d+)\s*marks?$',
        ]
        for p in patterns:
            m = re.search(p, line, re.IGNORECASE)
            if m:
                g = m.groups()
                return {'number': int(g[0]), 'text': g[1].strip(), 'marks': int(g[2])}

        simple = re.match(r'^Q?\.?\s*(\d+)[\.\)]\s+(.+)', line, re.IGNORECASE)
        if simple:
            return {'number': int(simple.group(1)), 'text': simple.group(2).strip(), 'marks': 1}
        return None

    def _parse_options_from_line(self, line: str) -> Optional[Dict]:
        """
        MCQ options in any of:
          (A) opt1  (B) opt2  (C) opt3  (D) opt4   ← all on one line
          A) opt,   A. opt                           ← one per line
          1) opt … 4) opt                            ← numbered
          
        Also detects correct answer marked with * or [✓]
        Returns: {'options': {A: text, B: text}, 'correct': 'A'}
        """
        correct_answer = None
        
        # All on one line
        multi = re.findall(r'\(([A-D])\)\s+([^(]+?)(?=\s*\([A-D]\)|$)', line)
        if multi:
            opts = {}
            for k, v in multi:
                v_clean = v.strip()
                # Check for correct answer markers
                if '*' in v_clean or '✓' in v_clean or '[✓]' in v_clean:
                    correct_answer = k
                    v_clean = re.sub(r'[*✓\[\]]', '', v_clean).strip()
                opts[k] = v_clean
            if opts:
                return {'options': opts, 'correct': correct_answer}

        single = re.match(r'^([A-D])[\.\)]\s+(.+)', line)
        if single:
            v_clean = single.group(2).strip()
            if '*' in v_clean or '✓' in v_clean or '[✓]' in v_clean:
                correct_answer = single.group(1)
                v_clean = re.sub(r'[*✓\[\]]', '', v_clean).strip()
            return {'options': {single.group(1): v_clean}, 'correct': correct_answer}

        numbered = re.match(r'^([1-4])[\.\)]\s+(.+)', line)
        if numbered:
            v_clean = numbered.group(2).strip()
            letter = chr(64 + int(numbered.group(1)))
            if '*' in v_clean or '✓' in v_clean or '[✓]' in v_clean:
                correct_answer = letter
                v_clean = re.sub(r'[*✓\[\]]', '', v_clean).strip()
            return {'options': {letter: v_clean}, 'correct': correct_answer}

        return None

    def _is_assertion_start(self, text: str) -> bool:
        return bool(re.search(r'Assertion\s*\(?A\)?[:\s]', text, re.IGNORECASE))

    def _is_reason_line(self, line: str) -> bool:
        return bool(re.search(r'^Reason\s*\(?R\)?[:\s]', line.strip(), re.IGNORECASE))

    # ─────────────────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────────────────

    def _preserve_math(self, text: str) -> str:
        text = re.sub(r'(\w)\^([\w\d]+)', r'\1^{\2}', text)
        text = re.sub(r'(\w)_([\w\d]+)', r'\1_{\2}', text)
        for fn in ('sin', 'cos', 'tan', 'cot', 'sec', 'cosec', 'log', 'ln'):
            text = re.sub(rf'{fn}\^{{?(-?\d+)}}?', rf'{fn}^\1', text)
        return text

    def _detect_or(self, text: str) -> bool:
        return bool(re.search(r'\bOR\b|\(OR\)|\[OR\]', text))
    
    def _get_physics_marks_by_number(self, q_num: int) -> int:
        """Assign marks based on question number for CBSE Physics"""
        if 1 <= q_num <= 16:
            return 1
        elif 17 <= q_num <= 21:
            return 2
        elif 22 <= q_num <= 28:
            return 3
        elif 29 <= q_num <= 30:
            return 4
        elif 31 <= q_num <= 33:
            return 5
        return 1

    # ─────────────────────────────────────────────────────────────────────────
    # MCQ-only extractor (kept for backward compat)
    # ─────────────────────────────────────────────────────────────────────────

    def extract_mcq_from_image(self, image_path: str) -> List[Dict]:
        text, _ = self.ocr_service.extract_text_from_image(image_path)
        return self._parse_mcqs(text)

    def _parse_mcqs(self, text: str) -> List[Dict]:
        mcqs = []
        lines = text.split('\n')
        cur_mcq: Optional[Dict] = None
        cur_opts: Dict = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            qm = re.match(r'^Q?\.?\s*(\d+)\.?\s+(.+)', line, re.IGNORECASE)
            if qm and not re.match(r'^[A-D][\.\)]\s+', line):
                if cur_mcq and cur_opts:
                    cur_mcq['options'] = cur_opts
                    mcqs.append(cur_mcq)
                cur_mcq = {
                    'question_number': int(qm.group(1)),
                    'question_text': qm.group(2).strip(),
                    'marks': 1,
                    'question_type': 'mcq',
                }
                cur_opts = {}
            opt = re.match(r'^([A-D])[\.\)]\s+(.+)', line)
            if opt and cur_mcq:
                cur_opts[opt.group(1)] = opt.group(2).strip()

        if cur_mcq and cur_opts:
            cur_mcq['options'] = cur_opts
            mcqs.append(cur_mcq)

        return mcqs
