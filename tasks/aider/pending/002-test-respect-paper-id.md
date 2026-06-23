# Task: Make `test.html` respect selected paper ID

## Context
The new `v1_papers.html` page sends users to `test.html?paper={id}`. However, `test.html` currently fetches `/api/papers` and defaults to the first paper, ignoring the URL parameter.

## Allowed Scope
- You may ONLY edit `test.html`.
- Do not edit `v1_papers.html`, `v1.html`, backend files, or data files.

## Required Changes in `test.html`
1. Read the selected paper id:
   `const selectedPaperId = new URLSearchParams(window.location.search).get("paper");`
2. If `selectedPaperId` exists, use it as the `paper_id` in the API call to `/api/generate_test`.
3. If `selectedPaperId` is missing, fall back to the first paper from `/api/papers` as it does currently.
4. Update the `localStorage` state key so that each paper has its own separate state. For example:
   `const STATE_STORAGE_KEY = \`shylo_neet_attempt_${selectedPaperId || "default"}\`;` (or incorporate the fallback paper ID if preferred).
5. Remove any hardcoded text like "NEET 2025 Code 45" in visible loading/title/state elements unless it's dynamically populated from the API response's `paper_title`.

## Verification Instructions for Reviewer
- Ensure `test.html?paper=neet-2025-045` sends `paper_id=neet-2025-045`.
- Ensure `test.html?paper=neet-2024` sends `paper_id=neet-2024`.

## Stop Condition
Stop immediately if you need to modify backend API files or other HTML files.
