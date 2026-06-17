# Backend AGENTS.md

This folder contains the Python backend for the Shylo platform, including FastAPI routes, SQLAlchemy models, and the paper extraction/classification logic.

## Scope & Ownership
- Responsible for `neetvault.db` SQLite interaction.
- Houses the AI pipelines for PDF parsing (`paper_parser*.py`) and chapter classification (`classifier*.py`).
- Manages Authentication (JWT), Answer Provenance (`AnswerEvaluation`), and Admin workflows.

## Required Operations & Constraints
- **Database Migrations:** Modifying `models.py` requires either dropping tables (if safe/dev mode) or writing a `migrate_*.py` script since alembic is not currently configured.
- **Scoring Safety:** Do NOT mutate `QuestionPaper.scoring_enabled` during human or AI answer corrections.
- **Curriculum Boundaries:** `exam_program_id` must be strictly enforced on all queries (e.g. NEET questions only map to NEET chapters).

## Local Dependencies
- Requires Python 3.11 with `requirements.txt`.
- Activate `venv` before running: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac).
- Run server: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`.
