# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [2.0.0] - 2026-02-21

### Added
- **Core AI Evaluation**: Completely revamped the `evaluate_submission` function to utilize Google Gemini via `google-genai` and `langchain` components instead of OpenAI.
- **OCR System Integration**: Integrated Google Cloud Vision to robustly parse handwritten text, checkboxes, diagrams, and mathematical symbols directly from image uploads.
- **Knowledge Base (RAG)**: Developed a textbook processing pipeline uploading documents into Qdrant for context-aware grading.
- **Student Performance Dashboard**: Added dynamic progress tracking, bar charts, and historical submission timelines.
- **Interactive Reports & Leaderboards**: Added PDF Report Card streaming (`reportlab`) and class ranking leaderboards per paper.
- **Notification System**: Added real-time polling to inform students of evaluation completions and new assignments.
- **Student Profile Management**: Added the ability for students to specify their `grade` level across the frontend UI and database.

### Fixed
- **Database Enum Errors**: Resolved critical `DataError` exceptions related to PostgreSQL Enum capitalization by syncing SQLAlchemy definitions strictly to lowercase mappings.
- **Context Generation Chunking**: Fixed file ingestion bugs with unstructured text that previously triggered database transaction rollbacks.
- **Frontend State Synching**: Removed orphaned React hooks that blocked evaluation state refreshing when navigating to the results viewer.
