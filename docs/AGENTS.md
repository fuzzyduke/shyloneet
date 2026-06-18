# Dox AGENTS.md

This folder contains persistent system architecture documents, state trackers, and design documentation.

## Scope & Ownership
- This directory supplements the AGENTS.md hierarchy with long-form context.
- **Do NOT** use these docs as a replacement for updating the local `AGENTS.md` contracts.
- These files must be updated at major milestones or architectural shifts.

## Documents
- `architecture.md`: The Grounded Hybrid Architecture, boundary layers, and core infrastructure stack.
- `current-state.md`: The live state tracker detailing completed phases and current review queues.
- `data-provenance.md`: Legacy provenance concepts.
- `answer-provenance.md`: Detailed rules for `AnswerEvaluation` history, overrides, and display priorities.
- `admin-review.md`: The workflow and structure of the `/admin` interface.
- `scoring-safety.md`: Rules isolating raw ingestion from student analytics (e.g. `scoring_enabled` flag).
