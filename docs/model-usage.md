# Model Usage & AI Guidelines

**Last Updated:** 2026-06-23

This document tracks the LLMs, APIs, and AI models authorized for use within the Shylo platform, as well as prompt architectures and usage boundaries.

## Authorized Models
- **Agent Zero (qwen-3-7-plus):** Used for vision parsing, PDF triage, and mapping question papers.
- **Sentence-Transformers:** Used for Vector Embedding Search to retrieve top chapter candidates for classification.

## Pipelines & Usage
- **Physics Paper Triage:** Extracted primarily via offline AG scripts from raw PDFs into structured `paper_triage.json` files.
- **Classification Validation:** Grounded Hybrid Architecture first retrieves the top 5 NCERT chapter candidates via vector search, then an LLM validation step (via Agent Zero) decides the final mapping.

## Confidence Thresholds & Review
- AI-generated mappings and parsed questions are marked as `needs_review` or pending state.
- They must be manually reviewed and approved through the V1 Lite Admin dashboard before entering the active database for student practice.
