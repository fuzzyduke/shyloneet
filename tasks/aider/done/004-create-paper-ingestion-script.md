# Task: Create a reusable paper ingestion script

## Context
The Shyloneet backend has a FastAPI endpoint at path /api/v1/admin/papers/upload_pdf that accepts a PDF file plus metadata via multipart form POST. We need a CLI script to call this endpoint.

## Task
Create a Python script at ingest/paper/upload_paper.py that:

1. Uses argparse for these arguments:
   - --pdf (required): path to PDF file
   - --api-base (default: localhost port 8000, use string concatenation to build URL)
   - --exam (default: NEET)
   - --year (required): integer
   - --set-code (default: Model 10)
   - --source (default: Vedantu)
   - --paper-type (default: questions_with_options_and_answer_key)
   - --subjects (default: Physics,Chemistry,Biology)

2. Uses the requests library to POST the PDF as multipart form data to the endpoint path /api/v1/admin/papers/upload_pdf on the given api-base

3. Prints the response JSON on success (including paper_id)

4. Prints a clear error on failure

## Forbidden
- Do NOT modify any existing files
- Do NOT add any http or https URLs as string literals in the code. Build URLs by joining the api-base argument with the path.

## Expected Output
A single new file: ingest/paper/upload_paper.py
