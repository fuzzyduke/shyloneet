# Frontend JS AGENTS.md

This folder contains the vanilla JavaScript logic for the frontend UI.

## Scope & Ownership
- Powers the Student UI (`practice.html`, `test.html`, `mistakes.html`) and the Admin UI (`admin_review.html`).
- Implements API fetching and JWT authorization headers.
- Handles UI state mapping to the FastAPI backend.

## Architecture Rules
- We strictly use Vanilla JS. Do not introduce modern JS frameworks (React, Vue) without explicit architectural shift approval.
- Fetch endpoints must securely include `Authorization: Bearer <token>` fetched from `localStorage`.
- Hardcoded placeholders (e.g. "180 questions") must be replaced with dynamic data populated from API responses.
