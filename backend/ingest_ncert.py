"""
ingest_ncert.py — Enhanced NCERT Physics PDF Ingestion (v2)

Fixes over v1:
  1. Correct chapter/class parsing via ncert_chapter_map.parse_leph_filename()
  2. exam_program_id = "NEET" set on every Chapter
  3. Unicode-safe text extraction (no ascii encode/ignore)
  4. Chunk-type tagging: heading / example / exercise / text
  5. Supplementary PDFs (leph1an, leph1ps, leph2an, leph2ps) are skipped
  6. Idempotent: deletes old chunks/assets before re-ingesting
  7. Writes ingest_report.json at the end of a batch run
"""

import os
import glob
import json
import fitz  # PyMuPDF
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import Chapter, ChapterChunk, ChapterAsset
from ncert_chapter_map import parse_ncert_filename, get_chapter_name

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# PDFs that contain answers / practice problems — skip them for the main corpus
SUPPLEMENTARY_STEMS = {"leph1an", "leph1ps", "leph2an", "leph2ps"}

# Minimum image byte size to be considered a real diagram (not a decorative icon)
MIN_IMAGE_BYTES = 5_000

# Threshold below which a block is probably a header (heuristic: short + uppercase)
HEADING_MAX_LEN = 120


def _classify_chunk_type(block_text: str, font_info: dict | None = None) -> str:
    """
    Heuristically determine the chunk_type for a text block.

    Types: heading | example | exercise | text
    """
    stripped = block_text.strip()
    lower = stripped.lower()

    # Example blocks
    if lower.startswith("example") or lower.startswith("solved example"):
        return "example"

    # Exercise / activity blocks
    if lower.startswith("exercise") or lower.startswith("activity") or lower.startswith("points to ponder"):
        return "exercise"

    # Short ALL-CAPS lines are usually section headings
    if len(stripped) < HEADING_MAX_LEN and stripped == stripped.upper() and stripped.replace(" ", "").isalpha():
        return "heading"

    return "text"


def ingest_pdf(db: Session, filepath: str) -> dict:
    """
    Ingest a single NCERT Physics chapter PDF into the database.

    Returns a summary dict for reporting.
    """
    filename = os.path.basename(filepath)
    stem = filename.lower().replace(".pdf", "")

    # --- Guard: skip supplementary files ---
    if stem in SUPPLEMENTARY_STEMS:
        print(f"  [SKIP] {filename} is a supplementary file - not ingested into chapter corpus.")
        return {"file": filename, "status": "skipped", "reason": "supplementary"}

    # --- Parse filename → subject + class level + chapter number ---
    parsed = parse_ncert_filename(filename)
    if parsed is None:
        print(f"  [SKIP] {filename} — unrecognised filename pattern.")
        return {"file": filename, "status": "skipped", "reason": "unrecognised_filename"}

    subject, class_level, chapter_number, _raw_code = parsed
    chapter_name = get_chapter_name(subject, class_level, chapter_number)

    print(f"  [START] {filename} -> {subject} Class {class_level}, Chapter {chapter_number}: {chapter_name}")

    # --- Upsert Chapter row ---
    chapter = db.query(Chapter).filter(Chapter.file_name == filename).first()
    if chapter:
        # Delete existing chunks and assets so we can re-ingest cleanly
        old_chunk_ids = [c.id for c in db.query(ChapterChunk).filter(ChapterChunk.chapter_id == chapter.id).all()]
        db.query(ChapterAsset).filter(ChapterAsset.chapter_id == chapter.id).delete(synchronize_session=False)
        db.query(ChapterChunk).filter(ChapterChunk.chapter_id == chapter.id).delete(synchronize_session=False)
        db.commit()
        print(f"    Cleared {len(old_chunk_ids)} old chunks for fresh re-ingest.")

        # Update fields that may have been wrong in v1
        chapter.subject = subject
        chapter.source = "NCERT"
        chapter.class_level = class_level
        chapter.chapter_number = chapter_number
        chapter.chapter_name = chapter_name
        chapter.exam_program_id = "NEET"
        chapter.source_type = "reference_book"
        chapter.source_name = f"NCERT {subject}"
        db.commit()
    else:
        chapter = Chapter(
            subject=subject,
            source="NCERT",
            class_level=class_level,
            chapter_number=chapter_number,
            chapter_name=chapter_name,
            file_name=filename,
            exam_program_id="NEET",
            source_type="reference_book",
            source_name=f"NCERT {subject}",
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)

    # --- Setup assets directory ---
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "data", "assets", "chapters", chapter.id)
    os.makedirs(assets_dir, exist_ok=True)

    # --- Open PDF ---
    doc = fitz.open(filepath)

    chunks_created = 0
    images_saved = 0
    seen_xrefs: set[int] = set()  # avoid duplicate image extraction across pages

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # ---- TEXT EXTRACTION ----
        # Use "dict" mode to get font/size information for chunk-type tagging
        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # type 0 = text
                continue

            # Reconstruct block text from spans, preserving Unicode
            block_text_parts = []
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                block_text_parts.append(line_text)
            block_text = "\n".join(block_text_parts).strip()

            if len(block_text) < 20:  # Skip very short artifacts / page numbers
                continue

            chunk_type = _classify_chunk_type(block_text)

            chunk = ChapterChunk(
                chapter_id=chapter.id,
                page_number=page_num + 1,
                chunk_text=block_text,
                chunk_type=chunk_type,
                embedding="[]",  # Placeholder — filled by generate_embeddings.py
            )
            db.add(chunk)
            chunks_created += 1

        # ---- IMAGE EXTRACTION ----
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            if xref in seen_xrefs:
                continue  # same image embedded on multiple pages — save once
            seen_xrefs.add(xref)

            try:
                # Use Pixmap to render the image correctly instead of extracting raw stream
                pix = fitz.Pixmap(doc, xref)
                # Convert to RGB if it's CMYK or has a different colorspace
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                image_bytes = pix.tobytes("png")
                image_ext = "png"
                pix = None  # Free memory
            except Exception as e:
                print(f"    [WARN] Could not extract image xref {xref} on page {page_num + 1}: {e}")
                continue

            if len(image_bytes) < MIN_IMAGE_BYTES:
                continue  # skip tiny decorative icons

            image_filename = f"page_{page_num + 1}_img_{img_index}.{image_ext}"
            image_path = os.path.join(assets_dir, image_filename)

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            asset = ChapterAsset(
                chapter_id=chapter.id,
                page_number=page_num + 1,
                asset_type="diagram",
                image_url=f"/data/assets/chapters/{chapter.id}/{image_filename}",
                caption=f"Image from page {page_num + 1}",
            )
            db.add(asset)
            images_saved += 1

    db.commit()
    page_count = len(doc)  # capture before close
    doc.close()

    summary = {
        "file": filename,
        "class": class_level,
        "chapter": chapter_number,
        "chapter_name": chapter_name,
        "pages": page_count,
        "chunks": chunks_created,
        "images": images_saved,
        "status": "ok" if chunks_created >= 20 else "low_chunks",
    }
    print(f"  [DONE] {filename}: {chunks_created} chunks, {images_saved} images - {summary['status'].upper()}")
    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest_ncert.py <path_to_pdf_directory_or_file>")
        sys.exit(1)

    path = sys.argv[1]
    db = SessionLocal()
    results = []

    if os.path.isdir(path):
        pdf_files = sorted(glob.glob(os.path.join(path, "*.pdf")))
        print(f"Found {len(pdf_files)} PDFs in {path}")
        for pdf in pdf_files:
            result = ingest_pdf(db, pdf)
            results.append(result)
    elif os.path.isfile(path) and path.lower().endswith(".pdf"):
        result = ingest_pdf(db, path)
        results.append(result)
    else:
        print("Invalid path provided.")
        sys.exit(1)

    db.close()

    # Write report
    report_path = os.path.join(os.path.dirname(__file__), "ingest_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    ok = sum(1 for r in results if r.get("status") == "ok")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    low = sum(1 for r in results if r.get("status") == "low_chunks")
    print(f"\nIngestion complete: {ok} OK, {low} low-chunk, {skipped} skipped.")
    print(f"Report saved to: {report_path}")
