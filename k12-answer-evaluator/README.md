# K12 Answer Sheet Evaluator

AI-powered system for evaluating K12 student answer sheets using OCR, RAG, and LLM.

## Features

- OCR text extraction from answer sheets
- RAG-based evaluation using textbook content
- GPT-4 powered intelligent grading
- Vector similarity search with Qdrant
- Modern React/Next.js frontend

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Frontend**: React, Next.js
- **Vector DB**: Qdrant
- **LLM**: OpenAI GPT-4
- **OCR**: Tesseract

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

## Usage

1. Upload textbooks via `/api/textbook/upload`
2. Submit answer sheets via `/api/evaluation/evaluate`
3. View results with scores and feedback

## Project Structure

- `backend/app/services/` - Core services (OCR, RAG, Evaluation)
- `backend/app/routes/` - API endpoints
- `frontend/src/components/` - React components
- `frontend/src/pages/` - Next.js pages
