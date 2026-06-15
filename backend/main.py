from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import engine, Base, get_db
import models
from fastapi.middleware.cors import CORSMiddleware
import os

# Create tables if not exists
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NEET Vault AI Pipeline")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to NEET Vault AI API"}

@app.get("/api/chapters")
def get_chapters(subject: str = None, source: str = None, class_level: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Chapter)
    if subject:
        query = query.filter(models.Chapter.subject == subject)
    if source:
        query = query.filter(models.Chapter.source == source)
    if class_level:
        query = query.filter(models.Chapter.class_level == class_level)
    return query.all()

class TestGenerationRequest(BaseModel):
    subject: str
    chapter_ids: List[str]
    question_count: int = 50

@app.post("/api/generate_test")
def generate_test(req: TestGenerationRequest, db: Session = Depends(get_db)):
    # Fetch questions mapped to requested chapters that are approved
    questions = db.query(models.Question).join(models.QuestionChapterMap).filter(
        models.QuestionChapterMap.chapter_id.in_(req.chapter_ids),
        models.QuestionChapterMap.approved_by_admin == True,
        models.Question.subject == req.subject
    ).limit(req.question_count).all()
    
    return [
        {
            "id": q.id,
            "text": q.question_text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
            "answer": q.answer,
            "solution": q.solution_text,
            "images": [asset.image_url for asset in q.assets]
        }
        for q in questions
    ]

class SuggestionRequest(BaseModel):
    question_id: str
    suggested_chapter_id: str
    reason: str = ""

@app.post("/api/suggestions")
def submit_suggestion(req: SuggestionRequest, db: Session = Depends(get_db)):
    suggestion = models.QuestionChapterSuggestion(
        question_id=req.question_id,
        user_id="anonymous",
        suggested_chapter_id=req.suggested_chapter_id,
        reason_optional=req.reason
    )
    db.add(suggestion)
    db.commit()
    return {"status": "success", "message": "Suggestion submitted for review."}

@app.post("/admin/upload_paper")
async def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Placeholder for Phase 2 paper upload
    return {"filename": file.filename, "status": "uploaded", "message": "Phase 2 Question Extraction not yet implemented."}

# Admin Review Endpoints
@app.get("/admin/questions/review")
def get_questions_for_review(db: Session = Depends(get_db)):
    # Fetch questions mapping that need manual review
    mappings = db.query(models.QuestionChapterMap).filter(
        models.QuestionChapterMap.needs_manual_review == True,
        models.QuestionChapterMap.approved_by_admin == False
    ).all()
    
    results = []
    for m in mappings:
        q = m.question
        results.append({
            "mapping_id": m.id,
            "question_id": q.id,
            "question_text": q.question_text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
            "suggested_chapter": m.chapter.chapter_name if m.chapter else "Unknown",
            "confidence": m.confidence,
            "reason": m.reason,
            "source_pdf": q.source_pdf,
            "page_number": q.page_number
        })
    return results

class ApprovalRequest(BaseModel):
    mapping_id: str
    primary_chapter_id: str
    secondary_chapter_ids: List[str] = []
    is_bad_extraction: bool = False
    is_duplicate: bool = False

@app.post("/admin/questions/approve")
def approve_question_mapping(req: ApprovalRequest, db: Session = Depends(get_db)):
    mapping = db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.id == req.mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
        
    if req.is_bad_extraction or req.is_duplicate:
        # Mark as rejected/bad
        mapping.needs_manual_review = False
        mapping.approved_by_admin = False
        db.commit()
        return {"status": "rejected"}
        
    # Update mapping
    mapping.chapter_id = req.primary_chapter_id
    mapping.approved_by_admin = True
    mapping.needs_manual_review = False
    
    # Normally we'd handle secondary chapters here by adding new QuestionChapterMap rows
    
    db.commit()
    return {"status": "approved"}
