# Shyloneet Ingestion Superpower

Welcome to the `shyloneet/ingest` superpower. This directory contains the exact, standardized workflows (SOPs) for ingesting data into the Shyloneet system.

When an AI agent (AG) is instructed to "ingest" a PDF or a set of PDFs, it MUST route through this directory to ensure perfect conformity with the database schema and extraction pipelines.

## Folder Structure
- `/subject`: Instructions and conventions for ingesting **Course Material** (e.g., NCERT textbooks for Physics, Chemistry, Biology).
- `/paper`: Instructions and conventions for ingesting **Question Papers** (e.g., NEET 2024, Mock Tests).

## General Preflight Rules for AG
Before beginning any ingestion workflow, AG must perform the following checks:

1. **Verify Source PDF Exists**: Ensure the target PDF exists in the provided path.
2. **Determine Ingestion Type**: Decide if this is a `subject` (reference material) or a `paper` (test with 180 questions).
3. **Read Specific SOP**: You MUST open and read `subject/README.md` OR `paper/README.md` based on your determination *before* running any ingestion scripts.
4. **Environment Check**: Ensure the Python environment (`backend/venv`) is available and active if you need to run backend python scripts.

Proceed to either `./subject/README.md` or `./paper/README.md` depending on your task!
