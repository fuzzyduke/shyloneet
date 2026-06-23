#!/usr/bin/env python3
"""
Reusable CLI script to upload a question paper PDF to the Shyloneet backend.
Part of the shyloneet/ingest superpower.

Usage:
    python upload_paper.py --pdf "path/to/paper.pdf" --year 2026
    python upload_paper.py --pdf "path/to/paper.pdf" --year 2026 --api-base "https://shyloneetv1.valhallala.com"
"""

import argparse
import sys
import os
import requests


def main():
    parser = argparse.ArgumentParser(description="Upload a question paper PDF to the Shyloneet backend")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Backend API base (no trailing slash)")
    parser.add_argument("--exam", default="NEET", help="Exam name")
    parser.add_argument("--year", required=True, type=int, help="Year of the paper")
    parser.add_argument("--set-code", default="Model 10", help="Set/code identifier")
    parser.add_argument("--source", default="Vedantu", help="Source publisher")
    parser.add_argument("--paper-type", default="questions_with_options_and_answer_key", help="Paper type")
    parser.add_argument("--subjects", default="Physics,Chemistry,Biology", help="Comma-separated subjects")
    parser.add_argument("--token", default=None, help="Bearer auth token (reads from AUTH_TOKEN env var if not provided)")

    args = parser.parse_args()

    # Validate PDF exists
    if not os.path.exists(args.pdf):
        print(f"ERROR: PDF not found at: {args.pdf}")
        sys.exit(1)

    # Auth token
    token = args.token or os.environ.get("AUTH_TOKEN", "")

    # Build endpoint URL
    url = args.api_base.rstrip("/") + "/api/v1/admin/papers/upload_pdf"

    # Prepare multipart upload — field name must be 'file' to match FastAPI endpoint
    with open(args.pdf, "rb") as pdf_file:
        files = {"file": (os.path.basename(args.pdf), pdf_file, "application/pdf")}
        data = {
            "exam": args.exam,
            "year": args.year,
            "set_code": args.set_code,
            "source": args.source,
            "paper_type": args.paper_type,
            "subjects_included": args.subjects,  # field name matches backend Form()
        }
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        print(f"Uploading: {os.path.basename(args.pdf)}")
        print(f"Endpoint: {url}")
        print(f"Metadata: exam={args.exam}, year={args.year}, set_code={args.set_code}, source={args.source}")

        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=300)
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Could not connect to {args.api_base}. Is the server running?")
            sys.exit(1)

    if response.status_code == 200:
        result = response.json()
        print(f"\nSUCCESS!")
        print(f"  Paper ID: {result.get('paper_id', 'unknown')}")
        print(f"  Message:  {result.get('message', '')}")
    else:
        print(f"\nFAILED (HTTP {response.status_code})")
        try:
            print(f"  Detail: {response.json().get('detail', response.text)}")
        except Exception:
            print(f"  Response: {response.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
