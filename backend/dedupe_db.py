import os
import shutil
import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Question, QuestionChapterMap, QuestionAsset

# 1. Backup DB
db_path = "neetvault.db"
backup_dir = "backups"
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"neetvault_backup_{timestamp}.db")

try:
    shutil.copy2(db_path, backup_path)
    backup_success = True
except Exception as e:
    backup_success = False
    backup_error = str(e)

if not backup_success:
    print(json.dumps({"error": f"Backup failed: {backup_error}"}))
    exit(1)

# Connect to DB
engine = create_engine(f"sqlite:///{db_path}")
Session = sessionmaker(bind=engine)
session = Session()

# 2. Scope & Grouping
target_paper_id = session.query(Question.paper_id).filter(
    Question.exam_program_id == "NEET", 
    Question.year == 2024, 
    Question.subject == "Physics",
    Question.paper_id != None
).first()[0]

all_physics_qs = session.query(Question).filter(
    Question.exam_program_id == "NEET",
    Question.year == 2024,
    Question.subject == "Physics"
).all()

total_before = len(all_physics_qs)
unique_q_numbers_before = len(set(q.question_number for q in all_physics_qs))
mappings_before = session.query(QuestionChapterMap).join(Question).filter(
    Question.exam_program_id == "NEET", Question.year == 2024, Question.subject == "Physics"
).count()

groups = {}
for q in all_physics_qs:
    groups.setdefault(q.question_number, []).append(q)

# 4. Scoring function
def score_question(q):
    score = 0
    # 1. is_mock = false
    if not q.is_mock: score += 100
    
    # 2. source_type = real_pdf_extraction
    if q.source_type == "real_pdf_extraction": score += 100
    
    # 3. extraction_status = success
    if q.extraction_status in ["success", "clean", "approved"]: score += 200
    elif q.extraction_status == "needs_review": score -= 50
    
    # 4. all 4 options present
    if q.option_a and q.option_b and q.option_c and q.option_d: score += 150
    else: score -= 100
    
    # 5 & 6. question text length and presence
    q_text = q.question_text or ""
    if q_text.strip():
        score += 50
        length = len(q_text)
        if 20 < length < 1500: # reasonable length
            score += min(length // 10, 50) 
        elif length < 20: # too short
            score -= 50
    else:
        score -= 200
        
    # Incompatibility flags
    if q.incompatibility_flags:
        try:
            flags = json.loads(q.incompatibility_flags)
            score -= (len(flags) * 30)
        except:
            pass
            
    # Extraction confidence
    if q.extraction_confidence:
        score += int(q.extraction_confidence * 50)
        
    return score

kept_ids = {}
deleted_ids = []
duplicate_groups_count = 0

for q_num, group in groups.items():
    if len(group) > 1:
        duplicate_groups_count += 1
    
    # Score each
    scored = [(score_question(q), q) for q in group]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    best_q = scored[0][1]
    kept_ids[q_num] = best_q.id
    
    for _, q in scored[1:]:
        deleted_ids.append(q.id)

# 5 & 6. Cleanup Duplicates & Mappings
# First delete mappings for deleted questions
session.query(QuestionChapterMap).filter(QuestionChapterMap.question_id.in_(deleted_ids)).delete(synchronize_session=False)

# Delete orphaned assets
session.query(QuestionAsset).filter(QuestionAsset.question_id.in_(deleted_ids)).delete(synchronize_session=False)

# Delete the duplicate questions
session.query(Question).filter(Question.id.in_(deleted_ids)).delete(synchronize_session=False)

# Check mappings for kept questions
auto_approved = 0
review_recommended = 0
mandatory_review = 0
no_mapping = 0
boundary_violations = 0

for q_num, q_id in kept_ids.items():
    kept_q = session.query(Question).filter(Question.id == q_id).first()
    kept_q.paper_id = target_paper_id
    mappings = session.query(QuestionChapterMap).filter(QuestionChapterMap.question_id == q_id).all()
    
    if not mappings:
        no_mapping += 1
        kept_q.needs_manual_review = True
        continue
        
    # If multiple mappings, keep the one with highest confidence
    if len(mappings) > 1:
        mappings.sort(key=lambda m: m.confidence or 0.0, reverse=True)
        best_map = mappings[0]
        # delete others
        for m in mappings[1:]:
            session.delete(m)
        
        # update the best map
        best_map.is_primary = True
        mappings = [best_map]
    
    m = mappings[0]
    # Check boundary violation
    if m.chapter and m.chapter.exam_program_id != "NEET":
        boundary_violations += 1
        m.needs_manual_review = True
        
    # Calculate status based on current logic
    if m.mapping_method == "embedding_fallback":
        m.needs_manual_review = True
        m.approved_by_admin = False
    elif m.mapping_method == "embedding_plus_llm":
        if m.confidence and m.confidence >= 0.85 and not m.needs_manual_review:
            m.approved_by_admin = True
        elif m.confidence and m.confidence >= 0.70 and not m.needs_manual_review:
            m.approved_by_admin = False
        else:
            m.needs_manual_review = True
            m.approved_by_admin = False
            
    # Count stats
    if m.approved_by_admin:
        auto_approved += 1
    elif m.needs_manual_review:
        mandatory_review += 1
    else:
        review_recommended += 1

session.commit()

# Final validation metrics
all_physics_after = session.query(Question).filter(
    Question.exam_program_id == "NEET",
    Question.year == 2024,
    Question.subject == "Physics",
    Question.paper_id == target_paper_id
).all()

total_after = len(all_physics_after)
q_numbers_after = sorted([q.question_number for q in all_physics_after])
unique_q_numbers_after = len(set(q_numbers_after))

mappings_after = session.query(QuestionChapterMap).join(Question).filter(
    Question.exam_program_id == "NEET", Question.year == 2024, Question.subject == "Physics"
).count()

expected_nums = set(list(range(1, 22)) + list(range(24, 39)) + list(range(40, 51)))
missing = [n for n in range(1, 51) if n not in q_numbers_after]

orphaned_assets = session.query(QuestionAsset).outerjoin(Question).filter(Question.id == None).count()

output = {
    "backup_path": os.path.abspath(backup_path),
    "total_before": total_before,
    "unique_before": unique_q_numbers_before,
    "duplicate_groups": duplicate_groups_count,
    "deleted_ids_count": len(deleted_ids),
    "total_after": total_after,
    "unique_after": unique_q_numbers_after,
    "missing_numbers": missing,
    "mappings_before": mappings_before,
    "mappings_after": mappings_after,
    "no_mapping": no_mapping,
    "auto_approved": auto_approved,
    "review_recommended": review_recommended,
    "mandatory_review": mandatory_review,
    "boundary_violations": boundary_violations,
    "orphaned_assets": orphaned_assets
}

print(json.dumps(output, indent=2))
