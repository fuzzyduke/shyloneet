# Scoring Safety 

The platform strictly isolates analytical scoring controls from raw ingestion to prevent students from being incorrectly scored or exposed to unverified, AI-invented answer keys.

## Paper-Level Flags
Every Question Paper maintains two critical fields:
1. `solution_status` (e.g., `official_from_paper`, `ai_mapped`, `unavailable`, `needs_review`)
2. `scoring_enabled` (boolean)

## Student UI Enforcement
- If `scoring_enabled == False`, the frontend practice UI fundamentally locks out:
  1. Real-time accuracy tracking.
  2. End-of-test Scorecards and ranks.
  3. Correct answer reveals in the post-test Review screen.
- Instead, the student takes an "unscored practice" session.

## Mutation Strictness
- **Human Corrections:** When a `sub_admin` (Shiloh) overrides an answer, the answer updates locally for their own view (and future admin review), but the paper-level `scoring_enabled` flag is **never** flipped automatically.
- **AI Processing:** Background AI evaluation jobs append to the Provenance tables but do not toggle `scoring_enabled`.
- Scoring must always be a deliberate, explicit action taken by an Admin at the paper level.
