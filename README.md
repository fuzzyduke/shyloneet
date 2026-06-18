# Shyloneet

A specialized platform for parsing, ingesting, and answering NEET exam papers with deep provenance tracking and admin curation.

## Current Status
- Backend API and Admin Review UI (Phase 4) implemented.
- Question extraction and Chapter mapping functional.
- JWT Auth, User Roles, and Data Provenance tracked (Phase 6).
- Scoring remains admin-locked per paper.

## Implemented Features
- **Phase 1-3:** Database, Question Extraction, Chapter Classification.
- **Phase 4:** Admin Review UI.
- **Phase 5:** Scoring Safety controls.
- **Phase 6:** Auth & Answer Provenance (Shiloh corrections).

## Planned / Wishlist Features
- Fully automated OCR/parsing of PDF exams (Advanced Paper Ingestion).
- Dynamic mock test generation by chapter.
- Detailed step-by-step solutions attached to questions.
- Subject expansion beyond current sets.
- Student Scorecards and progress tracking.

## Tech Stack
- Frontend: HTML/JS UI interfaces for Admin/Student
- Backend: Python (with `bcrypt` pinned for Passlib auth)
- Data: JSON parsed output and relational database state.

## Local Setup
Check the deployment script `deploy.js` or standard Python/Nginx setup routines (`setup_nginx.js`, `check_nginx.js`).

## Documentation (DOX)
This project follows the DOX methodology, combined with a strict nested `AGENTS.md` hierarchy, ensuring that future plans and wishlist items are preserved alongside current implementations.

- [DOX Methodology](DOX.md)
- [Project Brief](docs/project-brief.md)
- [Current State](docs/current-state.md)
- [Roadmap](docs/roadmap.md)
- [Architecture](docs/architecture.md)
