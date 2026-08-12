import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import models

db = SessionLocal()

bad_ids = ['5c63dc27-82b7-42f1-9bce-74c389fbb62e', 'dd54e80e-4267-4a9b-bc8f-717712903fd3']

for bad_id in bad_ids:
    print(f"Deleting paper {bad_id}")
    # Delete related records
    q_ids = [q.id for q in db.query(models.Question).filter(models.Question.paper_id == bad_id).all()]
    if q_ids:
        db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(models.ChapterMappingEvaluation).filter(models.ChapterMappingEvaluation.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(models.QuestionAsset).filter(models.QuestionAsset.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(models.Question).filter(models.Question.paper_id == bad_id).delete(synchronize_session=False)
    
    db.query(models.FailedExtraction).filter(models.FailedExtraction.paper_id == bad_id).delete(synchronize_session=False)
    db.query(models.PaperAIProcessingJob).filter(models.PaperAIProcessingJob.paper_id == bad_id).delete(synchronize_session=False)
    
    db.query(models.QuestionPaper).filter(models.QuestionPaper.id == bad_id).delete(synchronize_session=False)

db.commit()
print("Done clearing duplicate/incomplete papers.")
