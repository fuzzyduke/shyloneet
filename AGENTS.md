# Shylo - DOX Root

This is the primary `AGENTS.md` for the Shylo project. All AI agents operating in this repository must follow these constraints.

## Project Purpose
Shylo is an AI-powered learning and assessment platform for NEET preparation. It uses Vision LLMs to parse past papers and embeddings to classify questions against NCERT curriculum chapters.

## Core Constraints & Boundaries
- **Tech Stack:** Python 3.11, FastAPI, SQLite, SentenceTransformers, vanilla HTML/JS/CSS frontend.
- **Boundaries:** All database queries must enforce the `exam_program_id` boundary (e.g., NEET questions only map to NEET chapters). See `dox/architecture.md` for full rules.
- **Testing:** Do not modify the database schema without updating `models.py` and running isolated tests first.
- **Data Protection:** Failed extractions or mappings MUST not be silently dropped. They must be tracked via the `FailedExtraction` table or `needs_manual_review` flags.

## Documentation Index
Critical context files located in `dox/`:
- **Current State & Hand-off:** [dox/current-state.md](dox/current-state.md)
- **Architecture & System Design:** [dox/architecture.md](dox/architecture.md)
- **Data Provenance & Handling:** [dox/data-provenance.md](dox/data-provenance.md)

## Sub-Module Contracts
The following directories have their own specialized `AGENTS.md` rules which extend or override these root rules:
- *(None currently established. All rules flow from this root file).*

## The Update Contract
If you alter the purpose, structure, infrastructure, or operational rules of this project, you MUST update this `AGENTS.md` and the relevant documents in `dox/` before ending your session.
