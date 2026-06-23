import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from paper_triage import triage_parse_paper
from database import SessionLocal
import models

def generate_json():
    db = SessionLocal()
    pdf_path = os.path.join(os.path.dirname(__file__), 'backend', 'sample_paper_10.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return
    
    print("Running triage on PDF...")
    try:
        paper_id = triage_parse_paper(pdf_path, db)
        print(f"Triage successful. Paper ID: {paper_id}")
    except Exception as e:
        print(f"Failed to triage: {e}")
        return

    # Fetch parsed questions
    paper = db.query(models.QuestionPaper).filter(models.QuestionPaper.id == paper_id).first()
    questions = db.query(models.Question).filter(models.Question.paper_id == paper_id).order_by(models.Question.question_number.asc()).all()
    
    total_parsed = len(questions)
    needs_review_count = sum(1 for q in questions if q.needs_manual_review)
    with_diagrams = sum(1 for q in questions if len(q.assets) > 0)
    with_options = sum(1 for q in questions if q.option_a and q.option_b and q.option_c and q.option_d)
    
    q_nums = [q.question_number for q in questions]
    missing_nums = [i for i in range(1, 46) if i not in q_nums]
    duplicate_nums = list(set([x for x in q_nums if q_nums.count(x) > 1]))
    
    serialized_qs = []
    for q in questions:
        reasons = []
        if q.incompatibility_flags:
            try:
                reasons = json.loads(q.incompatibility_flags)
            except:
                reasons = [q.incompatibility_flags]
                
        serialized_qs.append({
            "id": f"ag-{q.id}",  # Using AG prefix to mark it as AG output
            "question_number": q.question_number,
            "question_text": q.question_text,
            "options": {
                "1": q.option_a,
                "2": q.option_b,
                "3": q.option_c,
                "4": q.option_d
            },
            "has_diagram": len(q.assets) > 0,
            "diagram_url": q.assets[0].image_url if q.assets else None,
            "page_number": q.page_number,
            "needs_review": q.needs_manual_review,
            "review_reasons": reasons,
            "raw_text": getattr(q, "raw_text", getattr(q, "question_text", ""))
        })
        
    output_json = {
        "metadata": {
            "title": "NEET Sample Paper Model 10 - Physics",
            "exam_name": "NEET",
            "paper_type": "sample/model/practice",
            "source_name": "Vedantu",
            "subject": "Physics",
            "source_type": "question_paper",
            "question_range": "1-45",
            "has_solutions": True,
            "source_filename": "NEET Sample Paper 10 Practice Set PDF with Solutions.pdf",
            "year": 2024,
            "paper_code": "VEDANTU-MODEL-10"
        },
        "stats": {
            "total_expected": 45,
            "total_parsed": total_parsed,
            "needs_review": needs_review_count,
            "with_diagrams": with_diagrams,
            "with_options": with_options,
            "missing_numbers": missing_nums,
            "duplicate_numbers": duplicate_nums,
            "chemistry_ignored": True
        },
        "questions": serialized_qs
    }
    
    out_path = os.path.join(os.path.dirname(__file__), 'paper_triage.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {out_path} with {total_parsed} questions.")

if __name__ == "__main__":
    generate_json()
