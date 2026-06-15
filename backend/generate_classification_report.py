import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question, Chapter, QuestionChapterMap

def generate_report():
    db = SessionLocal()
    
    # 1. Total clean questions
    total_clean = db.query(Question).filter(
        Question.exam_program_id == "NEET",
        Question.extraction_status != "needs_review",
        Question.needs_manual_review == False
    ).count()
    
    mappings = db.query(QuestionChapterMap).join(Question).filter(
        Question.exam_program_id == "NEET"
    ).all()
    
    total_mapped = len(set([m.question_id for m in mappings]))
    
    primary_mappings = [m for m in mappings if m.is_primary]
    
    auto_approved = sum(1 for m in primary_mappings if m.approved_by_admin)
    review_recommended = sum(1 for m in primary_mappings if m.needs_manual_review and m.confidence >= 0.70)
    mandatory_review = sum(1 for m in primary_mappings if m.needs_manual_review and m.confidence < 0.70)
    
    # Secondary chapters
    secondary_mappings = [m for m in mappings if not m.is_primary]
    qs_with_sec = len(set([m.question_id for m in secondary_mappings]))
    
    # Embedding/LLM disagreements
    disagreements = 0
    questions = db.query(Question).filter(Question.id.in_([m.question_id for m in mappings])).all()
    for q in questions:
        if q.incompatibility_flags:
            try:
                flags = json.loads(q.incompatibility_flags)
                if "embedding_llm_disagreement" in flags:
                    disagreements += 1
            except:
                pass
                
    low_confidence = mandatory_review
    
    # Chapter Distribution
    distribution = {}
    for m in primary_mappings:
        ch_name = m.chapter.chapter_name if m.chapter else "Unknown"
        distribution[ch_name] = distribution.get(ch_name, 0) + 1
        
    dist_str = "\n".join([f"- **{k}**: {v} questions" for k, v in sorted(distribution.items(), key=lambda item: item[1], reverse=True)])
    
    # 10 Samples
    samples = primary_mappings[:10]
    samples_str = ""
    for idx, m in enumerate(samples):
        samples_str += f"### Sample {idx+1}: Q{m.question.question_number}\n"
        samples_str += f"**Question:** {m.question.question_text[:150]}...\n"
        ch_name = m.chapter.chapter_name if m.chapter else "Unknown/Hallucinated ID"
        samples_str += f"**Mapped Chapter:** {ch_name}\n"
        samples_str += f"**Confidence:** {m.confidence:.2f}\n"
        samples_str += f"**Reason:** {m.reason}\n"
        samples_str += f"**Status:** {'Auto-Approved' if m.approved_by_admin else 'Needs Review'}\n\n"
        
    report_content = f"""# Phase 3: Chapter Classification Report

## Classification Metrics
- **Total Clean Questions:** {total_clean}
- **Successfully Mapped:** {total_mapped}
- **Auto-Approved (Conf >= 0.85):** {auto_approved}
- **Review Recommended (0.70 - 0.84):** {review_recommended}
- **Mandatory Manual Review (Conf < 0.70):** {mandatory_review}

## Incompatibilities & Edge Cases
- **Questions with Secondary Chapters:** {qs_with_sec}
- **Embedding/LLM Disagreements:** {disagreements}
- **Low Confidence Mappings:** {low_confidence}

## Distribution by Chapter
{dist_str}

## Classification Samples
{samples_str}

## Model Usage Summary
- **Vector Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **LLM Validator:** Agent Zero API (`qwen-3-7-plus`)
- **Strategy:** Grounded Hybrid. Embedding searches the top 5 relevant NCERT chapters, and the LLM makes the final decision based on those summaries. Strict boundaries enforced (`NEET` to `NEET` only).
"""

    report_path = os.path.join(os.path.dirname(__file__), '..', '..', 'brain', '6c63da0d-fcc9-4ae8-bb18-6cfaf1890268', 'chapter_classification_report.md')
    report_path = os.path.abspath(report_path)
    
    print(f"Writing report to: {report_path}")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    db.close()

if __name__ == "__main__":
    generate_report()
