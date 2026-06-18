# Implementation Notes

- **Dependency Constraints:** `bcrypt` must remain pinned below 4.0.0 due to Passlib compatibility in the current authentication stack.
- **Scoring Safety:** Scoring MUST remain admin-controlled at the paper level. Do not enable scoring globally without verifying paper solution sets.
- **Provenance:** Any user correction (e.g., Shiloh corrections) must be logged in the `AnswerEvaluation` and `ChapterMappingEvaluation` tables for auditability.
- **Nested DOX:** This repository utilizes a strict hierarchical `AGENTS.md` structure. Do not edit logic without reading both the local and root `AGENTS.md`.
