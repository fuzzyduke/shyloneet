import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import SessionLocal
from paper_triage import triage_parse_paper
import models

db = SessionLocal()
try:
    print("Starting parse of backend/sample_paper_10.pdf...")
    paper_id = triage_parse_paper("backend/sample_paper_10.pdf", db)
    print("Parse succeeded! Paper ID:", paper_id)
    
    # Query database to print results
    paper = db.query(models.QuestionPaper).filter(models.QuestionPaper.id == paper_id).first()
    questions = db.query(models.Question).filter(models.Question.paper_id == paper_id).all()
    print("Paper title in DB:", paper.source_file)
    print("Total parsed questions:", len(questions))
    
    subjects = {}
    for q in questions:
        subjects[q.subject] = subjects.get(q.subject, 0) + 1
    print("Subject breakdown:", subjects)
    
    # Check if assets were extracted
    assets_count = db.query(models.QuestionAsset).join(models.Question).filter(models.Question.paper_id == paper_id).count()
    print("Total image assets extracted:", assets_count)
# ---- New Assertions for page 1 ----
    page1_questions = [q for q in questions if q.page_number == 1]
    # Expect exactly Q1 and Q2 on page 1
    assert len(page1_questions) == 2, f"Expected 2 questions on page 1, found {len(page1_questions)}"
    page1_nums = sorted([q.question_number for q in page1_questions])
    assert page1_nums == [1, 2], f"Expected question numbers [1,2] on page 1, got {page1_nums}"
    print("Page 1 assertions passed: only Q1 and Q2 present.")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
