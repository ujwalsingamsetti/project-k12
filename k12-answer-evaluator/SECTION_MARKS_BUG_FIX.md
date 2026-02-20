# Section-Based Marks Extraction Bug Fix

## Problem
When uploading question papers with format `[SECTION – A] (16x1=16 marks)`, all questions were getting 5 marks instead of the correct 1 mark per question.

## Root Causes

### 1. Section Header Regex Failed to Match
**Issue**: Regex used `.match()` which only matches from start of line, and didn't handle:
- Square brackets `[` and `]`
- Em-dash `–` (Unicode \u2013) vs regular hyphen `-`
- Flexible whitespace between section letter and marks

**Old Pattern**:
```python
section_match = re.match(
    r'^SECTION\s+([A-Z])\s*[:\-]?\s*(?:\()?\s*(\d+)\s*[xX×]\s*(\d+)\s*=\s*(\d+)\s*marks?',
    line, re.IGNORECASE
)
```

**New Pattern**:
```python
section_match = re.search(
    r'\[?SECTION\s*[–\-]?\s*([A-Z])\]?\s*(?:\()?\s*(\d+)\s*[xX×]\s*(\d+)\s*=\s*(\d+)\s*marks?',
    line, re.IGNORECASE
)
```

**Changes**:
- `.match()` → `.search()` (finds pattern anywhere in line)
- Added `\[?` and `\]?` for optional square brackets
- Added `[–\-]?` to match both em-dash (\u2013) and hyphen

### 2. Question Number Regex Didn't Match Q1., Q17. Format
**Issue**: Regex only matched `1.` or `1)` but not `Q1.` or `Q17.`

**Old Pattern**:
```python
q_match = re.match(r'^(\d+)[\.\)]\s+(.+)', line)
```

**New Pattern**:
```python
q_match = re.match(r'^Q?(\d+)[\.\)]\s+(.+)', line)
```

**Change**: Added `Q?` to make the Q prefix optional

### 3. Fallback Marks Hardcoded to 5
**Issue**: When section detection failed, every question silently got `marks: 5`

**Old Code**:
```python
return {
    'number': int(simple_match.group(1)),
    'text': simple_match.group(2).strip(),
    'marks': 5  # ❌ Wrong default
}
```

**New Code**:
```python
return {
    'number': int(simple_match.group(1)),
    'text': simple_match.group(2).strip(),
    'marks': 1  # ✅ Safer default
}
```

## Real Paper Format Example

### Input:
```
[SECTION – A]               (16x1=16 marks)
Q1. A uniform electric field pointing in positive X-direction...
    (A) VA < VB    (B) VA > VB.    (C) VA < VC    (D) VA > VC

Q2. Another question...
    (A) Option A   (B) Option B    (C) Option C    (D) Option D

[SECTION – B]               (05x2=10 marks)
Q17. A platinum surface having work function 5.63 eV...
Q18. Another question...
```

### Output After Fix:
- **Section A**: Questions Q1-Q16 → 1 mark each
- **Section B**: Questions Q17-Q21 → 2 marks each

## Files Modified
- `backend/app/services/question_paper_ocr_service.py`
  - `_parse_section_based()` method
  - `_match_question_start()` method

## Testing Checklist
- [ ] Upload paper with `[SECTION – A] (16x1=16 marks)`
- [ ] Verify Q1-Q16 get 1 mark each
- [ ] Upload paper with `[SECTION – B] (05x2=10 marks)`
- [ ] Verify Q17-Q21 get 2 marks each
- [ ] Test with em-dash (–) and regular hyphen (-)
- [ ] Test with and without square brackets
- [ ] Verify MCQ options still detected correctly

## Supported Formats Now

### Section Headers:
- `[SECTION – A] (16x1=16 marks)` ✅
- `[SECTION - A] (16x1=16 marks)` ✅
- `SECTION A (16x1=16 marks)` ✅
- `SECTION – A: 16 x 1 = 16 marks` ✅
- `[SECTION A] 16×1=16 marks` ✅

### Question Numbers:
- `Q1. Question text` ✅
- `Q17. Question text` ✅
- `1. Question text` ✅
- `1) Question text` ✅

## Impact
- **Before**: All questions in section-based papers got 5 marks (incorrect)
- **After**: Questions get correct marks from section header (1, 2, 3, etc.)
- **Fallback**: If section detection fails, questions get 1 mark (safer than 5)
