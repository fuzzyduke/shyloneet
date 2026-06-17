import os
import sys
import re
import fitz

# Add backend to path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
from models import QuestionPaper, Question, AnswerEvaluation

def extract_answers_from_pdf():
    doc = fitz.open('papers/neet-2025-045/source.pdf')
    page26 = doc[25].get_text('text')
    lines = [l.strip() for l in page26.split('\n') if l.strip()]
    
    answers = {}
    
    # Simple state machine to parse "1." followed by "(2)"
    q_num = None
    for line in lines:
        q_match = re.match(r'^(\d+)\.$', line)
        ans_match = re.match(r'^\(([\d,]+)\)$', line)
        
        if q_match:
            q_num = int(q_match.group(1))
        elif ans_match and q_num is not None:
            raw_ans = ans_match.group(1)
            # Map to canonical
            if raw_ans == '1': mapped = 'A'
            elif raw_ans == '2': mapped = 'B'
            elif raw_ans == '3': mapped = 'C'
            elif raw_ans == '4': mapped = 'D'
            else: mapped = 'bonus' # e.g. "1,2"
            
            answers[q_num] = mapped
            q_num = None
            
    return answers

def main():
    answers = extract_answers_from_pdf()
    print(f"Extracted {len(answers)} answers from PDF.")
    
    db = SessionLocal()
    # Find the target paper
    paper = db.query(QuestionPaper).filter(QuestionPaper.year == 2025).first()
    if not paper:
        print("Could not find the 2025 paper in the DB!")
        return
        
    print(f"Target Paper ID: {paper.id}")
    
    questions = db.query(Question).filter(Question.paper_id == paper.id).all()
    print(f"Found {len(questions)} questions for this paper in DB.")
    
    inserts = 0
    for q in questions:
        q_num = q.question_number
        if q_num in answers:
            # We want to insert AnswerEvaluation
            # Check if there is already an official paper answer
            existing = db.query(AnswerEvaluation).filter(
                AnswerEvaluation.question_id == q.id,
                AnswerEvaluation.evaluator_type == 'paper'
            ).first()
            
            # Deactivate older answers if they exist so this one is active
            db.query(AnswerEvaluation).filter(AnswerEvaluation.question_id == q.id).update({"is_active": False})
            
            new_eval = AnswerEvaluation(
                question_id=q.id,
                evaluator_type='paper',
                evaluator_name='paper',
                evaluator_model_provider='Paper',
                source_location='page 26',
                correct_option=answers[q_num],
                status='active',
                is_active=True,
                confidence=1.0
            )
            db.add(new_eval)
            inserts += 1
            
            # Also update the main Question table for quick access
            q.answer = answers[q_num]
            q.answer_status = 'official_from_paper'
            q.solution_source = 'official_answer_key'
            
    db.commit()
    print(f"Inserted/updated {inserts} answers into DB.")

if __name__ == '__main__':
    main()
