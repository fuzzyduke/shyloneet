# Backend - DOX Contract

This `AGENTS.md` file defines the local working rules for the `backend/` subtree.

## Local Purpose
This directory contains the Python backend for the Shylo platform, including FastAPI routes, SQLAlchemy models, and the paper extraction/classification logic.

## Local Rules & Constraints
- **Frameworks:** Python 3.11, FastAPI, SQLAlchemy, SQLite (`neetvault.db`).
- **File Structure:** Core application is in `main.py`, models in `models.py`, db logic in `database.py`. Paper parsing scripts are `paper_parser*.py` and `classifier*.py`.
- **Prohibited Actions:** Modifying `models.py` requires writing a `migrate_*.py` script since alembic is not currently configured. Do NOT mutate `QuestionPaper.scoring_enabled` during human or AI answer corrections.
- **Curriculum Boundaries:** `exam_program_id` must be strictly enforced on all queries (e.g. NEET questions only map to NEET chapters).

## Inheritance
These rules extend the constraints found in the parent directory's `AGENTS.md`. In case of a direct conflict, these local rules take precedence for files within this directory.
