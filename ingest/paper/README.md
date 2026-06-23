# Question Paper Ingestion SOP

This document defines the process for ingesting **Question Papers** (e.g., past NEET exams, sample papers) into the Shyloneet system.

Unlike Subject Materials, Question Papers require rigorous parsing to extract exactly 180 individual questions, their options, and diagrams.

## Directory Convention

When the user asks to ingest a paper folder (e.g., `shyloneet/ingest paper <folder name>`), the target folder should contain the raw test PDFs.

Example:
```
data/papers/neet-2024/
  ├── source.pdf
  └── answer_key.pdf
```

## API Endpoint Reference

```
Endpoint: POST /api/v1/admin/papers/upload_pdf
Auth:     Bearer JWT token (required)

File field:   'file'  (NOT 'pdf')
Form fields:
  - exam              (string, default: "NEET")
  - year              (int)
  - set_code          (string)
  - source            (string)
  - paper_type        (string, default: "questions_with_options_and_answer_key")
  - subjects_included (string, comma-separated — NOT 'subjects')
```

## Authentication

The upload endpoint requires a Bearer JWT token. Generate one using the backend venv:

```powershell
backend\venv\Scripts\python.exe -c "from jose import jwt; print(jwt.encode({'sub':'admin','role':'admin'}, 'mvp-secret-key-shiloh', algorithm='HS256'))"
```

Pass via: `--token` flag on the upload script, or `AUTH_TOKEN` env var.

## CLI Upload Script

A reusable script exists at `ingest/paper/upload_paper.py`:

```powershell
C:\Users\graci\AppData\Local\Programs\Python\Python312\python.exe ingest/paper/upload_paper.py `
  --pdf "path\to\paper.pdf" `
  --year 2026 `
  --api-base "http://127.0.0.1:8000" `
  --token "<jwt_token>"
```

## AG Instructions for Ingestion

When executing a paper ingestion, AG must follow the official architecture defined in `docs/NEET_PAPER_INGESTION_WORKFLOW.md`.

**In Summary:**
1. **Locate PDF**: Find the target PDF in the specified directory.
2. **Generate Auth Token**: Use the command above. Do not ask the user.
3. **Run Upload Script**: Execute `ingest/paper/upload_paper.py` with the correct PDF path and metadata.
4. **Verify Question Count**: After upload, query the database:
   ```powershell
   backend\venv\Scripts\python.exe -c "import sys; sys.path.append('backend'); from database import SessionLocal; import models; db = SessionLocal(); qc = db.query(models.Question).filter(models.Question.paper_id == '<PAPER_ID>').count(); print(f'Questions: {qc}/180')"
   ```
5. **Parse Rate Check**: If `parsed_count / expected_count < 80%`, flag the paper as needing manual review or parser improvement. **Do NOT auto-publish incomplete papers.**
6. **Publish** (only if ≥80%): Update the paper status from `draft` to `approved` via `POST /api/v1/admin/papers/{id}/publish`.
7. **Failure Recovery**: If parsing fails, clean up the failed `QuestionPaper` record and attempt to resolve parsing errors before re-inserting.
