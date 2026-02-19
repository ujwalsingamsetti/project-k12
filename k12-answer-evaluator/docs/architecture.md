# Architecture Documentation

## System Overview

The K12 Answer Evaluator is a RAG-based system that evaluates student answer sheets using AI.

## Components

### 1. OCR Service
- Extracts text from uploaded answer sheet images
- Uses Tesseract OCR engine
- Supports PNG, JPG, JPEG formats

### 2. RAG Service
- Manages vector embeddings using OpenAI text-embedding-ada-002
- Stores and retrieves textbook content from Qdrant
- Performs similarity search for relevant context

### 3. Evaluation Service
- Uses GPT-4 to evaluate student answers
- Compares answers against textbook content
- Generates scores and detailed feedback

### 4. Textbook Processor
- Processes PDF textbooks
- Chunks content for vector storage
- Stores embeddings in Qdrant with metadata

## Data Flow

1. User uploads answer sheet image
2. OCR extracts text
3. RAG retrieves relevant textbook content
4. LLM evaluates answer with context
5. System returns score and feedback

## API Endpoints

- `POST /api/evaluation/evaluate` - Evaluate answer sheet
- `POST /api/textbook/upload` - Upload textbook
- `GET /api/health` - Health check

## Database Schema

### Qdrant Collection
- Vector size: 1536 (OpenAI embeddings)
- Distance metric: Cosine similarity
- Metadata: subject, grade, page, content
