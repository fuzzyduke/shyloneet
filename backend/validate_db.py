import os
from database import SessionLocal, engine
from models import Chapter, ChapterChunk, ChapterAsset
import sqlalchemy

db = SessionLocal()

print("--- 1. Total number of records in the chapters table ---")
chapters = db.query(Chapter).all()
print(f"Total Chapters: {len(chapters)}")

print("\n--- 2. List all chapter records ---")
for c in chapters:
    print(f"ID: {c.id} | Subj: {c.subject} | Source: {c.source} | Class: {c.class_level} | Ch_Num: {c.chapter_number} | Name: {c.chapter_name} | File: {c.file_name}")

print("\n--- 5 & 6. Report chunk count & asset count per chapter ---")
for c in chapters:
    chunk_count = db.query(ChapterChunk).filter(ChapterChunk.chapter_id == c.id).count()
    asset_count = db.query(ChapterAsset).filter(ChapterAsset.chapter_id == c.id).count()
    print(f"File: {c.file_name} -> Chunks: {chunk_count}, Assets: {asset_count}")

print("\n--- 7. Confirm whether embeddings were generated for chapter chunks ---")
first_chunk = db.query(ChapterChunk).first()
if first_chunk:
    print(f"Sample chunk embedding field value: {first_chunk.embedding}")

print("\n--- 8. Database path and tables ---")
print(f"Engine URL: {engine.url}")
inspector = sqlalchemy.inspect(engine)
print(f"Tables: {inspector.get_table_names()}")

db.close()
