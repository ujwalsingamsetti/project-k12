# K12 Answer Evaluator

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-2.0.0-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)

## Overview
The **K12 Answer Evaluator** is a cutting-edge educational platform designed to automate the evaluation of handwritten student answer sheets. It leverages Google Cloud Vision for OCR, Gemini AI for intelligent grading against an answer key, and an advanced Retrieval-Augmented Generation (RAG) system to query textbook content for accurate feedback. 

It provides two distinct portals:
- **Teacher Portal:** Central hub to extract, create, and assign question papers. Gives teachers final authority to override AI evaluations.
- **Student Portal:** A unified, glassmorphism-themed UI where students can upload handwritten answers, monitor tracking indicators, analyze subject-wise trends, and download detailed PDF report cards.

## Quick Install & Usage
### Prerequisites
- Python 3.10+
- PostgreSQL
- Node.js & NPM
- Google Cloud Vision Credentials (`JSON` format)
- Gemini API Key (`GOOGLE_API_KEY`)

### Backend Setup
```bash
git clone https://github.com/your-org/project-k12.git
cd project-k12/k12-answer-evaluator/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set .env vars, then run database migrations
alembic upgrade head
# Start server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd project-k12/frontend
npm install
npm run dev
```

For more in-depth system architecture, workflows, and API details, please see the [**DOCUMENTATION.md**](./DOCUMENTATION.md) file. For testing and release notes, visit [**TEST_PLAN.md**](./TEST_PLAN.md) and [**CHANGELOG.md**](./CHANGELOG.md).
