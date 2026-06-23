# Frontend JS - DOX Contract

This `AGENTS.md` file defines the local working rules for the `js/` subtree.

## Local Purpose
This directory contains the vanilla JavaScript logic for the frontend UI. It powers the Student UI and the Admin UI, implements API fetching, and handles UI state mapping.

## Local Rules & Constraints
- **Frameworks:** We strictly use Vanilla JS. Do not introduce modern JS frameworks (React, Vue) without explicit architectural shift approval.
- **API Fetching:** Fetch endpoints must securely include `Authorization: Bearer <token>` fetched from `localStorage`.
- **Dynamic Data:** Hardcoded placeholders must be replaced with dynamic data populated from API responses.

## Inheritance
These rules extend the constraints found in the parent directory's `AGENTS.md`. In case of a direct conflict, these local rules take precedence for files within this directory.
