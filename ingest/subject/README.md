# Subject Material Ingestion SOP

This document defines the process for ingesting **Course Material / Reference Textbooks** (e.g., NCERT Physics, Chemistry) into the Shyloneet system.

Unlike Question Papers, Subject Materials are ingested to populate the **RAG Knowledge Base**. They are chopped into chunks rather than strict individual questions.

## Directory Convention

When the user asks to ingest a subject folder (e.g., `shyloneet/ingest subject <folder name>`), the target folder should contain the raw PDFs for that subject.

Example:
```
data/textbooks/physics/
  ├── kinematics.pdf
  └── thermodynamics.pdf
```

## Mandatory Tags

Every ingested chapter must be tagged with appropriate metadata before insertion into the DB:
* `subject`: (e.g., "Physics", "Chemistry", "Biology")
* `source_type`: ALWAYS set to `"reference_book"`
* `exam_program_id`: (e.g., "NEET")
* `source`: The name of the textbook (e.g., "NCERT Class 11")
* `class_level`: 11 or 12

## AG Instructions for Ingestion

When executing a subject ingestion, AG must:

1. **Scan the target folder**: Find all PDFs.
2. **Extract Text**: Use standard Python PDF extraction libraries (like `PyMuPDF` or `pdfplumber`) to pull raw text.
3. **Chunking**: Break the text into logical, readable chunks (e.g., paragraph by paragraph, or by headings).
4. **Database Insertion**:
   - Create a `Chapter` entry in the `chapters` table.
   - For each text chunk, create a `ChapterChunk` entry linking back to the `Chapter`.
   - Set `chunk_type="text"`.
   - *(Optional Phase)* If vector embeddings are available/requested, populate the `embedding` field.
5. **Validation**: Query the SQLite database (`backend/neet_vault.db`) to verify that the `chapters` and `chapter_chunks` tables have incremented correctly.
