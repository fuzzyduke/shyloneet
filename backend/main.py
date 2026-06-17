from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import engine, Base, get_db
import models
from fastapi.middleware.cors import CORSMiddleware
import os
from passlib.context import CryptContext
from datetime import datetime
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = "mvp-secret-key-shiloh"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

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

# Mount parent directory to serve frontend HTML files
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app.mount("/static", StaticFiles(directory=parent_dir), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to NEET Vault AI API"}

@app.get("/admin")
def redirect_admin():
    return RedirectResponse(url="/static/admin_review.html")

# Seed users
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    if not db.query(models.User).filter_by(username="admin").first():
        db.add(models.User(username="admin", hashed_password=get_password_hash("admin"), role="admin"))
    if not db.query(models.User).filter_by(username="shiloh").first():
        # TODO: replace with secure credentials before production
        db.add(models.User(username="shiloh", hashed_password=get_password_hash("shiloh"), role="sub_admin"))
    db.commit()

# Auth APIs
@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/api/auth/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

class UpdatePaperSolutionStatusRequest(BaseModel):
    solution_status: str
    scoring_enabled: bool
    scoring_source: str
    solution_extraction_method: str

class UpdateQuestionAnswerRequest(BaseModel):
    correct_option: str
    solution_text: Optional[str] = None
    answer_status: str
    solution_source: str
    solution_needs_review: bool
    scoring_eligible: bool

@app.get("/api/papers")
def get_papers(db: Session = Depends(get_db)):
    papers = db.query(models.QuestionPaper).all()
    return [
        {
            "id": p.id,
            "exam_type": p.exam_type,
            "year": p.year,
            "paper_code": p.paper_code,
            "solution_status": p.solution_status,
            "scoring_enabled": p.scoring_enabled,
            "scoring_source": p.scoring_source
        }
        for p in papers
    ]

@app.get("/api/papers/{paper_id}/solution-status")
def get_paper_solution_status(paper_id: str, db: Session = Depends(get_db)):
    p = db.query(models.QuestionPaper).filter(models.QuestionPaper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    qs = db.query(models.Question).filter(models.Question.paper_id == paper_id).all()
    
    return {
        "solution_status": p.solution_status,
        "scoring_enabled": p.scoring_enabled,
        "scoring_source": p.scoring_source,
        "counts": {
            "total": len(qs),
            "official_from_paper": sum(1 for q in qs if q.answer_status == "official_from_paper"),
            "ai_mapped": sum(1 for q in qs if q.answer_status == "ai_mapped"),
            "manual_admin": sum(1 for q in qs if q.answer_status == "manual_admin"),
            "unavailable": sum(1 for q in qs if q.answer_status == "unavailable"),
            "needs_review": sum(1 for q in qs if q.solution_needs_review)
        }
    }

@app.post("/api/admin/papers/{paper_id}/update-solution-status")
def update_paper_solution_status(paper_id: str, req: UpdatePaperSolutionStatusRequest, db: Session = Depends(get_db)):
    p = db.query(models.QuestionPaper).filter(models.QuestionPaper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    p.solution_status = req.solution_status
    p.scoring_enabled = req.scoring_enabled
    p.scoring_source = req.scoring_source
    p.solution_extraction_method = req.solution_extraction_method
    p.solution_last_verified_at = datetime.utcnow()
    
    db.commit()
    return {"status": "success"}

@app.post("/api/admin/questions/{question_id}/update-answer")
def update_question_answer(question_id: str, req: UpdateQuestionAnswerRequest, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    q.answer = req.correct_option
    q.solution_text = req.solution_text
    q.answer_status = req.answer_status
    q.solution_source = req.solution_source
    q.solution_needs_review = req.solution_needs_review
    q.scoring_eligible = req.scoring_eligible
    
    db.commit()
    return {"status": "success"}

@app.get("/api/chapters")
def get_chapters(subject: str = None, source: str = None, class_level: int = None, exam_program_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Chapter)
    if subject:
        query = query.filter(models.Chapter.subject == subject)
    if source:
        query = query.filter(models.Chapter.source == source)
    if class_level:
        query = query.filter(models.Chapter.class_level == class_level)
    if exam_program_id:
        query = query.filter(models.Chapter.exam_program_id == exam_program_id)
    return query.all()

class TestGenerationRequest(BaseModel):
    subject: str
    chapter_ids: List[str]
    paper_id: Optional[str] = None
    question_count: int = 50
    role: Optional[str] = "student"

@app.post("/api/generate_test")
def generate_test(req: TestGenerationRequest, db: Session = Depends(get_db)):
    # Simple token check to see if user is sub_admin/admin (passed via header?)
    # Since we don't have request obj easily here without Depends(Request), let's just return answers always?
    # Wait, Phase 5 safety: student UI should NOT see answers if unscored.
    # To fix this, we'll accept an optional role in the request body for MVP, or just depend on get_current_user?
    # Actually, generate_test is public. We can just add an optional `role` field to TestGenerationRequest for MVP.
    # Base query for questions
    q_query = db.query(models.Question).join(models.QuestionChapterMap).filter(
        models.QuestionChapterMap.approved_by_admin == True,
        models.Question.subject == req.subject,
        models.Question.extraction_status == "success",
        models.Question.is_mock == False,
        models.QuestionChapterMap.is_primary == True
    )

    if req.chapter_ids:
        q_query = q_query.filter(models.QuestionChapterMap.chapter_id.in_(req.chapter_ids))
    if req.paper_id:
        q_query = q_query.filter(models.Question.paper_id == req.paper_id)

    # Fetch questions
    questions = q_query.limit(req.question_count).all()

    # Determine scoring mode
    scoring_mode = "scored"
    scoring_enabled = True
    disabled_controls = []
    solution_status = "mixed"

    # If all requested questions belong to a paper, we check the paper's scoring capability.
    # For MVP: "Only generate scored tests from scoring_eligible questions"
    # If any question is NOT scoring eligible, we force unscored mode for the entire test.
    if any(not q.scoring_eligible for q in questions) or not questions:
        scoring_mode = "unscored"
        scoring_enabled = False
        solution_status = "unavailable"
        disabled_controls = ["submit_for_score", "percentage_score", "rank_benchmark", "result_analytics", "wrong_answer_review", "performance_history_update"]

    paper_title = "Practice Paper"
    if req.paper_id:
        paper = db.query(models.QuestionPaper).filter(models.QuestionPaper.id == req.paper_id).first()
        if paper:
            # {year} {exam_program_id} {subject or 'Paper'} - Code {paper_code}
            if hasattr(paper, 'title') and paper.title:
                paper_title = paper.title
            elif paper.year and paper.exam_program_id:
                subject_text = paper.subject if getattr(paper, 'subject', None) else 'Paper'
                code_text = f" - Code {paper.paper_code}" if paper.paper_code else ""
                paper_title = f"{paper.year} {paper.exam_program_id} {subject_text}{code_text}"
            elif paper.source_file:
                paper_title = paper.source_file

    return {
        "scoring_mode": scoring_mode,
        "scoring_enabled": scoring_enabled,
        "solution_status": solution_status,
        "disabled_controls": disabled_controls,
        "paper_title": paper_title,
        "questions": [
            {
                "id": q.id,
                "text": q.question_text,
                "options": {
                    "A": q.option_a,
                    "B": q.option_b,
                    "C": q.option_c,
                    "D": q.option_d,
                },
                "answer": q.answer if scoring_enabled or req.role in ["admin", "sub_admin"] else None,
                "answer_status": q.answer_status,
                "solution": q.solution_text if scoring_enabled or req.role in ["admin", "sub_admin"] else None,
                "images": [asset.image_url for asset in q.assets]
            }
            for q in questions
        ]
    }

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
@app.get("/api/admin/review-summary")
def get_review_summary(paper_id: str = None, db: Session = Depends(get_db)):
    base_q = db.query(models.Question).filter(models.Question.is_mock == False)
    if paper_id:
        base_q = base_q.filter(models.Question.paper_id == paper_id)
    total_unique = base_q.count()
    
    base_m = db.query(models.QuestionChapterMap).join(models.Question).filter(models.Question.is_mock == False)
    if paper_id:
        base_m = base_m.filter(models.Question.paper_id == paper_id)
        
    auto_approved = base_m.filter(models.QuestionChapterMap.approved_by_admin == True, models.QuestionChapterMap.is_primary == True).count()
    mandatory_review = base_m.filter(models.QuestionChapterMap.needs_manual_review == True, models.QuestionChapterMap.confidence < 0.7, models.QuestionChapterMap.is_primary == True).count()
    review_recommended = base_m.filter(models.QuestionChapterMap.needs_manual_review == True, models.QuestionChapterMap.confidence >= 0.7, models.QuestionChapterMap.is_primary == True).count()
    
    # Unmapped: Questions with no mapping
    mapped_q_ids = base_m.with_entities(models.QuestionChapterMap.question_id).all()
    mapped_q_ids = [m[0] for m in mapped_q_ids]
    unmapped = base_q.filter(
        models.Question.id.not_in(mapped_q_ids)
    ).count()
    
    failed_extractions = db.query(models.FailedExtraction).count()
    
    return {
        "total_unique": total_unique,
        "auto_approved": auto_approved,
        "mandatory_review": mandatory_review,
        "review_recommended": review_recommended,
        "unmapped": unmapped,
        "failed_extractions": failed_extractions
    }

@app.get("/api/admin/review-queue")
def get_review_queue(paper_id: str = None, db: Session = Depends(get_db)):
    def serialize_q(q):
        assets = [{"type": a.asset_type, "url": a.image_url, "caption": a.caption} for a in q.assets]
        return {
            "id": q.id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
            "answer": q.answer,
            "solution": q.solution_text,
            "source_pdf": q.source_pdf,
            "page_number": q.page_number,
            "extraction_confidence": q.extraction_confidence,
            "extraction_method": q.extraction_method,
            "extraction_model": q.extraction_model,
            "incompatibility_flags": q.incompatibility_flags,
            "assets": assets
        }

    m_query = db.query(models.QuestionChapterMap).join(models.Question).filter(models.Question.is_mock == False)
    if paper_id:
        m_query = m_query.filter(models.Question.paper_id == paper_id)
    mappings = m_query.all()
    
    auto_approved = []
    mandatory_review = []
    review_recommended = []
    
    for m in mappings:
        if not m.is_primary:
            continue
        q_data = serialize_q(m.question)
        m_data = {
            "mapping_id": m.id,
            "chapter_id": m.chapter_id,
            "chapter_name": m.chapter.chapter_name if m.chapter else "Unknown",
            "confidence": m.confidence,
            "mapping_method": m.mapping_method,
            "reason": m.reason,
            "needs_manual_review": m.needs_manual_review,
            "approved_by_admin": m.approved_by_admin
        }
        
        # secondary chapters
        secondaries = db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id == m.question_id, models.QuestionChapterMap.is_primary == False).all()
        m_data["secondary_chapters"] = [{"chapter_id": sec.chapter_id, "chapter_name": sec.chapter.chapter_name if sec.chapter else "Unknown"} for sec in secondaries]
        
        item = {"question": q_data, "mapping": m_data}
        
        if m.approved_by_admin:
            auto_approved.append(item)
        elif m.needs_manual_review and m.confidence < 0.7:
            mandatory_review.append(item)
        elif m.needs_manual_review:
            review_recommended.append(item)
        else:
            auto_approved.append(item)
            
    # Unmapped
    mapped_q_ids = [m.question_id for m in mappings]
    q_query = db.query(models.Question).filter(
        models.Question.is_mock == False,
        models.Question.id.not_in(mapped_q_ids)
    )
    if paper_id:
        q_query = q_query.filter(models.Question.paper_id == paper_id)
    unmapped_qs = q_query.all()
    unmapped = [{"question": serialize_q(q), "mapping": None} for q in unmapped_qs]
    
    # Failed Extractions
    failed_exts = db.query(models.FailedExtraction).all()
    failed = [{
        "id": f.id,
        "page_number": f.page_number,
        "column_name": f.column_name,
        "image_url": f.image_url,
        "raw_response": f.raw_response,
        "parse_error": f.parse_error,
        "review_status": f.review_status,
        "flags": {
            "schema_incompatible": f.schema_incompatible,
            "extraction_incomplete": f.extraction_incomplete
        }
    } for f in failed_exts]
    
    return {
        "auto_approved": auto_approved,
        "mandatory_review": mandatory_review,
        "review_recommended": review_recommended,
        "unmapped": unmapped,
        "failed_extractions": failed
    }

@app.get("/api/admin/questions/{question_id}")
def get_question_detail(question_id: str, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    assets = [{"type": a.asset_type, "url": a.image_url, "caption": a.caption} for a in q.assets]
    
    # fetch mappings
    mappings = db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id == question_id).all()
    primary = next((m for m in mappings if m.is_primary), None)
    secondaries = [m for m in mappings if not m.is_primary]
    
    current_mapping = None
    if primary:
        current_mapping = {
            "primary_chapter_id": primary.chapter_id,
            "primary_chapter_name": primary.chapter.chapter_name if primary.chapter else "Unknown",
            "confidence": primary.confidence,
            "mapping_method": primary.mapping_method,
            "reason": primary.reason,
            "needs_manual_review": primary.needs_manual_review,
            "approved_by_admin": primary.approved_by_admin,
            "secondary_chapters": [{"id": s.chapter_id, "name": s.chapter.chapter_name if s.chapter else "Unknown"} for s in secondaries]
        }
        
    return {
        "id": q.id,
        "question_number": q.question_number,
        "question_text": q.question_text,
        "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
        "answer": q.answer,
        "solution": q.solution_text,
        "source_pdf": q.source_pdf,
        "page_number": q.page_number,
        "extraction_confidence": q.extraction_confidence,
        "extraction_method": q.extraction_method,
        "extraction_model": q.extraction_model,
        "incompatibility_flags": q.incompatibility_flags,
        "extraction_status": q.extraction_status,
        "assets": assets,
        "current_mapping": current_mapping
    }

from datetime import datetime

@app.post("/api/admin/questions/{question_id}/approve-mapping")
def approve_question_mapping(question_id: str, db: Session = Depends(get_db)):
    mappings = db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id == question_id).all()
    if not mappings:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    for mapping in mappings:
        mapping.approved_by_admin = True
        mapping.needs_manual_review = False
        mapping.approved_at = datetime.utcnow()
    
    db.commit()
    return {"status": "approved"}

class UpdateMappingRequest(BaseModel):
    primary_chapter_id: str
    secondary_chapter_ids: List[str] = []

@app.post("/api/admin/questions/{question_id}/update-mapping")
def update_question_mapping(question_id: str, req: UpdateMappingRequest, db: Session = Depends(get_db)):
    # Remove old mappings
    db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id == question_id).delete()
    
    # Create new primary
    new_primary = models.QuestionChapterMap(
        question_id=question_id,
        chapter_id=req.primary_chapter_id,
        is_primary=True,
        confidence=1.0,
        mapping_method="manual_admin",
        needs_manual_review=False,
        approved_by_admin=True,
        approved_at=datetime.utcnow()
    )
    db.add(new_primary)
    
    if req.secondary_chapter_ids:
        for sid in req.secondary_chapter_ids:
            sec = models.QuestionChapterMap(
                question_id=question_id,
                chapter_id=sid,
                is_primary=False,
                confidence=1.0,
                mapping_method="manual_admin",
                needs_manual_review=False,
                approved_by_admin=True,
                approved_at=datetime.utcnow()
            )
            db.add(sec)
        
    db.commit()
    return {"status": "updated"}

@app.post("/api/admin/questions/{question_id}/mark-bad-extraction")
def mark_bad_extraction(question_id: str, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    q.extraction_status = "bad_extraction"
    
    # Remove mappings so it doesn't appear mapped
    db.query(models.QuestionChapterMap).filter(models.QuestionChapterMap.question_id == question_id).delete()
    
    db.commit()
    return {"status": "marked_bad"}
class SubmitAnswerCorrectionRequest(BaseModel):
    correct_option: str
    note: Optional[str] = None
    source_context: str

class ReplaceWithAdminAnswerRequest(BaseModel):
    correct_option: str
    note: Optional[str] = None

class AIProcessingJobRequest(BaseModel):
    job_type: str
    requested_model: str

@app.get("/api/admin/papers/{paper_id}/ai-processing")
def get_paper_ai_processing(paper_id: str, db: Session = Depends(get_db)):
    jobs = db.query(models.PaperAIProcessingJob).filter(models.PaperAIProcessingJob.paper_id == paper_id).order_by(models.PaperAIProcessingJob.created_at.desc()).all()
    return jobs

@app.post("/api/admin/papers/{paper_id}/ai-processing-jobs")
def create_ai_processing_job(paper_id: str, req: AIProcessingJobRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    job = models.PaperAIProcessingJob(
        paper_id=paper_id,
        job_type=req.job_type,
        requested_model=req.requested_model,
        requested_by=current_user.username
    )
    db.add(job)
    db.commit()
    return {"status": "success", "job_id": job.id}

@app.get("/api/questions/{question_id}/answer-evaluations")
def get_answer_evaluations(question_id: str, db: Session = Depends(get_db)):
    evals = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.question_id == question_id).order_by(models.AnswerEvaluation.created_at.desc()).all()
    return evals

@app.get("/api/questions/{question_id}/chapter-mapping-evaluations")
def get_chapter_mapping_evaluations(question_id: str, db: Session = Depends(get_db)):
    evals = db.query(models.ChapterMappingEvaluation).filter(models.ChapterMappingEvaluation.question_id == question_id).order_by(models.ChapterMappingEvaluation.created_at.desc()).all()
    return evals

@app.post("/api/questions/{question_id}/submit-answer-correction")
def submit_answer_correction(question_id: str, req: SubmitAnswerCorrectionRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Mark old active evaluation as superseded
    old_active = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.question_id == question_id, models.AnswerEvaluation.is_active == True).first()
    if old_active:
        old_active.is_active = False
        old_active.status = "superseded"
        
    # Create new evaluation
    new_eval = models.AnswerEvaluation(
        paper_id=q.paper_id,
        question_id=question_id,
        evaluator_type="sub_admin" if current_user.role == "sub_admin" else "admin",
        evaluator_name=current_user.username,
        correct_option=req.correct_option,
        reasoning=req.note,
        status="active" if current_user.role == "admin" else "proposed", # UI says pending_admin_review but status can be active with needs_review
        is_active=True,
        created_by=current_user.username
    )
    
    if current_user.role == "sub_admin":
        new_eval.status = "needs_review"
    
    db.add(new_eval)
    
    # Update question cached state
    q.answer = req.correct_option
    q.answer_status = "manual_admin" if current_user.role == "admin" else "needs_review"
    q.solution_needs_review = current_user.role == "sub_admin"
    
    db.commit()
    return {"status": "success", "evaluation_id": new_eval.id}

@app.get("/api/admin/subadmin-corrections")
def get_subadmin_corrections(paper_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models.AnswerEvaluation).join(models.Question).filter(models.AnswerEvaluation.evaluator_type == "sub_admin", models.AnswerEvaluation.status == "needs_review")
    if paper_id:
        query = query.filter(models.Question.paper_id == paper_id)
    evals = query.all()
    return [{
        "evaluation_id": e.id,
        "question_id": e.question_id,
        "question_number": e.question.question_number,
        "evaluator_name": e.evaluator_name,
        "proposed_option": e.correct_option,
        "reasoning": e.reasoning,
        "created_at": e.created_at
    } for e in evals]

@app.post("/api/admin/answer-evaluations/{evaluation_id}/accept")
def accept_evaluation(evaluation_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    e = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.id == evaluation_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    e.status = "accepted"
    e.reviewed_by = current_user.username
    e.reviewed_at = datetime.utcnow()
    
    q = db.query(models.Question).filter(models.Question.id == e.question_id).first()
    q.solution_needs_review = False
    q.answer_status = "manual_admin"
    db.commit()
    return {"status": "success"}

@app.post("/api/admin/answer-evaluations/{evaluation_id}/revert")
def revert_evaluation(evaluation_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    e = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.id == evaluation_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Evaluation not found")
        
    e.status = "reverted"
    e.is_active = False
    e.reviewed_by = current_user.username
    e.reviewed_at = datetime.utcnow()
    
    # Restore previous active if any
    prev_eval = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.question_id == e.question_id, models.AnswerEvaluation.id != e.id, models.AnswerEvaluation.status == "superseded").order_by(models.AnswerEvaluation.created_at.desc()).first()
    q = db.query(models.Question).filter(models.Question.id == e.question_id).first()
    
    if prev_eval:
        prev_eval.is_active = True
        prev_eval.status = "active"
        q.answer = prev_eval.correct_option
        q.answer_status = prev_eval.evaluator_type
    else:
        q.answer = None
        q.answer_status = "unavailable"
        
    q.solution_needs_review = False
    db.commit()
    return {"status": "success"}

@app.post("/api/admin/answer-evaluations/{evaluation_id}/replace-with-admin-answer")
def replace_evaluation(evaluation_id: str, req: ReplaceWithAdminAnswerRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    e = db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.id == evaluation_id).first()
    if e:
        e.is_active = False
        e.status = "superseded"
        e.reviewed_by = current_user.username
        e.reviewed_at = datetime.utcnow()
        
    new_eval = models.AnswerEvaluation(
        paper_id=e.paper_id if e else None,
        question_id=e.question_id if e else None,
        evaluator_type="admin",
        evaluator_name=current_user.username,
        correct_option=req.correct_option,
        reasoning=req.note,
        status="active",
        is_active=True,
        created_by=current_user.username
    )
    db.add(new_eval)
    
    if e:
        q = db.query(models.Question).filter(models.Question.id == e.question_id).first()
        q.answer = req.correct_option
        q.answer_status = "manual_admin"
        q.solution_needs_review = False
    
    db.commit()
    return {"status": "success"}
