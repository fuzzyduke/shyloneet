import sys
sys.path.append(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")
from database import SessionLocal
from models import QuestionPaper, Question
from sqlalchemy import func

def verify_state():
    db = SessionLocal()
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == 'neet-2024').first()
    
    if paper:
        print("=== Paper State ===")
        print(f"Paper ID: {paper.id}")
        print(f"Paper Name: {paper.name}")
        print(f"Exam Program ID: {paper.exam_program_id}")
        print(f"Year: {paper.year}")
        print(f"Exam Type: {paper.exam_type}")
        print(f"Solution Status: {paper.solution_status}")
        print(f"Scoring Enabled: {paper.scoring_enabled}")
        print(f"Scoring Source: {paper.scoring_source}")
        print(f"Answer Key Detected: {paper.answer_key_detected}")
        print(f"Solution Review Required: {paper.solution_review_required}")
    else:
        print("Paper 'neet-2024' not found in QuestionPaper table.")
        
    print("\n=== Question State ===")
    total = db.query(Question).filter_by(paper_id='neet-2024').count()
    print(f"Total Questions: {total}")
    
    if total > 0:
        with_answer = db.query(Question).filter(Question.paper_id == 'neet-2024', Question.answer.isnot(None), Question.answer != '').count()
        with_solution = db.query(Question).filter(Question.paper_id == 'neet-2024', Question.solution_text.isnot(None), Question.solution_text != '').count()
        status_official = db.query(Question).filter_by(paper_id='neet-2024', answer_status='official_from_paper').count()
        status_ai = db.query(Question).filter_by(paper_id='neet-2024', answer_status='ai_mapped').count()
        status_admin = db.query(Question).filter_by(paper_id='neet-2024', answer_status='manual_admin').count()
        status_unavail = db.query(Question).filter_by(paper_id='neet-2024', answer_status='unavailable').count()
        scoring_eligible = db.query(Question).filter_by(paper_id='neet-2024', scoring_eligible=True).count()
        scoring_ineligible = db.query(Question).filter_by(paper_id='neet-2024', scoring_eligible=False).count()
        is_mock_count = db.query(Question).filter_by(paper_id='neet-2024', is_mock=True).count()
        is_not_mock_count = db.query(Question).filter_by(paper_id='neet-2024', is_mock=False).count()
        source_real = db.query(Question).filter_by(paper_id='neet-2024', source_type='real_pdf_extraction').count()
        
        print(f"Questions with correct_option: {with_answer}")
        print(f"Questions with solution_text: {with_solution}")
        print(f"Questions with answer_status = official_from_paper: {status_official}")
        print(f"Questions with answer_status = ai_mapped: {status_ai}")
        print(f"Questions with answer_status = manual_admin: {status_admin}")
        print(f"Questions with answer_status = unavailable: {status_unavail}")
        print(f"Questions with scoring_eligible = True: {scoring_eligible}")
        print(f"Questions with scoring_eligible = False: {scoring_ineligible}")
        print(f"Questions with is_mock = True: {is_mock_count}")
        print(f"Questions with is_mock = False: {is_not_mock_count}")
        print(f"Questions with source_type = real_pdf_extraction: {source_real}")

if __name__ == "__main__":
    verify_state()
