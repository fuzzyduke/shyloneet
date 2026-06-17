from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True, default=generate_uuid)
    subject = Column(String, index=True)
    source = Column(String)
    class_level = Column(Integer)
    chapter_number = Column(Integer)
    chapter_name = Column(String)
    file_name = Column(String)
    
    # Boundary Layer tracking
    exam_program_id = Column(String, index=True)
    source_type = Column(String, default="reference_book")
    source_name = Column(String)
    year = Column(Integer, nullable=True)
    paper_code = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    chunks = relationship("ChapterChunk", back_populates="chapter")
    assets = relationship("ChapterAsset", back_populates="chapter")

class ChapterChunk(Base):
    __tablename__ = "chapter_chunks"
    id = Column(String, primary_key=True, default=generate_uuid)
    chapter_id = Column(String, ForeignKey("chapters.id"))
    page_number = Column(Integer)
    chunk_text = Column(Text)
    chunk_type = Column(String) # text, formula, diagram_caption, example, exercise, table
    embedding = Column(Text) # Storing as JSON string for SQLite MVP. Use Vector type for Postgres.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    chapter = relationship("Chapter", back_populates="chunks")

class ChapterAsset(Base):
    __tablename__ = "chapter_assets"
    id = Column(String, primary_key=True, default=generate_uuid)
    chapter_id = Column(String, ForeignKey("chapters.id"))
    page_number = Column(Integer)
    asset_type = Column(String) # diagram, formula_image, table, graph
    image_url = Column(String)
    caption = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chapter = relationship("Chapter", back_populates="assets")

class QuestionPaper(Base):
    __tablename__ = "question_papers"
    id = Column(String, primary_key=True, default=generate_uuid)
    exam_type = Column(String)
    year = Column(Integer)
    paper_code = Column(String)
    source_file = Column(String)
    
    # Boundary Layer tracking
    exam_program_id = Column(String, index=True)
    source_type = Column(String, default="question_paper")
    source_name = Column(String)
    subject = Column(String, nullable=True)
    class_level = Column(Integer, nullable=True)

    upload_status = Column(String)
    processing_status = Column(String) # uploaded, extracting, extracted, failed, mock_only, ready_for_classification
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Solution Availability and Scoring Capability
    solution_status = Column(String, default="unavailable") # official_from_paper, ai_mapped, unavailable, mixed, needs_review
    scoring_enabled = Column(Boolean, default=False)
    scoring_source = Column(String, default="none") # official_answer_key, official_solutions, ai_answer_mapping, manual_admin, none, mixed
    solution_confidence = Column(Float, nullable=True)
    solution_review_required = Column(Boolean, default=False)
    solution_notes = Column(Text, nullable=True)
    answer_key_detected = Column(Boolean, default=False)
    answer_key_source_page = Column(Integer, nullable=True)
    solution_extraction_method = Column(String, default="none") # pdf_answer_key, pdf_solutions_section, ai_extracted, manual_admin, none
    solution_last_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    questions = relationship("Question", back_populates="paper")

class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=generate_uuid)
    paper_id = Column(String, ForeignKey("question_papers.id"))
    year = Column(Integer)
    exam_type = Column(String)
    paper_code = Column(String)
    
    # Boundary Layer tracking
    exam_program_id = Column(String, index=True)
    
    subject = Column(String, index=True)
    question_number = Column(Integer)
    question_text = Column(Text)
    option_a = Column(Text)
    option_b = Column(Text)
    option_c = Column(Text)
    option_d = Column(Text)
    answer = Column(String)
    solution_text = Column(Text)
    difficulty = Column(String)
    source_pdf = Column(String)
    page_number = Column(Integer)
    extraction_confidence = Column(Float)
    needs_manual_review = Column(Boolean, default=False)
    
    # Provenance Tracking
    source_type = Column(String, default="real_pdf_extraction") # real_pdf_extraction, mock, manual_seed
    is_mock = Column(Boolean, default=False)
    extraction_method = Column(String) # heuristic_pdf_text, vision_agentzero, vision_venice, vision_nvidia, vision_gemini, manual
    extraction_model = Column(String) # Actual model name used
    extraction_status = Column(String, default="success") # success, partial, failed, mock_validation_only, needs_review
    
    # Incompatibility Flags (JSON list of strings or string enum)
    incompatibility_flags = Column(String, nullable=True)
    
    # Solution Tracking
    answer_status = Column(String, default="unavailable") # official_from_paper, ai_mapped, manual_admin, unavailable, needs_review
    solution_source = Column(String, default="none") # official_answer_key, official_solution, ai_generated, manual_admin, none
    solution_confidence = Column(Float, nullable=True)
    solution_needs_review = Column(Boolean, default=False)
    scoring_eligible = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    paper = relationship("QuestionPaper", back_populates="questions")
    assets = relationship("QuestionAsset", back_populates="question")
    mappings = relationship("QuestionChapterMap", back_populates="question")
    suggestions = relationship("QuestionChapterSuggestion", back_populates="question")

class QuestionAsset(Base):
    __tablename__ = "question_assets"
    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey("questions.id"))
    asset_type = Column(String) # diagram, formula, table, graph, passage_image
    image_url = Column(String)
    caption = Column(Text)
    page_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("Question", back_populates="assets")

class QuestionChapterMap(Base):
    __tablename__ = "question_chapter_map"
    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey("questions.id"))
    chapter_id = Column(String, ForeignKey("chapters.id"))
    is_primary = Column(Boolean, default=True)
    confidence = Column(Float)
    mapping_method = Column(String) # embedding, llm, manual_admin, student_suggested, corrected_after_review
    reason = Column(Text)
    needs_manual_review = Column(Boolean, default=False)
    approved_by_admin = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    question = relationship("Question", back_populates="mappings")
    chapter = relationship("Chapter")

class QuestionChapterSuggestion(Base):
    __tablename__ = "question_chapter_suggestions"
    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey("questions.id"))
    user_id = Column(String) # Mock user ID for now
    current_chapter_id = Column(String)
    suggested_chapter_id = Column(String, ForeignKey("chapters.id"))
    suggested_secondary_chapter_ids = Column(Text) # Store as JSON string
    reason_optional = Column(Text)
    test_attempt_id = Column(String)
    status = Column(String, default="pending") # pending, accepted, rejected, duplicate, needs_more_review
    reviewed_by_admin = Column(Boolean, default=False)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("Question", back_populates="suggestions")
    suggested_chapter = relationship("Chapter")

class CurriculumBridge(Base):
    __tablename__ = "curriculum_bridges"
    id = Column(String, primary_key=True, default=generate_uuid)
    source_exam_program_id = Column(String, index=True)
    target_exam_program_id = Column(String, index=True)
    source_chapter_id = Column(String, ForeignKey("chapters.id"))
    target_chapter_id = Column(String, ForeignKey("chapters.id"))
    topic_name = Column(String)
    similarity_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FailedExtraction(Base):
    __tablename__ = "failed_extractions"
    id = Column(String, primary_key=True, default=generate_uuid)
    paper_id = Column(String, ForeignKey("question_papers.id"))
    page_number = Column(Integer)
    column_name = Column(String)
    image_url = Column(String)
    raw_response = Column(Text)
    parse_error = Column(Text)
    review_status = Column(String, default="pending") # pending, recovered, discarded
    
    # Flags
    response_format_incompatible = Column(Boolean, default=False)
    schema_incompatible = Column(Boolean, default=False)
    extraction_incomplete = Column(Boolean, default=False)
    instruction_contamination = Column(Boolean, default=False)
    missing_options = Column(Boolean, default=False)
    duplicate_question_number = Column(Boolean, default=False)
    missing_question_number = Column(Boolean, default=False)
    diagram_asset_missing = Column(Boolean, default=False)
    curriculum_boundary_violation = Column(Boolean, default=False)
    subject_boundary_violation = Column(Boolean, default=False)
    low_confidence_mapping = Column(Boolean, default=False)
    embedding_llm_disagreement = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # admin, sub_admin, student
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"
    id = Column(String, primary_key=True, default=generate_uuid)
    paper_id = Column(String, ForeignKey("question_papers.id"), index=True)
    question_id = Column(String, ForeignKey("questions.id"), index=True)
    evaluator_type = Column(String) # paper, ai_model, sub_admin, admin
    evaluator_name = Column(String) 
    evaluator_model_provider = Column(String, nullable=True)
    correct_option = Column(String, nullable=True)
    solution_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    source_location = Column(String, nullable=True)
    status = Column(String, default="proposed") # proposed, active, accepted, reverted, rejected, superseded, needs_review
    is_active = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)
    supersedes_evaluation_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    question = relationship("Question")

class ChapterMappingEvaluation(Base):
    __tablename__ = "chapter_mapping_evaluations"
    id = Column(String, primary_key=True, default=generate_uuid)
    paper_id = Column(String, ForeignKey("question_papers.id"), index=True)
    question_id = Column(String, ForeignKey("questions.id"), index=True)
    evaluator_type = Column(String)
    evaluator_name = Column(String)
    evaluator_model_provider = Column(String, nullable=True)
    primary_chapter_id = Column(String, nullable=True)
    secondary_chapter_ids = Column(Text, nullable=True) # JSON
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    evidence_snippets = Column(Text, nullable=True) # JSON
    status = Column(String, default="proposed")
    is_active = Column(Boolean, default=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)
    question = relationship("Question")
    metadata_json = Column(Text, nullable=True)

class PaperAIProcessingJob(Base):
    __tablename__ = "paper_ai_processing_jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    paper_id = Column(String, ForeignKey("question_papers.id"), index=True)
    job_type = Column(String) # answer_mapping, chapter_mapping, answer_and_chapter_mapping, re_evaluation
    requested_model = Column(String)
    requested_provider = Column(String, nullable=True)
    status = Column(String, default="queued") # queued, running, completed, failed, cancelled
    requested_by = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    result_summary_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
