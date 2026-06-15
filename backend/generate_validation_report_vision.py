import os
import json
from database import SessionLocal
from models import Question, QuestionAsset, QuestionPaper
import random

db = SessionLocal()

paper = db.query(QuestionPaper).filter(QuestionPaper.source_file == "2024 neet pw.pdf").first()

if not paper:
    print("Paper not found in database.")
    exit(1)

questions = db.query(Question).filter(Question.paper_id == paper.id, Question.extraction_method == "vision_agentzero").order_by(Question.question_number).all()

if not questions:
    print("No vision extractions found.")
    exit(1)

# Load stats
stats_file = os.path.join(os.path.dirname(__file__), "run_stats.json")
stats = {"request_count": 0, "timeout_count": 0, "error_count": 0, "total_duration": 0.0}
if os.path.exists(stats_file):
    with open(stats_file, "r") as f:
        stats = json.load(f)

model_used = questions[0].extraction_model if questions and hasattr(questions[0], 'extraction_model') else "qwen-3-7-plus"
provider_used = "Agent Zero"

total_q = len(questions)
expected_q = 50
valid_4_options = sum(1 for q in questions if q.option_a and q.option_b and q.option_c and q.option_d)
missing_options = total_q - valid_4_options
diagram_qs = sum(1 for q in questions if db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count() > 0)
needs_review = sum(1 for q in questions if q.needs_manual_review)

# Confidence
avg_conf = sum(q.extraction_confidence for q in questions if q.extraction_confidence) / total_q if total_q > 0 else 0

# Duplicates & Missing
q_nums = [q.question_number for q in questions if q.question_number]
duplicates = []
seen = set()
for n in q_nums:
    if n in seen:
        duplicates.append(n)
    seen.add(n)
    
missing_seq = []
for i in range(1, min(max(q_nums)+1 if q_nums else 51, 51)):
    if i not in seen:
        missing_seq.append(i)

report_content = f"""# Full Physics 2024 Vision Extraction Report

## Run Telemetry
- **Total Requests:** {stats['request_count']}
- **Timeouts/Errors:** {stats['timeout_count']} / {stats['error_count']}
- **Total Duration:** {stats['total_duration']:.1f} seconds
- **Provider:** {provider_used}
- **Model:** {model_used}
- **Image Settings:** 150 DPI, JPEG

## Extraction Metrics
- **Real Physics Questions Detected:** {total_q}
- **Expected Questions:** {expected_q}
- **Questions with all 4 options:** {valid_4_options}
- **Questions missing options:** {missing_options}
- **Diagram-based Questions:** {diagram_qs}
- **Questions needing manual review:** {needs_review}
- **Average Extraction Confidence:** {avg_conf:.2f}

## Sequence Quality
- **Duplicate Question Numbers:** {duplicates if duplicates else 'None'}
- **Missing Question Numbers (1-50):** {missing_seq if missing_seq else 'None'}

## Sample Extracted Questions
"""

plain_candidates = [q for q in questions if not db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count() and len(q.question_text) > 40]
formula_candidates = [q for q in questions if ("=" in q.question_text or "^" in q.question_text or "/" in q.question_text) and not db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count()]
diagram_candidates = [q for q in questions if db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count() > 0]
list_candidates = [q for q in questions if "List-I" in q.question_text or "List I" in q.question_text]
horizontal_candidates = [q for q in questions if q.option_a and len(q.option_a) < 15 and q.option_b and len(q.option_b) < 15 and not "List" in q.question_text]
uncertain_candidates = [q for q in questions if q.needs_manual_review]

def get_random(candidates, count=1, exclude=[]):
    valid = [c for c in candidates if c.id not in exclude]
    if not valid: return []
    return random.sample(valid, min(count, len(valid)))

samples_dict = {}
seen_ids = set()

for s in get_random(plain_candidates, 3, seen_ids):
    samples_dict[s.id] = ("Plain Text", s)
    seen_ids.add(s.id)

for s in get_random(formula_candidates, 2, seen_ids):
    samples_dict[s.id] = ("Numerical/Formula", s)
    seen_ids.add(s.id)

for s in get_random(diagram_candidates, 2, seen_ids):
    samples_dict[s.id] = ("Diagram-Based", s)
    seen_ids.add(s.id)

for s in get_random(list_candidates, 1, seen_ids):
    samples_dict[s.id] = ("List-Matching", s)
    seen_ids.add(s.id)

for s in get_random(horizontal_candidates, 1, seen_ids):
    samples_dict[s.id] = ("Horizontal-Options", s)
    seen_ids.add(s.id)

for s in get_random(uncertain_candidates, 1, seen_ids):
    samples_dict[s.id] = ("Uncertain/Needs Review", s)
    seen_ids.add(s.id)

# Render samples
if not samples_dict:
    report_content += "*No samples extracted.*\n"
else:
    for q_id, (label, q) in samples_dict.items():
        report_content += f"### {label}\n"
        report_content += f"**Q{q.question_number}:** {q.question_text.strip()[:400]}...\n"
        report_content += f"- **A:** {q.option_a}\n"
        report_content += f"- **B:** {q.option_b}\n"
        report_content += f"- **C:** {q.option_c}\n"
        report_content += f"- **D:** {q.option_d}\n"
        img_count = db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count()
        if img_count > 0:
            img_asset = db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).first()
            report_content += f"- **Diagram Source Column:** ![Diagram]({img_asset.image_url})\n"
            report_content += f"- **Diagram Description:** {img_asset.caption}\n"
        report_content += f"- *Confidence:* {q.extraction_confidence} | *Needs Review:* {q.needs_manual_review}\n\n"

artifact_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'brain', '6c63da0d-fcc9-4ae8-bb18-6cfaf1890268')
os.makedirs(artifact_dir, exist_ok=True)
report_path = os.path.join(artifact_dir, "parser_validation_report.md")

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_content)

print(f"Report generated at {report_path}")
