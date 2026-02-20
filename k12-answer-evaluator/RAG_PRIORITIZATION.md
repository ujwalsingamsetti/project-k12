# RAG Context Prioritization Enhancement

## Overview
Modified the RAG (Retrieval-Augmented Generation) system to prioritize question paper context over textbook content during student answer evaluation.

## Problem
Previously, the evaluation system only used textbook chunks from the vector database, which sometimes lacked specific context about the question's requirements, marks distribution, and section information.

## Solution
Enhanced RAG to use a **two-tier context system**:

### 1. Primary Context: Question Paper
- Question number and marks allocation
- Section information (A, B, C, D, E)
- Exact question text from the paper
- **Score: 1.0** (highest priority)

### 2. Secondary Context: Textbook
- Retrieved from Qdrant vector database
- Top 2 most relevant chunks
- Subject-filtered semantic search
- **Score: 0.0-1.0** (based on similarity)

---

## Implementation

### Modified Files

#### 1. `rag_service.py`

**Method**: `retrieve_relevant_context()`

```python
def retrieve_relevant_context(
    self, 
    query: str, 
    subject: str, 
    top_k: int = 5, 
    question_paper_context: str = None  # NEW PARAMETER
) -> List[Dict]:
```

**Logic**:
```python
results = []

# First priority: Question paper context
if question_paper_context:
    results.append({
        "text": question_paper_context,
        "score": 1.0,
        "chapter": "Question Paper",
        "source": "question_paper"
    })

# Second priority: Textbook chunks from vector DB
search_result = qdrant_client.query_points(...)
for point in search_result:
    results.append({
        "text": point.payload["text"],
        "score": point.score,
        "source": "textbook"
    })

return results
```

**Method**: `format_context_for_llm()`

```python
def format_context_for_llm(self, chunks: List[Dict], max_tokens: int = 1200) -> str:
    # Separate by source
    qp_chunks = [c for c in chunks if c["source"] == "question_paper"]
    tb_chunks = [c for c in chunks if c["source"] != "question_paper"]
    
    context_parts = []
    
    # Add question paper context first
    if qp_chunks:
        context_parts.append("[QUESTION PAPER CONTEXT]")
        context_parts.append(qp_chunks[0]["text"])
    
    # Add top 2 textbook chunks
    if tb_chunks:
        context_parts.append("\n[TEXTBOOK REFERENCE]")
        for chunk in tb_chunks[:2]:
            context_parts.append(chunk["text"])
    
    return "\n\n".join(context_parts)
```

#### 2. `students.py`

**In**: `process_submission_multiple()`

```python
# Build question paper context
qp_context = f"Question {question.question_number} ({question.marks} marks): {question.question_text}"
if question.section:
    qp_context = f"Section {question.section} - " + qp_context

# RAG retrieval with question paper context prioritized
context_chunks = rag_service.retrieve_relevant_context(
    question.question_text,
    subject=paper.subject.value,
    question_paper_context=qp_context  # NEW PARAMETER
)
```

---

## Context Format Sent to LLM

### Before (Textbook Only)
```
TEXTBOOK REFERENCE:
Newton's first law states that an object at rest stays at rest...

Newton's second law relates force, mass, and acceleration...
```

### After (Question Paper + Textbook)
```
[QUESTION PAPER CONTEXT]
Section A - Question 1 (1 marks): State Newton's first law of motion.

[TEXTBOOK REFERENCE]
Newton's first law states that an object at rest stays at rest and an object in motion stays in motion with the same speed and direction unless acted upon by an unbalanced force.

This law is also known as the law of inertia. Inertia is the tendency of an object to resist changes in its state of motion.
```

---

## Benefits

### 1. **Accurate Marks Allocation**
LLM knows exactly how many marks the question carries:
- 1 mark → Brief answer expected
- 5 marks → Detailed explanation required

### 2. **Section-Aware Evaluation**
- Section A (MCQ) → Different evaluation criteria
- Section E (Long answer) → More detailed feedback

### 3. **Question Context**
LLM understands:
- What is being asked
- Expected answer format
- Key terms to look for

### 4. **Better Scoring**
- More accurate score breakdown
- Appropriate feedback depth
- Aligned with CBSE marking schemes

---

## Example Evaluation Flow

### Question
**Section B - Q17 (2 marks)**: Define photoelectric effect and state one application.

### Student Answer
"Photoelectric effect is emission of electrons when light falls on metal surface. Used in solar panels."

### RAG Context Sent to LLM
```
[QUESTION PAPER CONTEXT]
Section B - Question 17 (2 marks): Define photoelectric effect and state one application.

[TEXTBOOK REFERENCE]
The photoelectric effect is the phenomenon in which electrons are emitted from the surface of a metal when electromagnetic radiation of sufficiently high frequency falls on it. This effect was explained by Einstein in 1905.

Applications include: photocells, solar panels, light sensors, and automatic door openers.
```

### LLM Evaluation
```json
{
  "score": 1.5,
  "score_breakdown": {
    "correctness": 0.8,
    "completeness": 0.5,
    "understanding": 0.2
  },
  "correct_points": [
    "Correctly defined photoelectric effect as emission of electrons",
    "Mentioned light falling on metal surface",
    "Provided valid application (solar panels)"
  ],
  "errors": [],
  "missing_concepts": [
    "Did not mention 'high frequency' or threshold frequency requirement",
    "Could elaborate on how solar panels use this effect"
  ],
  "overall_feedback": "Good basic understanding. For 2 marks, include more detail about frequency requirement."
}
```

---

## Configuration

### Max Token Limits
- **Before**: 800 characters
- **After**: 1200 characters (to accommodate question paper context)

### Chunk Selection
- **Question Paper**: 1 chunk (always included if available)
- **Textbook**: Top 2 chunks (down from 3 to fit token limit)

---

## Testing

### Verify Question Paper Context
Check logs for:
```
Added question paper context as primary reference
Retrieved 3 total chunks (question paper + textbook)
```

### Verify Context Format
Check logs for:
```
Context preview: [QUESTION PAPER CONTEXT]
Section A - Question 1 (1 marks): State...
```

### Verify Evaluation Quality
- 1-mark questions should get brief feedback
- 5-mark questions should get detailed feedback
- Scores should align with marks allocation

---

## Backward Compatibility

The enhancement is **fully backward compatible**:
- If `question_paper_context=None`, only textbook chunks are used
- Existing evaluations continue to work
- No database schema changes required

---

## Future Enhancements

### 1. Include Answer Key
If teacher provides answer key:
```python
qp_context = f"Question {q_num} ({marks} marks): {q_text}\nExpected Answer: {answer_key}"
```

### 2. Include Marking Scheme
```python
qp_context += f"\nMarking Scheme: {marking_scheme}"
```

### 3. Include Previous Year Patterns
Retrieve similar questions from past papers and their evaluations.

---

## Summary

✅ **Question paper context now prioritized over textbook**  
✅ **LLM receives structured context with marks and section info**  
✅ **More accurate evaluations aligned with CBSE standards**  
✅ **Better feedback tailored to question requirements**  
✅ **Backward compatible with existing system**
