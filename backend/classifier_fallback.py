import os
import json
import time
import requests
import numpy as np
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question, ChapterChunk, Chapter, QuestionChapterMap
import concurrent.futures

AGENT_ZERO_API_KEY = "sk-a0-jvjZaEPiDlpBJcj4Zk41eKS5owfpeVpzy0"
MODEL_NAME = "qwen-3-7-plus"

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

def call_strong_llm(question_text: str, options_str: str, top_candidates: list):
    headers = {
        "Authorization": f"Bearer {AGENT_ZERO_API_KEY}",
        "Accept": "application/json"
    }
    
    candidates_info = ""
    for idx, cand in enumerate(top_candidates):
        candidates_info += f"\nCandidate {idx+1}:\nChapter ID: {cand['chapter_id']}\nChapter Name: {cand['chapter_name']}\nSummary: {cand['text'][:500]}...\n"

    system_prompt = """You are an expert physics teacher mapping NEET multiple-choice questions to NCERT Physics chapters.
Given the question and the top candidate chapters, select the primary chapter that this question belongs to.
Return strictly JSON format:
{
  "primary_chapter_id": "string",
  "primary_chapter_name": "string",
  "secondary_chapters": [],
  "confidence": float,
  "reason": "string",
  "needs_manual_review": boolean
}
"""

    user_prompt = f"Question:\n{question_text}\n\nOptions:\n{options_str}\n\nCandidate Chapters:\n{candidates_info}\n\nClassify the question now. Return strictly JSON."

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://llm.agent-zero.ai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            return None
            
        content = response.json()["choices"][0]["message"]["content"]
        
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            extracted = content[start:end+1]
            return json.loads(extracted)
        return json.loads(content)
    except Exception as e:
        return None

def process_single_question(q_id, q_text, options_str, q_number, q_exam_program_id, chunk_data, q_emb):
    chapter_scores = {}
    for c in chunk_data:
        sim = np.dot(q_emb, c["embedding"]) / (np.linalg.norm(q_emb) * np.linalg.norm(c["embedding"]))
        ch_id = c["chapter_id"]
        if ch_id not in chapter_scores or sim > chapter_scores[ch_id]["score"]:
            chapter_scores[ch_id] = {
                "chapter_id": ch_id,
                "chapter_name": c["chapter_name"],
                "score": float(sim),
                "text": c["text"]
            }
            
    top_candidates = sorted(chapter_scores.values(), key=lambda x: x["score"], reverse=True)[:5]
    if not top_candidates:
        return {"error": f"No candidates found for Q{q_number}"}
        
    llm_result = call_strong_llm(q_text, options_str, top_candidates)
    
    # Fallback to embedding top match if LLM fails
    if not llm_result:
        llm_result = {
            "primary_chapter_id": top_candidates[0]["chapter_id"],
            "primary_chapter_name": top_candidates[0]["chapter_name"],
            "secondary_chapters": [],
            "confidence": 0.5,
            "reason": f"LLM parsing failed. Fallback to top embedding match (Similarity: {top_candidates[0]['score']:.2f})",
            "needs_manual_review": True
        }
        
    return {
        "q_id": q_id,
        "q_number": q_number,
        "q_exam_program_id": q_exam_program_id,
        "top_candidates": top_candidates,
        "llm_result": llm_result
    }

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
        
    tasks = []
    for q in clean_questions:
        q_text = q.question_text or ""
        options_str = f"A: {q.option_a}\nB: {q.option_b}\nC: {q.option_c}\nD: {q.option_d}"
        full_text = q_text + " " + options_str
        q_emb = model.encode(full_text, convert_to_numpy=True)
        tasks.append((q.id, q_text, options_str, q.question_number, q.exam_program_id, chunk_data, q_emb))
        
    print(f"Computed local embeddings. Dispatching to API with 10 threads...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_question, *t): t for t in tasks}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            if "error" in res:
                print(res["error"])
            else:
                q_num = res["q_number"]
                llm_res = res["llm_result"]
                print(f"Mapped Q{q_num} -> {llm_res.get('primary_chapter_name')} | Conf: {llm_res.get('confidence', 0.0):.2f}")
    
    print("Saving mappings to DB...")
    for res in results:
        if "error" in res:
            continue
            
        q_id = res["q_id"]
        q_exam_program_id = res["q_exam_program_id"]
        llm_result = res["llm_result"]
        top_candidates = res["top_candidates"]
        
        primary_id = llm_result.get("primary_chapter_id")
        confidence = llm_result.get("confidence", 0.0)
        
        embedding_llm_disagreement = False
        if top_candidates and primary_id != top_candidates[0]["chapter_id"]:
            embedding_llm_disagreement = True
            
        needs_review = llm_result.get("needs_manual_review", False)
        if confidence < 0.70 or embedding_llm_disagreement:
            needs_review = True
        elif confidence < 0.85:
            needs_review = True
            
        if primary_id:
            ch_obj = db.query(Chapter).filter(Chapter.id == primary_id).first()
            if ch_obj and ch_obj.exam_program_id != q_exam_program_id:
                print(f"Boundary violation on Q{res['q_number']}! Rejecting.")
                continue
                
            mapping = QuestionChapterMap(
                question_id=q_id,
                chapter_id=primary_id,
                is_primary=True,
                confidence=confidence,
                mapping_method="embedding_plus_llm",
                reason=llm_result.get("reason", ""),
                needs_manual_review=needs_review,
                approved_by_admin=(confidence >= 0.85 and not embedding_llm_disagreement)
            )
            db.add(mapping)
                
    db.commit()
    db.close()
    print("Done!")

if __name__ == "__main__":
    run_pipeline()
