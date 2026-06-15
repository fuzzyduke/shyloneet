import re
import fitz
import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import QuestionPaper, Question, QuestionAsset

Base.metadata.create_all(bind=engine)

def parse_paper(filepath: str, db: Session, exam_type="NEET", year=2024, paper_code="T3"):
    filename = os.path.basename(filepath)
    
    # Delete existing paper to start fresh for validation
    existing = db.query(QuestionPaper).filter(QuestionPaper.source_file == filename).first()
    if existing:
        db.delete(existing)
        db.commit()

    paper = QuestionPaper(
        exam_type=exam_type,
        year=year,
        paper_code=paper_code,
        source_file=filename,
        upload_status="processing",
        processing_status="started"
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
        
    doc = fitz.open(filepath)
    
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets', 'papers', paper.id)
    os.makedirs(assets_dir, exist_ok=True)
    
    current_subject = "Physics"
    current_question = None
    
    # Matches "1. ", "50. ", etc.
    q_start_pattern = re.compile(r'^\s*(\d+)\.\s+(.*)', re.DOTALL)
    
    # Matches "(1) ", "(2) " at the start of a line
    opt_start_pattern = re.compile(r'^\s*[(]?([1-4])[).]\s+(.*)', re.DOTALL)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_width = page.rect.width
        
        blocks = page.get_text("blocks")
        
        # Filter for text blocks (type 0)
        text_blocks = [b for b in blocks if b[6] == 0]
        
        # Sort column-aware: Col 1 then Col 2, then by y0
        def sort_key(b):
            col = 0 if b[0] < (page_width / 2) else 1
            return (col, b[1])
            
        text_blocks.sort(key=sort_key)
        
        for block in text_blocks:
            # decode ascii to avoid charmaps error, or just ignore errors
            text = block[4].strip()
            # Try to fix weird encodings if any
            text = text.encode('ascii', 'ignore').decode('ascii').strip()
            
            if not text:
                continue

            # Check if this block starts a new question
            q_match = q_start_pattern.match(text)
            if q_match:
                q_num = int(q_match.group(1))
                if q_num > 50:
                    # We only want Physics (1-50) for this validation run
                    continue
                
                # Save previous question if exists
                if current_question:
                    db.add(current_question)
                
                q_text = q_match.group(2)
                
                current_question = Question(
                    paper_id=paper.id,
                    year=year,
                    exam_type=exam_type,
                    paper_code=paper_code,
                    subject="Physics",
                    question_number=q_num,
                    question_text=q_text,
                    source_pdf=filename,
                    page_number=page_num + 1,
                    extraction_confidence=0.9
                )
                
                # Check if options are inline in the same block
                _parse_inline_options(current_question)
                
            elif current_question:
                # Is it an option block?
                opt_match = opt_start_pattern.match(text)
                if opt_match:
                    opt_num = opt_match.group(1)
                    opt_text = opt_match.group(2)
                    _set_option(current_question, opt_num, opt_text)
                    _parse_inline_options(current_question)
                else:
                    # Is it multiple options inline without starting with one?
                    if "(1)" in text or "(2)" in text or "(3)" in text or "(4)" in text:
                        # Append to current question text and parse inline
                        current_question.question_text += "\n" + text
                        _parse_inline_options(current_question)
                    else:
                        # Standard question continuation
                        # If we already have options, it might be broken text, but let's just append to text
                        current_question.question_text += "\n" + text

        # Extract Images and associate with current question
        # To be highly accurate, we'd check image physical bounds against question bounds.
        # For simplicity in MVP, we just assign page images to whatever the last parsed question was on that column, 
        # or we just get images and assign them based on their physical y0.
        
        img_info = page.get_image_info(xrefs=True)
        for img in img_info:
            xref = img["xref"]
            bbox = img["bbox"] # (x0, y0, x1, y1)
            
            # Extract
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                if len(image_bytes) < 3000:
                    continue # skip tiny icons/noise
                
                # Find which question this belongs to by looking at text blocks near it
                # For MVP, if there is a current question on this page, attach it.
                if current_question:
                    image_filename = f"q{current_question.question_number}_img_{xref}.{image_ext}"
                    image_path = os.path.join(assets_dir, image_filename)
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                        
                    asset = QuestionAsset(
                        question_id=current_question.id,
                        asset_type="diagram",
                        image_url=f"/data/assets/papers/{paper.id}/{image_filename}",
                        caption=f"Extracted from page {page_num + 1}",
                        page_number=page_num + 1
                    )
                    db.add(asset)
            except:
                pass

    if current_question:
        db.add(current_question)

    paper.upload_status = "completed"
    paper.processing_status = "completed"
    db.commit()
    print(f"Extracted questions from {filename}")

def _set_option(q: Question, opt_num: str, text: str):
    text = text.strip()
    if opt_num == '1': q.option_a = text
    elif opt_num == '2': q.option_b = text
    elif opt_num == '3': q.option_c = text
    elif opt_num == '4': q.option_d = text

def _parse_inline_options(q: Question):
    # Search for (1) ... (2) ... (3) ... (4) ... inside q.question_text
    parts = re.split(r'\(([1-4])\)', q.question_text)
    if len(parts) > 1:
        # parts[0] is the pure question text
        q.question_text = parts[0].strip()
        # parts[1] is '1', parts[2] is text for 1
        for i in range(1, len(parts)-1, 2):
            opt_num = parts[i]
            opt_text = parts[i+1]
            _set_option(q, opt_num, opt_text)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python paper_parser.py <path_to_paper_pdf>")
        sys.exit(1)
    
    path = sys.argv[1]
    db = SessionLocal()
    parse_paper(path, db)
    db.close()
