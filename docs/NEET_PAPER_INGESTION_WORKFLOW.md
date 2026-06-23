# NEET Question Paper Ingestion Workflow

This document serves as the official source of truth and repository memory for how question papers are ingested, parsed, reviewed, and published in the Shylo NEET application.

---

## 1. Reference Textbook Ingestion vs. Question Paper Ingestion

It is critical to distinguish between these two pipelines:
* **Reference Textbook Ingestion:** Focuses on importing chapters, books, and reference materials (e.g., NCERT PDFs) for building the RAG (Retrieval-Augmented Generation) knowledge base. These are parsed into coarse chunks and mapped to chapters.
* **Question Paper Ingestion:** Focuses on processing individual question papers (e.g., past NEET exams or practice tests) to build a library of test questions. Each paper requires strict metadata, precise parsing of individual questions (exactly 180 questions for full papers), option mapping (A-D), diagram/image association, and an administrative review and publishing flow.

---

## 2. Expected PDF-to-DB Workflow

Question paper ingestion is a multi-step backend-driven process:
1. **Upload PDF:** The admin uploads a NEET paper PDF directly through the admin panel.
2. **Enter Metadata:** The admin specifies metadata (year, code, subjects, type).
3. **Save Original PDF:** The backend saves the PDF to `data/papers/<paper_id>.pdf`.
4. **Parse All Questions:** The sequence-aware parser parses all questions from the PDF, checking for option-index collisions.
5. **Extract/Crop Diagrams and Question Regions:**
   * Images/diagrams are physically associated with the matching questions on the page.
   * If a question contains complex equations/formatting, or is flagged for manual review, the parser crops the original PDF question bounding box as a PNG asset to act as a fallback.
6. **Save Draft Records to DB:** The paper is saved in `draft` status, and all 180 questions are saved as `draft` questions.
7. **Review in Admin UI:** The admin reviews each question, its options, answer keys, and extracted images/crops in the review table/modal.
8. **Approve & Publish:** The admin approves questions and publishes the paper, making it live for students.

---

## 3. Required Paper Metadata

When uploading a paper, the following metadata fields must be provided and stored:
* **Exam:** The exam name (e.g., `NEET`).
* **Year:** The year the exam was held (e.g., `2024`).
* **Set/Code:** The paper set identifier or code (e.g., `Model 10` or `Set R3`).
* **Source/Provider:** The source organization (e.g., `Vedantu`, `Allen`, `NTA`).
* **Paper Type:** One of the following categories:
  * Questions only
  * Questions + options
  * Questions + options + answer key
  * Questions + options + answer key + solutions
  * AI-generated
* **Subjects Included:** List of subjects included (e.g., `Physics`, `Chemistry`, `Biology`, `Full paper`).
* **Expected Question Count:** The total number of questions expected (typically `180` for standard NEET).

---

## 4. Full NEET Paper Rules

Standard NEET papers must follow these subject range conventions during parsing:
* **Expected Total:** Exactly 180 questions.
* **Physics:** Questions 1–45.
* **Chemistry:** Questions 46–90.
* **Biology:** Questions 91–180, unless Botany/Zoology sections are explicitly labeled.
* **Subject Uncertainty:** If subject detection is uncertain or does not align with expected ranges, mark the subject as `Unknown / Needs Review` instead of defaulting to Physics or Biology. Do not let options (1-4) override question sequence tracking.

---

## 5. Question Storage Rules

For every parsed question, the database stores:
* **Global Question Number:** The absolute number in the paper (1-180).
* **Subject:** The classified subject (e.g., Physics, Chemistry, Biology, Botany, Zoology, or Unknown).
* **Subject-Local Question Number:** The number of the question within its subject (e.g., Q46 is Chemistry local Q1).
* **Question Text:** The parsed text of the question.
* **Options:** Text values for options A, B, C, and D.
* **Correct Answer:** The correct option (A, B, C, or D) mapped from the answer key if available.
* **Solution Text:** The explanation text if available.
* **Source Page:** The physical page number in the source PDF.
* **Image/Diagram/Crop Asset References:** URLs linking to extracted images and visual question crops.
* **Parse Confidence:** The computed confidence score (e.g., 0.85 for successful regex, 0.60 for flagged review).
* **Review Reasons:** Array of warnings/reasons why manual review is needed (e.g., math symbols, missing options).
* **Publish Status:** The lifecycle state (`draft` or `published`).

---

## 6. Image and Diagram Handling

The parser automatically detects and extracts images using coordinates:
* **Real Diagrams/Images:** Extracted using PDF image extraction, filtering out decorative images (under 3KB). They are aligned with question bounding boxes in the same column and linked.
* **Fallback Bounding Box Crop:** When math symbols, complex formatting, or diagrams are detected, the parser crops the visual area of the question directly from the PDF page at 150 DPI and saves it as a `crop` asset (stored at `data/assets/papers/<paper_id>/q<num>_crop.png`).
* **UI Integration:** The review modal loads and displays the original PDF crop and any extracted diagrams to ensure perfect readability during manual review.
* **Filtering Noise:** Do not mark every text layout issue as a diagram; verify physical overlaps.

---

## 7. Review Lifecycle

A question paper moves through the following ingestion states:
1. **Draft:** Initial status after backend ingestion. Questions and assets are stored as drafts and visible only in the admin review interface.
2. **Needs Review:** Questions with low confidence, missing options, math symbols, or associated diagrams are flagged with `needs_manual_review = True`.
3. **Approved:** Individual questions are marked as approved by the admin.
4. **Published:** The paper status becomes `approved` (and questions set to `published`). The paper is now live and available for test generation.
5. **Failed:** Ingestion or parsing encountered fatal errors (e.g., corrupted PDF).

---

## 8. Ingestion Verification Checklist

After parsing, the admin (or agent) must verify the following items before publishing:
- [ ] **Expected vs. Parsed Count:** Confirm that the parsed question count matches the expected count (e.g., exactly 180 questions for a full paper).
- [ ] **Subject Breakdown:** Ensure the count matches NEET standard partitions:
  * Physics: 45 questions (Q1–Q45)
  * Chemistry: 45 questions (Q46–Q90)
  * Biology: 90 questions (Q91–Q180)
- [ ] **Options Extracted:** Verify that options A, B, C, and D are populated and not empty.
- [ ] **Answer Key Status:** Check that correct options are pre-filled from `parsed_answers.json` or show up in the questions list.
- [ ] **Diagrams/Crops Visible:** Confirm that visual fallback crops and diagrams load correctly in the question detail modal.
- [ ] **Paper Library:** Check that the paper record appears in the Question Paper Library table with the correct status.
- [ ] **Publish Flow:** Test approving individual questions and successfully publishing the entire paper as a test.
