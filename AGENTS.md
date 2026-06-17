# DOX Framework

- DOX is a highly performant AGENTS.md hierarchy installed here.
- Agent must follow DOX instructions across any edits.

## Core Contract

- `AGENTS.md` files are binding work contracts for their subtrees.
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable `AGENTS.md` plus every parent `AGENTS.md` above it.

## Read Before Editing

1. Read this root `AGENTS.md`.
2. Identify every file or folder you expect to touch.
3. Walk from the repository root to each target path.
4. Read every `AGENTS.md` found along each route.
5. If a parent `AGENTS.md` lists a child `AGENTS.md` whose scope contains the path, read that child and continue from there.
6. Use the nearest `AGENTS.md` as the local contract and parent docs for repo-wide rules.
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX.

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.
If code changes but docs/AGENTS.md are stale, update them.

Update the closest owning `AGENTS.md` when a change affects:
- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- `AGENTS.md` creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. 

## Project-Wide Rules & Constraints

- **Review Gates:** When a task asks for an implementation plan or review checkpoint, stop after the plan/report and wait for explicit approval before executing. Do not auto-proceed.
- **Bible DOX SOP Reference:** The Bible DOX SOP is the reusable operational source for general deployment and external resource references, without making Shylo the global DOX source of truth.
- **Dependency Stability:** `bcrypt` is pinned below 4.0.0 due to Passlib compatibility in the current auth stack.

## Top-Level Index

- `./backend/AGENTS.md` - Backend API, models, extraction/classification logic.
- `./dox/AGENTS.md` - Project documentation and architecture state.
- `./js/AGENTS.md` - Frontend JavaScript files.
- `./css/AGENTS.md` - Frontend CSS stylesheets.
