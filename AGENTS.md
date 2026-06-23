# Shylo NEET - DOX Root

This is the primary `AGENTS.md` for Shylo NEET. All AI agents operating in this repository must follow these constraints.

## Project Purpose
Shylo NEET is an educational platform that uses a Grounded Hybrid Architecture (Vector Embedding Search + LLM Validation) to map, parse, and review exam questions. It provides both a legacy admin interface and a modern V1 Lite student practice and triage surface.

## Core Constraints & Boundaries
- **Tech Stack:** Python 3.11, FastAPI, SQLite, Vanilla HTML/CSS/JS.
- **Boundaries:** 
  - Do NOT modify the database schema without an ADR or migration script.
  - Exam Program Boundary: Question-to-chapter classification MUST NEVER cross exam program boundaries (e.g. NEET questions only map to NEET chapters).
  - Review Gates: When a task asks for an implementation plan or review checkpoint, stop after the plan/report and wait for explicit approval before executing. Do not auto-proceed.
- **Testing:** Maintain scoring safety constraints; do not mutate `QuestionPaper.scoring_enabled` during corrections.

## Documentation Index
Critical context files located in `docs/`:
- **Current State & Hand-off:** [docs/current-state.md](docs/current-state.md)
- **Architecture & System Design:** [docs/architecture.md](docs/architecture.md)
- **Data Provenance & Handling:** [docs/data-provenance.md](docs/data-provenance.md)
- **Model Usage & Prompts:** [docs/model-usage.md](docs/model-usage.md)

## Sub-Module Contracts
The following directories have their own specialized `AGENTS.md` rules which extend or override these root rules:
- `backend/` -> `backend/AGENTS.md`
- `docs/` -> `docs/AGENTS.md`
- `js/` -> `js/AGENTS.md`
- `css/` -> `css/AGENTS.md`

## The Update Contract
If you alter the purpose, structure, infrastructure, or operational rules of this project, you MUST update this `AGENTS.md` and the relevant documents in `docs/` before ending your session. DOX is a living contract.
