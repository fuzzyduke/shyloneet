# Current State Tracker

**Last Updated:** 2026-06-21
**Updated By:** Antigravity (Password Removal + Physics Paper Triage Parser)

This document serves as the live state hand-off for AI agents. Update it whenever a major task is completed, blocked, or started.

## What is Working ✅
- **V1 Lite Admin Bypass:** Password gate is disabled/bypassed specifically for developer/review use within the V1 Lite Admin dashboard (`v1_admin.html`) using a dummy auth token mapping (`bypass-dev-token`). Clicking the Admin card logs in directly.
- **Physics Paper Triage (AG First):** Transitioned to an offline AG-first triage workflow. Raw PDF extraction happens externally via AG tools. The V1 Lite Admin surface (`v1_admin.html`) now imports `paper_triage.json` files for administrative review and selective approval of questions into the database. Raw server-side parsing via the website has been disabled in the primary flow.
- **V1 Lite Surface & Admin View:** Isolated frontend entry point at `/v1` (served from `v1.html`) containing student placeholder cards. The Admin Review block links to the updated `v1_admin.html` offering database diagnostics alongside the new Physics Triage pipeline interface.
- **Phase 1-3:** Database, Question Extraction, and Chapter Classification.
- **Phase 4: Admin Review UI:** Legacy reviews at `/admin` (mapped via Nginx proxy).
- **Phase 5-6:** Scoring parameters, JWT authentication structures, and provenance evaluation logs.

## Known Technical Constraints ⚠️
- **bcrypt** is pinned below 4.0.0 due to Passlib compatibility.

## Manual Review Queues
- **Current Queue:** 13 questions are currently student-eligible. 34 remain admin-locked.
- **Triage Queue:** NEET Physics Model 10 Q1-Q45 imported as `needs_review` status pending layout and option grid checks.

## In Progress / Next Immediate Steps 🔄
- **Verification & Deployment:** Verify live behavior of `v1_admin.html` upload components after pushing files to production.

