import os
from database import SessionLocal
from models import Chapter, ChapterChunk, ChapterAsset
import random

db = SessionLocal()
chapters = db.query(Chapter).order_by(Chapter.chapter_number).all()

print("--- 1. Average chunk length per chapter ---")
for c in chapters:
    chunks = db.query(ChapterChunk).filter(ChapterChunk.chapter_id == c.id).all()
    if chunks:
        lens = [len(ch.chunk_text) for ch in chunks]
        words = [len(ch.chunk_text.split()) for ch in chunks]
        avg_len = sum(lens) / len(lens)
        avg_words = sum(words) / len(words)
        print(f"Chapter {c.chapter_number}: Avg Chars: {avg_len:.1f} | Avg Words: {avg_words:.1f} | Min: {min(lens)} | Max: {max(lens)}")
    else:
        print(f"Chapter {c.chapter_number}: No chunks")

print("\n--- 2 & 3. Sample chunks ---")
sample_chapters = [1, 3, 9, 14]
for num in sample_chapters:
    c = db.query(Chapter).filter(Chapter.chapter_number == num).first()
    if c:
        chunks = db.query(ChapterChunk).filter(ChapterChunk.chapter_id == c.id).all()
        # Filter out very short ones to get meaningful samples
        valid_chunks = [ch for ch in chunks if len(ch.chunk_text) > 100]
        samples = random.sample(valid_chunks, min(3, len(valid_chunks)))
        print(f"\n>> Chapter {num}: {c.chapter_name}")
        for i, s in enumerate(samples):
            # Print a snippet of max 200 chars
            snippet = s.chunk_text[:200].replace('\n', ' ')
            print(f"  Sample {i+1}: {snippet}...")

print("\n--- 4 & 5. Sample Extracted Assets ---")
assets = db.query(ChapterAsset).limit(2).all()
for a in assets:
    print(f"Asset ID: {a.id}")
    print(f"Image URL: {a.image_url}")
    print(f"Chapter ID: {a.chapter_id}")
    print(f"Page Number: {a.page_number}")
    print(f"Asset Type: {a.asset_type}")
    print("---")

print("\nConfirming chapter_assets are not question_assets:")
from models import QuestionAsset
q_assets = db.query(QuestionAsset).count()
print(f"Total Question Assets: {q_assets}")

db.close()
