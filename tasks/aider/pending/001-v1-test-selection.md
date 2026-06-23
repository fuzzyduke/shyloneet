# Aider Task: V1 Lite Test Selection Page

## Context

This repo is Shyloneet, an educational platform. We recently added a modern V1 Lite student dashboard (`v1.html`). Currently, the "Questions + Answer Key" block on `v1.html` shows a placeholder alert. We need a new page (`v1_papers.html`) that matches the `v1.html` aesthetic and allows students to select a test to take, linking them to the existing `test.html` engine.

## Required Reading

Before editing, read:
- v1.html (to copy the CSS variables, layout classes, and design system)
- data/papers.json (to understand the paper data structure)

## Task

Create `v1_papers.html` using the visual design of `v1.html`.
Fetch the test papers from `data/papers.json`.
Render a card for each paper. Each card should have the title, year, subjects, and a "Start Test" button linking to `test.html?paper={id}`.
Update the "Questions + Answer Key" block button in `v1.html` to link to `/static/v1_papers.html` instead of triggering an `alert()`.

## Allowed Scope

Aider may edit only:
- v1_papers.html (Create new)
- v1.html

## Forbidden Scope

Do not edit:
- test.html
- papers.html
- js/app.js
- any backend python files
- any database schema

Do not:
- broaden the task
- change product boundaries
- rewrite unrelated files
- remove validation
- change the styling system (stick to vanilla CSS variables as in `v1.html`)

## Architectural Rules

Project-specific rules:
- Frontend files reside in the root or `static` dir, but we will put `v1_papers.html` in the root like `v1.html`.
- Maintain the tailwind-like semantic CSS variables (`--bg-color`, `--card-bg`, `--primary`) used in `v1.html`.

General rules:
- Prefer small, reviewable patches.
- Preserve existing architecture.
- Do not silently change approved artifacts or contracts.

## Expected Output

This task should produce:
- A new file `v1_papers.html`
- A modified `v1.html` pointing to the new file

## Verification Steps

After editing, run or describe:
- Open `v1.html` in the browser, verify clicking the second block navigates to `v1_papers.html`.
- Verify `v1_papers.html` successfully fetches `data/papers.json` and renders the list.
- Verify clicking "Start Test" on a card navigates to `test.html?paper=...`

## Stop Conditions

Stop and ask for AG/user review if:
- the task requires editing outside the allowed scope
- tests fail for unrelated reasons
- the files mentioned in the task do not exist
- the requested change conflicts with project architecture

## Aider Output Requirements

At the end, provide:
- summary of changed files
- concise explanation of what changed
- any commands run
- unresolved risks or follow-up tasks
