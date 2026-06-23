# Implementation Notes

- **Dependency Constraints:** `bcrypt` must remain pinned below 4.0.0 due to Passlib compatibility in the current authentication stack.
- **Scoring Safety:** Scoring MUST remain admin-controlled at the paper level. Do not enable scoring globally without verifying paper solution sets.
- **Provenance:** Any user correction (e.g., Shiloh corrections) must be logged in the `AnswerEvaluation` and `ChapterMappingEvaluation` tables for auditability. Track LLM provider and model separately when LLM suggested answers are recorded.
- **V1 Admin Password Bypass:** A temporary bypass is active using `bypass-dev-token` to facilitate rapid review. Restore password requirements before deploying sensitive administrative tools.
- **Ingestion Status Rules:** Question DB must categorize status explicitly into `q_only`, `q_with_key`, `q_with_llm`, or `q_verified`.
- **Nested DOX:** This repository utilizes a strict hierarchical `AGENTS.md` structure. Do not edit logic without reading both the local and root `AGENTS.md`.

