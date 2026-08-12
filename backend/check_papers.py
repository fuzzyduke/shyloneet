import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import models

db = SessionLocal()
papers = db.query(models.QuestionPaper).all()
for p in papers:
    q_count = db.query(models.Question).filter(models.Question.paper_id == p.id).count()
    print(f"Paper: {p.id} | Title: {getattr(p, 'title', p.source_file)} | Year: {p.year} | Questions: {q_count}")
