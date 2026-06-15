import os
import json
import numpy as np
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question, ChapterChunk, Chapter, QuestionChapterMap

def get_chapter_embeddings(db: Session, exam_program_id="NEET"):
    chunks = db.query(ChapterChunk).join(Chapter).filter(
        Chapter.exam_program_id == exam_program_id,
        Chapter.subject == "Physics",
        ChapterChunk.embedding != None,
        ChapterChunk.embedding != "[]"
    ).all()
    
    chunk_data = []
    for c in chunks:
        try:
            emb = json.loads(c.embedding)
            chunk_data.append({
                "chunk_id": c.id,
                "chapter_id": c.chapter_id,
                "chapter_name": c.chapter.chapter_name,
                "text": c.chunk_text,
                "embedding": np.array(emb)
            })
        except:
            continue
    return chunk_data

def run_pipeline():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("sentence-transformers not found.")
        return
        
    model = SentenceTransformer('all-MiniLM-L6-v2')
    db = SessionLocal()
    
    print("Loading chapter chunk embeddings...")
    chunk_data = get_chapter_embeddings(db, "NEET")
    if not chunk_data:
        print("No embeddings found!")
        return
        
    clean_questions = db.query(Question).filter(
        Question.subject == "Physics",
        Question.exam_program_id == "NEET",
        Question.needs_manual_review == False,
        ~Question.id.in_(db.query(QuestionChapterMap.question_id))
    ).order_by(Question.question_number).all()
    
    print(f"Found {len(clean_questions)} unmapped clean NEET Physics questions.")
    if not clean_questions:
        db.close()
        return
        
    for q in clean_questions:
        q_text = q.question_text or ""
        options_str = f"A: {q.option_a}\nB: {q.option_b}\nC: {q.option_c}\nD: {q.option_d}"
        full_text = q_text + " " + options_str
        q_emb = model.encode(full_text, convert_to_numpy=True)
        
        chapter_scores = {}
        for c in chunk_data:
            sim = np.dot(q_emb, c["embedding"]) / (np.linalg.norm(q_emb) * np.linalg.norm(c["embedding"]))
            ch_id = c["chapter_id"]
            if ch_id not in chapter_scores or sim > chapter_scores[ch_id]["score"]:
                chapter_scores[ch_id] = {
                    "chapter_id": ch_id,
                    "chapter_name": c["chapter_name"],
                    "score": float(sim)
                }
                
        top_candidates = sorted(chapter_scores.values(), key=lambda x: x["score"], reverse=True)[:5]
        if not top_candidates:
            continue
            
        primary_id = top_candidates[0]["chapter_id"]
        primary_name = top_candidates[0]["chapter_name"]
        
        # Incompatibility Check: Subject and Exam Program
        ch_obj = db.query(Chapter).filter(Chapter.id == primary_id).first()
        if ch_obj and ch_obj.exam_program_id != q.exam_program_id:
            continue
            
        mapping = QuestionChapterMap(
            question_id=q.id,
            chapter_id=primary_id,
            is_primary=True,
            confidence=0.5, # Manual review needed due to fallback
            mapping_method="embedding_fallback",
            reason=f"LLM mapping failed. Fallback to embedding top match (Sim: {top_candidates[0]['score']:.2f})",
            needs_manual_review=True,
            approved_by_admin=False
        )
        db.add(mapping)
        print(f"Mapped Q{q.question_number} -> {primary_name} (Fallback)")
                
    db.commit()
    db.close()
    print("Done!")

if __name__ == "__main__":
    run_pipeline()
