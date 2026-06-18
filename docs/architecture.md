# System Architecture

**Last Updated:** 2026-06-16

## High-Level Overview
Shylo relies on a Grounded Hybrid Architecture for chapter classification: using `sentence-transformers` for Vector Embedding Search to retrieve top 5 NCERT chapter candidates, and an LLM validation step (via Agent Zero) to decide the final mapping. It strictly enforces boundary layers.

## Core Infrastructure
- **Frontend:** Vanilla HTML/CSS/JS deployed via Cloudflare to a VPS.
- **Backend:** FastAPI (Python 3.11).
- **Database:** SQLite (`neetvault.db`).
- **Auth:** JWT-based bearer tokens with passlib/bcrypt hashing (Roles: `admin`, `sub_admin`, `student`).
- **Provenance Tracking:** `AnswerEvaluation` and `ChapterMappingEvaluation` tables maintain an immutable log of AI, human, and paper-sourced mappings.
- **External APIs:** Agent Zero `qwen-3-7-plus` for vision parsing and mapping.

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
