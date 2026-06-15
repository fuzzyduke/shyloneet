# Data Provenance & Handling

**Last Updated:** 2026-06-16

This document tracks the lifecycle of data, sources of truth, handling of mock data, and manual review queues in the Shylo system.

## Ingestion Pipeline
1. **PDF Intake:** Exam papers are uploaded and tagged with `exam_program_id`, `source_type`, `year`, etc.
2. **Extraction (Phase 2):** High-res images are sent to Agent Zero Vision LLM for strict JSON extraction.
3. **Fallback Logging:** Any failed extraction (e.g. LLM hallucinates markdown) is logged into `failed_extractions` for manual recovery.

## Mock Data Safety
If any mock data is inserted for testing UI/API plumbing, it must follow these safety rails:
1. `is_mock = true`
2. `source_type = "mock"`
3. `extraction_status = "mock_validation_only"`
4. `processing_status = "mock_only"`
**Mock questions must never appear in student practice mode or be classified against real chapters.**

## Classification Provenance
- Chapter boundaries are strictly enforced. NEET questions never touch HSC chapters.
- Low-confidence mappings are flagged for admin review and output into `chapter_classification_report.md`.
