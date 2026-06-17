# Answer Provenance

## Concept
Every answer and chapter mapping in the system traces its origin (provenance). We do not overwrite raw answers blindly. Instead, we insert immutable evaluation rows that maintain an audit trail.

## Tables
- `AnswerEvaluation`: Tracks `evaluator_type` (paper, sub_admin, admin, ai_model), `correct_option`, `confidence`, and `status`.
- `ChapterMappingEvaluation`: Tracks chapter mappings similarly.

## Resolution Logic
- An evaluation is marked `is_active=True` if it is the current reigning answer.
- When a human (`sub_admin` / `shiloh` or `admin`) submits a correction, their evaluation becomes `is_active=True`, and the previous active evaluation becomes `superseded` (`is_active=False`).
- `sub_admin` evaluations receive a `status="needs_review"` flag, highlighting them for Admin Review.

## Overrides & Safety
- **Paper Key Override:** If the current active answer originated from the raw paper extraction, `sub_admin`s receive a warning modal before submitting an override to prevent accidental corruption of the "ground truth" paper key.
