import os
from database import SessionLocal
from models import Question, QuestionAsset, QuestionPaper
import random

db = SessionLocal()

paper = db.query(QuestionPaper).filter(QuestionPaper.source_file == "2024 neet pw.pdf").first()

if not paper:
    print("Paper not found in database.")
    exit(1)

questions = db.query(Question).filter(Question.paper_id == paper.id).all()

total = len(questions)
all_options = 0
missing_options = 0
with_images = 0
with_answers = 0

for q in questions:
    if q.option_a and q.option_b and q.option_c and q.option_d:
        all_options += 1
    else:
        missing_options += 1
        
    assets = db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count()
    if assets > 0:
        with_images += 1
        
    if q.answer:
        with_answers += 1

manual_review = missing_options + (total - with_answers)  # Rough metric

report_content = f"""# Parser Validation Report

## Metrics
- **Total Physics Questions Detected:** {total} (Expected: 50)
- **Questions with all 4 options cleanly detected:** {all_options}
- **Questions with missing options:** {missing_options}
- **Questions with diagrams/images:** {with_images}
- **Questions with inline answers detected:** {with_answers}
- **Questions needing manual extraction review:** {manual_review}

## Sample Extracted Questions

"""

# 5 samples
plain_candidates = [q for q in questions if not db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count()]
formula_candidates = [q for q in questions if "=" in q.question_text or "^" in q.question_text]
diagram_candidates = [q for q in questions if db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count() > 0]

plain = random.choice(plain_candidates) if plain_candidates else questions[0]
formula = random.choice(formula_candidates) if formula_candidates else questions[1]
diagram = random.choice(diagram_candidates) if diagram_candidates else questions[2]
uncertain = next((q for q in questions if not q.option_d), questions[3])

samples = [
    ("Plain Text Question", plain),
    ("Formula-Heavy Question", formula),
    ("Diagram-Based Question", diagram),
    ("Difficult/Uncertain Extraction", uncertain)
]

for label, q in samples:
    report_content += f"### {label}\n"
    report_content += f"**Q{q.question_number}:** {q.question_text.strip()[:300]}...\n"
    report_content += f"- **A:** {q.option_a}\n"
    report_content += f"- **B:** {q.option_b}\n"
    report_content += f"- **C:** {q.option_c}\n"
    report_content += f"- **D:** {q.option_d}\n"
    img_count = db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).count()
    if img_count > 0:
        img_url = db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).first().image_url
        report_content += f"- **Diagram:** ![Diagram]({img_url})\n"
    report_content += "\n"

# Write to artifact dir
artifact_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'brain', '6c63da0d-fcc9-4ae8-bb18-6cfaf1890268')
os.makedirs(artifact_dir, exist_ok=True)
report_path = os.path.join(artifact_dir, "parser_validation_report.md")

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_content)

print(f"Report generated at {report_path}")
