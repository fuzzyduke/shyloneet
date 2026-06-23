# System Architecture

**Last Updated:** 2026-06-21

## High-Level Overview
Shylo relies on a Grounded Hybrid Architecture for chapter classification: using `sentence-transformers` for Vector Embedding Search to retrieve top 5 NCERT chapter candidates, and an LLM validation step (via Agent Zero) to decide the final mapping. It strictly enforces boundary layers.
The frontend routing is split between a legacy Admin application (`/admin`), a newly introduced V1 Lite student practice surface (`/v1`), and an updated V1 Lite Admin diagnostics and Physics Triage dashboard (`/static/v1_admin.html`).

## Core Infrastructure
- **Frontend:** Vanilla HTML/CSS/JS deployed to a VPS. Active pages: `index.html` (legacy student landing), `v1.html` (V1 Lite landing), `v1_admin.html` (diagnostics & triage), and `admin_review.html` (legacy mapping reviews).
- **Backend:** FastAPI (Python 3.11) exposing APIs for mock test generation, manual corrections, review queues, course material status endpoints, and new paper triage endpoints (`/api/v1/admin/triage/*`).
- **Database:** SQLite (`neetvault.db`).
- **Auth:** JWT-based bearer tokens with passlib/bcrypt hashing (Roles: `admin`, `sub_admin`, `student`). A developer bypass token (`bypass-dev-token`) resolves to a mock admin user for external review ease.
- **Provenance Tracking:** `AnswerEvaluation` and `ChapterMappingEvaluation` tables maintain an immutable log of AI, human, and paper-sourced mappings.
- **External APIs:** Agent Zero `qwen-3-7-plus` for vision parsing and mapping.

## AG-First PDF Triage Workflow
The parsing of raw question paper PDFs into structured data is explicitly separated from the web admin panel.
1. **Offline AG Extraction:** Antigravity (AG) or dedicated offline scripts ingest the raw PDF, extract texts/diagrams, and produce a structured `paper_triage.json` file.
2. **Website Review and Approval:** The Admin uploads this JSON file into the V1 Admin dashboard (`v1_admin.html`). The dashboard acts only as a review interface where questions are edited and approved.
3. **Database Insertion:** Only explicitly approved questions are saved to the `questions` table via `POST /api/v1/admin/triage/import_question`. Website-native PDF triage is considered experimental and disabled from the primary flow.

## Architecture Rules & Decisions


## 1. Exam Program / Curriculum Boundary Layer
The Shylo system supports multiple isolated educational universes (e.g., NEET, HSC State Board, SAT, JEE). To prevent cross-contamination, all curriculum and assessment data MUST strictly adhere to the Boundary Layer rules.

### Rule 1: PDF Tagging on Ingestion
Every uploaded PDF (whether a reference textbook or a question paper) must be tagged with the `exam_program_id`.
- **Reference Chapters**: Set `source_type="reference_book"`, `source_name="NCERT"` (or appropriate), and `exam_program_id`.
- **Question Papers**: Set `source_type="question_paper"`, `source_name="NTA"` (or appropriate), and `exam_program_id`.

### Rule 2: Strict Boundary Enforcement
Question-to-chapter classification MUST NEVER cross exam program boundaries. 
- When mapping a NEET question to its relevant chapter via vector search or LLM, the search space must be filtered by `exam_program_id == question.exam_program_id`.
- A NEET paper should only search NEET/NCERT chapters.
- An HSC paper should only search HSC/Balbharati chapters.

### Rule 3: Curriculum Bridging
If a feature requires connecting related topics across exams (e.g., mapping an HSC Physics chapter to the equivalent NEET Physics chapter), you must use the `curriculum_bridges` table. Do NOT establish automatic cross-mapping in the primary `question_chapter_map` table or during raw embedding searches.
