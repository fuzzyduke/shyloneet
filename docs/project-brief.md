# Project Brief: Shyloneet

## Project Overview
**What the project is:** A specialized exam preparation platform for the NEET exam.
**Who it is for:** Students answering the NEET exam ("Shiloh") and administrators managing question banks.
**Why it exists:** To parse, ingest, and categorize past exam papers into testable questions, providing chapter mapping, and allowing users to practice while providing an admin interface to curate and review the questions.

## Current Implementation
- **Backend API & Database:** Functional.
- **Phase 1-3 (Ingestion):** Question extraction and Chapter Classification implemented (currently ~47 real unique questions).
- **Phase 4 (Admin Review):** Admin UI available at `/admin` (mapped to `admin_review.html`).
- **Phase 5 (Scoring Safety):** Scoring is paper-level admin controlled.
- **Phase 6 (Auth & Provenance):** JWT authentication, specific user roles (`admin`, `shiloh`), tracking of `AnswerEvaluation` and `ChapterMappingEvaluation`.

## Planned / Wishlist
- **Paper Ingestion & Question Extraction:** Full automation for parsing messy PDF exam papers.
- **Test Generation:** Creating mock tests based on subject/chapter requirements.
- **Scoring & Solutions:** Detailed scoring metrics and step-by-step solution breakdowns for students.
- **Subject Expansion:** Expanding beyond Physics/Chemistry/Biology to other subjects if needed.
- **Student Scorecards:** Detailed progression tracking.

## Functional Specs
- **Main User Flows:** Admin ingests paper -> Admin maps chapters -> Student takes test -> Shiloh correction flow -> Admin approves corrections.
- **Core Modules:** Question Extractor, Auth System, Admin Review Panel, Student Test Interface.
