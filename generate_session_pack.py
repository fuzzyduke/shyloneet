import sys
import os

sys.path.append(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")
from database import SessionLocal
from models import Question, QuestionChapterMap, Chapter

def generate_pack():
    db = SessionLocal()
    
    # We want mandatory_review, review_recommended, and unmapped questions
    # from the neet-2024 paper.
    
    # 1. Fetch all questions for neet-2024
    paper_id = 'de0e8ff1-a244-4c33-852f-2a0cb501772f'
    questions = db.query(Question).filter_by(paper_id=paper_id, is_mock=False).all()
    
    # Sort them by unmapped, mandatory, recommended. Then by question_number.
    
    unmapped = []
    mandatory = []
    recommended = []
    
    for q in questions:
        # Check mapping
        primary_maps = [m for m in q.mappings if m.is_primary]
        if not primary_maps:
            unmapped.append(q)
        else:
            m = primary_maps[0]
            if not m.approved_by_admin:
                if m.needs_manual_review:
                    mandatory.append(q)
                else:
                    recommended.append(q)
            # If approved_by_admin, it's auto_approved, so we ignore it.
            
    unmapped.sort(key=lambda x: x.question_number)
    mandatory.sort(key=lambda x: x.question_number)
    recommended.sort(key=lambda x: x.question_number)
    
    total_locked = len(unmapped) + len(mandatory) + len(recommended)
    
    lines = []
    lines.append("# Admin Review Session Pack")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- **Total Locked Questions:** {total_locked}")
    lines.append(f"- **Unmapped:** {len(unmapped)}")
    lines.append(f"- **Mandatory Review:** {len(mandatory)}")
    lines.append(f"- **Review Recommended:** {len(recommended)}")
    lines.append(f"- **Likely Easy Approvals:** {len(recommended)}")
    lines.append(f"- **Likely Chapter Changes Needed:** {len(unmapped)}")
    lines.append(f"- **Questions Needing Careful Human Inspection:** {len(mandatory) + len(unmapped)}")
    
    diagram_heavy = sum(1 for q in (unmapped + mandatory + recommended) if q.assets)
    extraction_concerns = sum(1 for q in (unmapped + mandatory + recommended) if q.incompatibility_flags)
    
    lines.append(f"- **Diagram-Heavy Questions:** {diagram_heavy}")
    lines.append(f"- **Extraction-Quality Concerns:** {extraction_concerns}")
    lines.append("")
    
    lines.append("---")
    
    # Helper to print question details
    def print_q(q, queue_name):
        primary_map = next((m for m in q.mappings if m.is_primary), None)
        sec_maps = [m for m in q.mappings if not m.is_primary]
        
        lines.append(f"### Q{q.question_number} (ID: `{q.id}`)")
        lines.append(f"**Queue:** {queue_name}")
        lines.append(f"**Text:**\n> {q.question_text.replace(chr(10), ' ')}")
        lines.append("**Options:**")
        lines.append(f"- A: {q.option_a}")
        lines.append(f"- B: {q.option_b}")
        lines.append(f"- C: {q.option_c}")
        lines.append(f"- D: {q.option_d}")
        
        if q.assets:
            lines.append("**Diagrams/Assets:**")
            for a in q.assets:
                lines.append(f"- {a.asset_type}: {a.image_url} (Caption: {a.caption})")
        else:
            lines.append("**Diagrams/Assets:** None")
            
        if primary_map:
            chap_name = primary_map.chapter.chapter_name if primary_map.chapter else "Unknown"
            conf = f"{primary_map.confidence*100:.1f}%" if primary_map.confidence else "N/A"
            lines.append(f"**Current Mapped Chapter:** {chap_name} (Confidence: {conf})")
            lines.append(f"**Reason:** {primary_map.reason}")
        else:
            lines.append("**Current Mapped Chapter:** None")
            lines.append("**Reason:** N/A")
            
        lines.append("**Top 3 Embedding Candidates:** Not stored in DB")
        lines.append("**LLM Suggested Chapter:** Not stored in DB")
        lines.append("**NCERT Evidence Snippets:** Not stored in DB")
        
        if queue_name == "unmapped":
            lines.append("**Why it needs review:** No chapter assigned. Classification failed or was ambiguous.")
            lines.append("**Recommended Admin Action:** assign primary chapter")
        elif queue_name == "mandatory_review":
            lines.append("**Why it needs review:** Flagged for mandatory manual review due to low confidence, multi-chapter overlap, or extraction flags.")
            lines.append("**Recommended Admin Action:** change primary chapter / approve as-is")
        else:
            lines.append("**Why it needs review:** Review recommended to ensure accuracy, though confidence was sufficient to not mandate review.")
            lines.append("**Recommended Admin Action:** approve as-is")
            
        lines.append("**Suggested Primary Chapter:** (Human to fill)")
        lines.append(f"**Suggested Secondary Chapters:** {', '.join([m.chapter.chapter_name for m in sec_maps if m.chapter]) if sec_maps else 'None'}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
    for q in unmapped:
        print_q(q, "unmapped")
        
    for q in mandatory:
        print_q(q, "mandatory_review")
        
    for q in recommended:
        print_q(q, "review_recommended")
        
    report_path = r"C:\Users\edsel\.gemini\antigravity-ide\brain\6c63da0d-fcc9-4ae8-bb18-6cfaf1890268\admin_review_session_pack.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print("Report generated.")

if __name__ == "__main__":
    generate_pack()
