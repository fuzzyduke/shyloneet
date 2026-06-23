"""
verify_ncert_coverage.py — Post-ingestion Coverage Verification

Queries the database and produces a Markdown coverage report.
Flags:
  - Chapters with 0 chunks  → likely extraction failure
  - Chapters with < 30 chunks → possible truncation
  - Chapters with 0 images  → possible image extraction failure
  - Chunks with empty embeddings → need to run generate_embeddings.py

Usage:
  python verify_ncert_coverage.py
  python verify_ncert_coverage.py --out my_report.md
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Chapter, ChapterChunk, ChapterAsset
from sqlalchemy import func

LOW_CHUNK_THRESHOLD = 30


def verify() -> tuple[list[dict], dict]:
    db = SessionLocal()

    chapters = (
        db.query(Chapter)
        .filter(Chapter.subject == "Physics", Chapter.exam_program_id == "NEET")
        .order_by(Chapter.class_level, Chapter.chapter_number)
        .all()
    )

    rows = []
    summary = {
        "total_chapters": 0,
        "total_chunks": 0,
        "total_images": 0,
        "total_embedded": 0,
        "total_unembedded": 0,
        "zero_chunk_chapters": [],
        "low_chunk_chapters": [],
        "zero_image_chapters": [],
    }

    for ch in chapters:
        chunk_count = db.query(func.count(ChapterChunk.id)).filter(ChapterChunk.chapter_id == ch.id).scalar()
        image_count = db.query(func.count(ChapterAsset.id)).filter(ChapterAsset.chapter_id == ch.id).scalar()
        embedded_count = (
            db.query(func.count(ChapterChunk.id))
            .filter(
                ChapterChunk.chapter_id == ch.id,
                ChapterChunk.embedding != None,
                ChapterChunk.embedding != "[]",
            )
            .scalar()
        )
        unembedded_count = chunk_count - embedded_count

        flags = []
        if chunk_count == 0:
            flags.append("NO_CHUNKS")
            summary["zero_chunk_chapters"].append(ch.file_name)
        elif chunk_count < LOW_CHUNK_THRESHOLD:
            flags.append("LOW_CHUNKS")
            summary["low_chunk_chapters"].append(ch.file_name)

        if image_count == 0:
            flags.append("NO_IMAGES")
            summary["zero_image_chapters"].append(ch.file_name)

        if unembedded_count > 0:
            flags.append(f"MISSING_EMBEDS({unembedded_count})")

        status = "[OK]" if not flags else ("[FAIL]" if "NO_CHUNKS" in flags else "[WARN]")

        rows.append({
            "file": ch.file_name,
            "class": ch.class_level,
            "chapter": ch.chapter_number,
            "name": ch.chapter_name,
            "chunks": chunk_count,
            "images": image_count,
            "embedded": embedded_count,
            "unembedded": unembedded_count,
            "flags": ", ".join(flags) if flags else "—",
            "status": status,
        })

        summary["total_chapters"] += 1
        summary["total_chunks"] += chunk_count
        summary["total_images"] += image_count
        summary["total_embedded"] += embedded_count
        summary["total_unembedded"] += unembedded_count

    db.close()
    return rows, summary


def build_markdown(rows: list[dict], summary: dict, pdf_dir: str = "") -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# NCERT Physics Ingestion — Coverage Report",
        f"",
        f"**Generated:** {ts}",
        f"**PDF Source:** `{pdf_dir or 'n/a'}`",
        f"",
        f"## Chapter Coverage",
        f"",
        f"| File | Cl | Ch | Chapter Name | Chunks | Images | Embedded | Flags | Status |",
        f"|------|----|----|--------------|-------:|-------:|---------:|-------|--------|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['file']}` | {r['class']} | {r['chapter']} | {r['name']} "
            f"| {r['chunks']} | {r['images']} | {r['embedded']} | {r['flags']} | {r['status']} |"
        )

    lines += [
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Chapters | {summary['total_chapters']} |",
        f"| Total Chunks | {summary['total_chunks']} |",
        f"| Total Images | {summary['total_images']} |",
        f"| Embedded Chunks | {summary['total_embedded']} |",
        f"| Chunks Missing Embeddings | {summary['total_unembedded']} |",
        f"",
    ]

    if summary["zero_chunk_chapters"]:
        lines.append(f"> ❌ **Zero-chunk chapters (extraction failure):** {', '.join(summary['zero_chunk_chapters'])}")
        lines.append(f">")
    if summary["low_chunk_chapters"]:
        lines.append(f"> ⚠️ **Low-chunk chapters (< {LOW_CHUNK_THRESHOLD} chunks):** {', '.join(summary['low_chunk_chapters'])}")
        lines.append(f">")
    if summary["zero_image_chapters"]:
        lines.append(f"> ℹ️ **Zero-image chapters:** {', '.join(summary['zero_image_chapters'])}")
        lines.append(f">")
    if summary["total_unembedded"] > 0:
        lines.append(f"> ⚠️ **{summary['total_unembedded']} chunks are missing embeddings** — run `python generate_embeddings.py`")
        lines.append(f">")

    if not (summary["zero_chunk_chapters"] or summary["low_chunk_chapters"] or summary["total_unembedded"]):
        lines.append(f"> ✅ All chapters look healthy. Ingestion corpus is ready for classification.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Verify NCERT Physics ingestion coverage.")
    parser.add_argument("--out", default="ingest_coverage_report.md", help="Output Markdown file path")
    parser.add_argument("--pdf-dir", default="", help="PDF source path (for report header only)")
    args = parser.parse_args()

    print("Querying database…")
    rows, summary = verify()

    if not rows:
        print("No Physics chapters found in the database with exam_program_id='NEET'.")
        print("Run ingest_physics_ncert.py first.")
        sys.exit(1)

    md = build_markdown(rows, summary, args.pdf_dir)

    # Print to console
    print(f"\n{'='*70}")
    print("COVERAGE SUMMARY")
    print(f"{'='*70}")
    print(f"  Chapters: {summary['total_chapters']}")
    print(f"  Chunks:   {summary['total_chunks']}")
    print(f"  Images:   {summary['total_images']}")
    print(f"  Embedded: {summary['total_embedded']} / {summary['total_chunks']}")
    if summary["zero_chunk_chapters"]:
        print(f"\n  [FAIL] (no chunks): {', '.join(summary['zero_chunk_chapters'])}")
    if summary["low_chunk_chapters"]:
        print(f"  [WARN] LOW CHUNKS:        {', '.join(summary['low_chunk_chapters'])}")
    if summary["total_unembedded"] > 0:
        print(f"  [WARN] MISSING EMBEDS:    {summary['total_unembedded']} chunks - run generate_embeddings.py")
    print(f"{'='*70}\n")

    # Save Markdown report
    out_path = args.out if os.path.isabs(args.out) else os.path.join(os.path.dirname(__file__), args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[DONE] Markdown report saved: {out_path}")


if __name__ == "__main__":
    main()
