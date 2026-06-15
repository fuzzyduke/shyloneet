import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question, Chapter, QuestionChapterMap

db = SessionLocal()

mappings = db.query(QuestionChapterMap).join(Question).filter(
    Question.exam_program_id == "NEET"
).all()

primary_mappings = [m for m in mappings if m.is_primary]

auto_approved = []
review_recommended = []
mandatory_review = []

for m in primary_mappings:
    q_num = m.question.question_number
    if m.approved_by_admin:
        auto_approved.append(q_num)
    elif m.needs_manual_review and m.confidence >= 0.70:
        review_recommended.append(q_num)
    else:
        mandatory_review.append(q_num)

print(json.dumps({
    "auto_approved": sorted(list(set(auto_approved))),
    "review_recommended": sorted(list(set(review_recommended))),
    "mandatory_review": sorted(list(set(mandatory_review)))
}))
