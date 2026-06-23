"""
ingest_physics_ncert.py — Orchestrator for NCERT Physics PDF Ingestion

Runs the full pipeline:
  1. Ingest all chapter PDFs via ingest_ncert.ingest_pdf()
  2. Auto-generate embeddings via generate_embeddings.run_embeddings()
  3. Print a final coverage table

Usage:
  python ingest_physics_ncert.py --pdf-dir "C:\\path\\to\\physics\\pdfs"
  python ingest_physics_ncert.py  # uses PDF_DIR env var or prompts
"""

import argparse
import json
import os
import sys
import time
import glob
from datetime import datetime

# ---- Make sure we can import sibling modules from backend/ ----
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from ingest_ncert import ingest_pdf
from ncert_chapter_map import parse_leph_filename, get_chapter_name

# ANSI colour helpers (gracefully disabled on Windows if not supported)
try:
    import colorama
    colorama.init(autoreset=True)
    GREEN  = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    RED    = colorama.Fore.RED
    RESET  = colorama.Style.RESET_ALL
except ImportError:
    GREEN = YELLOW = RED = RESET = ""


def _status_icon(status: str) -> str:
    return {
        "ok":         f"{GREEN}[OK]{RESET}",
        "low_chunks": f"{YELLOW}[LOW]{RESET}",
        "skipped":    f"{YELLOW}[SKIP]{RESET}",
        "error":      f"{RED}[ERR]{RESET}",
    }.get(status, status)


def print_coverage_table(results: list[dict]) -> None:
    header = f"{'File':<16} {'Cl':>3} {'Ch':>3} {'Chapter Name':<38} {'Chunks':>6} {'Images':>6} {'Status'}"
    print("\n" + "=" * 90)
    print("INGESTION COVERAGE REPORT")
    print("=" * 90)
    print(header)
    print("-" * 90)
    for r in results:
        if r.get("status") == "skipped":
            print(f"  {r['file']:<14} {'-':>3} {'-':>3} {'(supplementary / skipped)':<38} {'-':>6} {'-':>6}  [SKIP]")
        else:
            print(
                f"  {r['file']:<14} {r.get('class', '?'):>3} {r.get('chapter', '?'):>3} "
                f"{r.get('chapter_name', '?'):<38} "
                f"{r.get('chunks', 0):>6} {r.get('images', 0):>6}  {_status_icon(r.get('status', '?'))}"
            )
    print("=" * 90)
    ok      = sum(1 for r in results if r.get("status") == "ok")
    low     = sum(1 for r in results if r.get("status") == "low_chunks")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    errors  = sum(1 for r in results if r.get("status") == "error")
    total_chunks = sum(r.get("chunks", 0) for r in results)
    total_images = sum(r.get("images", 0) for r in results)
    print(f"  Chapters: {ok} OK | {low} low-chunk | {skipped} skipped | {errors} error")
    print(f"  Total chunks: {total_chunks} | Total images: {total_images}")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest NCERT Physics PDFs into the shyloneet database."
    )
    parser.add_argument(
        "--pdf-dir",
        default=os.environ.get("SHYLO_PHYSICS_PDF_DIR", ""),
        help="Directory containing NCERT Physics PDFs (leph1xx.pdf, leph2xx.pdf, ...)",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip the embedding generation step (useful for quick iteration).",
    )
    args = parser.parse_args()

    pdf_dir = args.pdf_dir.strip()
    if not pdf_dir:
        pdf_dir = input("Enter path to physics PDFs directory: ").strip().strip('"')

    if not os.path.isdir(pdf_dir):
        print(f"{RED}ERROR: Directory not found: {pdf_dir}{RESET}")
        sys.exit(1)

    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    if not pdf_files:
        print(f"{RED}ERROR: No PDF files found in {pdf_dir}{RESET}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  NCERT Physics Ingestion Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Source:  {pdf_dir}")
    print(f"  PDFs:    {len(pdf_files)} files")
    print(f"{'='*60}\n")

    db = SessionLocal()
    results: list[dict] = []
    t_start = time.time()

    for pdf_path in pdf_files:
        print(f">> Processing: {os.path.basename(pdf_path)}")
        try:
            result = ingest_pdf(db, pdf_path)
        except Exception as e:
            fname = os.path.basename(pdf_path)
            print(f"  {RED}[ERROR] {fname}: {e}{RESET}")
            result = {"file": fname, "status": "error", "error": str(e)}
        results.append(result)
        print()

    db.close()

    elapsed = time.time() - t_start
    print(f"Ingestion finished in {elapsed:.1f}s")

    # Save JSON report
    report_path = os.path.join(os.path.dirname(__file__), "ingest_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved: {report_path}")

    # Print coverage table
    print_coverage_table(results)

    # ---- Step 2: Generate embeddings ----
    if not args.skip_embeddings:
        print("Generating sentence-transformer embeddings for new chunks...")
        try:
            from generate_embeddings import run_embeddings
            run_embeddings()
        except Exception as e:
            print(f"{RED}[WARN] Embedding generation failed: {e}{RESET}")
            print("Run manually: python generate_embeddings.py")
    else:
        print("(Embedding generation skipped - run python generate_embeddings.py when ready)")

    print(f"\n{GREEN}[DONE] Pipeline complete.{RESET}")
    print("Next step: python verify_ncert_coverage.py\n")


if __name__ == "__main__":
    main()
