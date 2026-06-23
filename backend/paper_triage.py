import re
import fitz
import os
import json
import uuid
from sqlalchemy.orm import Session
import models

def triage_parse_paper(filepath: str, db: Session, metadata: dict = None) -> str:
    filename = os.path.basename(filepath)
    
    # 1. Handle default metadata if not provided
    if not metadata:
        metadata = {
            "exam": "NEET",
            "year": 2024,
            "set_code": "Model 10",
            "source": "Vedantu",
            "paper_type": "questions_with_options_and_answer_key",
            "expected_question_count": 180,
            "subjects": ["Physics", "Chemistry", "Biology"]
        }

    # Extract metadata properties
    exam = metadata.get("exam", "NEET")
    year = metadata.get("year", 2024)
    set_code = metadata.get("set_code", "Model 10")
    source = metadata.get("source", "Vedantu")
    paper_type = metadata.get("paper_type", "questions_with_options_and_answer_key")
    expected_count = int(metadata.get("expected_question_count", 180))
    subjects_list = metadata.get("subjects", ["Physics", "Chemistry", "Biology"])
    
    # Clean existing records for this paper to allow clean rebuilds
    existing_paper = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.source_name == source,
        models.QuestionPaper.year == year,
        models.QuestionPaper.paper_code == set_code
    ).first()
    
    if existing_paper:
        # Get list of question IDs to safely delete their assets
        q_ids = [q.id for q in db.query(models.Question.id).filter(models.Question.paper_id == existing_paper.id).all()]
        if q_ids:
            db.query(models.QuestionAsset).filter(models.QuestionAsset.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(models.AnswerEvaluation).filter(models.AnswerEvaluation.paper_id == existing_paper.id).delete(synchronize_session=False)
        db.query(models.Question).filter(models.Question.paper_id == existing_paper.id).delete(synchronize_session=False)
        db.delete(existing_paper)
        db.commit()

    # 2. Initialize paper record
    paper = models.QuestionPaper(
        id=str(uuid.uuid4()),
        exam_type=exam,
        year=year,
        paper_code=set_code,
        source_file=filename,
        exam_program_id=exam,
        source_type="question_paper",
        source_name=source,
        upload_status="completed",
        processing_status="completed",
        solution_status="unavailable",
        scoring_enabled=False,
        scoring_source="none",
        paper_type=paper_type,
        expected_question_count=expected_count,
        subjects_included=",".join(subjects_list),
        import_status="draft" # Admin starts in DRAFT review state
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    doc = fitz.open(filepath)
    
    # Target directory for assets
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assets_dir = os.path.join(parent_dir, "data", "assets", "papers", paper.id)
    os.makedirs(assets_dir, exist_ok=True)

    # Patterns matching question numberings and option structures
    q_start_pattern = re.compile(r'^\s*(\d+)\s*[\.).]\s*(.*)', re.DOTALL)
    opt_start_pattern = re.compile(r'^\s*[(]?([1-4A-Da-d])[).]\s+(.*)', re.DOTALL)

    questions_parsed = []
    current_q = None
    current_subject = "Physics"
    
    # Sequence-aware parsing variables
    next_expected_q = 1
    subject_header_seen = False
    fake_option_candidates_count = 0
    stop_parsing = False
    # New helper to detect option labels (numeric, alphabetic, parenthesized) and short math patterns, including plain numbers
    def is_option_label(text: str, q_num: int, current_q):
        # Detect numeric/alpha option markers like 1., (1), A., (A), A) etc.
        opt_marker = re.match(r'^\s*[(]?([1-4A-Da-d])[).]?\s*$', text, re.IGNORECASE)
        if opt_marker:
            return True
        # Detect plain numeric option without dot/parenthesis (e.g., "1 " on its own line)
        plain_num = re.match(r'^\s*([1-4])\s*$', text)
        if plain_num:
            return True
        # Short mathematical patterns that should not be questions
        math_patterns = [
            r'^\s*\d+/?\d*\s*$',                # numbers or fractions
            r'^\s*[\d\.]+\s*(?:a0|a_0|V|°|rad|Hz|N|m|s|kg|J|W|C|T|A|V|Ohm|ohm|Ω|F|H)\s*$',
            r'^\s*[\d\.]+\s*x\s*10\s*\^?\s*-?\d+\s*.*$',
            r'^\s*[\d\.]+\s*×\s*10\s*\^?\s*-?\d+\s*.*$'
        ]
        if any(re.match(p, text.strip()) for p in math_patterns):
            return True
        return False
    
    # Build list of parsed questions across all pages
    for page_num in range(len(doc)):
        if stop_parsing:
            break
        page = doc.load_page(page_num)
        page_width = page.rect.width
        page_height = page.rect.height
        
        blocks = page.get_text("blocks")
        text_blocks = [b for b in blocks if b[6] == 0]
        
        # Column-aware sorting: Column 1 first (left half), then Column 2 (right half)
        def sort_key(b):
            col = 0 if b[0] < (page_width / 2) else 1
            return (col, b[1])
            
        text_blocks.sort(key=sort_key)

        for block in text_blocks:
            if stop_parsing:
                break
            text = block[4].strip()
            text = text.encode("utf-8", "ignore").decode("utf-8").strip()
            
            if not text or "www.vedantu.com" in text:
                continue

            # Check if this text block is a section header itself
            cleaned_block = text.upper().strip()
            if cleaned_block in ["PHYSICS", "PHYSICS SECTION", "SECTION A - PHYSICS", "SECTION B - PHYSICS"]:
                current_subject = "Physics"
                subject_header_seen = True
                continue
            elif cleaned_block in ["CHEMISTRY", "CHEMISTRY SECTION", "SECTION A - CHEMISTRY", "SECTION B - CHEMISTRY"]:
                stop_parsing = True
                break
            elif cleaned_block in ["BIOLOGY", "BIOLOGY SECTION", "BOTANY", "ZOOLOGY", "SECTION A - BOTANY", "SECTION B - ZOOLOGY"]:
                stop_parsing = True
                break

            q_match = q_start_pattern.match(text)
            if q_match:
                q_num = int(q_match.group(1))
                q_text = q_match.group(2).strip()
                
                # Early stop for chemistry or beyond physics range
                if q_num >= 46:
                    stop_parsing = True
                    break
                
                # Determine if this line is actually an option label (including plain numbers and lowercase letters)
                if is_option_label(text, q_num, current_q):
                    # Treat as option, not a new question
                    fake_option_candidates_count += 1
                    # Append to current question if exists and record warning
                    if current_q:
                        # Record that an option line was mistaken as a question
                        current_q["triage_warnings"].append("Fake option detected")
                        current_q["needs_review"] = True
                        current_q["review_reasons"].append("Option line misidentified as question")
                        current_q["raw_text"] += "\n" + text
                        current_q["blocks"].append(block)
                        opt_match = opt_start_pattern.match(text)
                        if opt_match:
                            opt_id = opt_match.group(1).upper()
                            opt_text = opt_match.group(2).strip()
                            _set_option_val(current_q, opt_id, opt_text)
                        else:
                            # Fallback inline detection for options
                            if any(f"({i})" in text for i in ["1","2","3","4","A","B","C","D"]) or any(f"{i}." in text for i in ["1","2","3","4","A","B","C","D"]):
                                _parse_inline_options_dict_raw(current_q, text)
                    # Skip question creation logic
                    continue
                
                # Verify sequential question number (physics only 1-45)
                is_valid_q = False
                if next_expected_q <= q_num <= 45:
                    is_valid_q = True
                else:
                    # Out‑of‑order or beyond expected range
                    if current_q:
                        # Record warning on previous question
                        current_q["needs_review"] = True
                        current_q["review_reasons"].append(f"Out‑of‑order number {q_num}")
                
                if is_valid_q:
                    subject_header_seen = False
                    next_expected_q = q_num + 1
                    
                    if current_q:
                        _parse_inline_options_dict(current_q)
                        questions_parsed.append(current_q)
                    
                    inferred_sub = current_subject
                    if current_subject not in ["Botany", "Zoology"]:
                        if 1 <= q_num <= 45:
                            inferred_sub = "Physics"
                        elif 46 <= q_num <= 90:
                            inferred_sub = "Chemistry"
                        elif 91 <= q_num <= 180:
                            inferred_sub = "Biology"
                        current_subject = inferred_sub
                    
                    current_q = {
                        "question_number": q_num,
                        "subject": inferred_sub,
                        "question_text": q_match.group(2).strip(),
                        "options": {"A": "", "B": "", "C": "", "D": ""},
                        "page_number": page_num + 1,
                        "raw_text": text,
                        "needs_review": False,
                        "review_reasons": [],
                        "triage_warnings": [],
                        "blocks": [block]
                    }
                    _parse_inline_options_dict(current_q)
                else:
                    # Not a valid question start, treat as body/option block
                    if current_q:
                        current_q["raw_text"] += "\n" + text
                        current_q["blocks"].append(block)
                        opt_match = opt_start_pattern.match(text)
                        if opt_match:
                            opt_id = opt_match.group(1).upper()
                            opt_text = opt_match.group(2).strip()
                            _set_option_val(current_q, opt_id, opt_text)
                        else:
                            if any(f"({i})" in text for i in ["1","2","3","4","A","B","C","D"]) or any(f"{i}." in text for i in ["1","2","3","4","A","B","C","D"]):
                                _parse_inline_options_dict_raw(current_q, text)
                            else:
                                current_q["question_text"] += "\n" + text
            elif current_q:
                current_q["raw_text"] += "\n" + text
                current_q["blocks"].append(block)
                
                opt_match = opt_start_pattern.match(text)
                if opt_match:
                    opt_id = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    _set_option_val(current_q, opt_id, opt_text)
                    _parse_inline_options_dict(current_q)
                else:
                    # Check for inline options
                    if any(f"({i})" in text for i in ["1", "2", "3", "4", "A", "B", "C", "D"]) or any(f"{i}." in text for i in ["1", "2", "3", "4", "A", "B", "C", "D"]):
                        _parse_inline_options_dict_raw(current_q, text)
                    else:
                        current_q["question_text"] += "\n" + text

    # Append the last parsed question
    if current_q:
        _parse_inline_options_dict(current_q)
        questions_parsed.append(current_q)

    # Cache answer key answers if parsed_answers.json exists locally
    answers_cache = {}
    answers_path = os.path.join(parent_dir, "parsed_answers.json")
    if os.path.exists(answers_path):
        try:
            with open(answers_path, "r", encoding="utf-8") as f:
                answers_cache = json.load(f)
        except Exception as e:
            print(f"Error loading answers cache: {e}")

    # Subject counters for subject-local numbering
    subject_counts = {}

    # Post-process, extract diagram assets, and write to database
    for q_data in questions_parsed:
        q_num = q_data["question_number"]
        subj = q_data["subject"]
        
        # Calculate local numbering
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
        local_num = subject_counts[subj]
        
        # Determine extraction status
        ext_status = "success"
        opt_count = sum(1 for opt in [q_data["options"]["A"], q_data["options"]["B"], q_data["options"]["C"], q_data["options"]["D"]] if opt)
        
        # Validate options completeness
        missing_opts = [k for k, v in q_data["options"].items() if not v]
        if missing_opts:
            q_data["needs_review"] = True
            q_data["review_reasons"].append(f"Missing options: {', '.join(missing_opts)}")
            ext_status = "partial"
        # Add triage warnings list if not present
        if "triage_warnings" not in q_data:
            q_data["triage_warnings"] = []
        # If any review reasons exist, add a warning entry
        if q_data["needs_review"]:
            q_data["triage_warnings"].append("Needs review due to missing options or content")
        # Check for complex formulas indicating review needs
        math_symbols = ["\\", "√", "π", "λ", "ω", "𝑞", "𝜀", "𝜃", "Ω", "→", "−", "∆", "∘", "^", "_"]
        if any(sym in q_data["question_text"] for sym in math_symbols):
            q_data["needs_review"] = True
            q_data["review_reasons"].append("Complex mathematical notations/equations detected")
            if ext_status == "success":
                ext_status = "needs_review"
        # Append any triage warnings collected earlier (if not already added)
        if q_data.get("triage_warnings"):
            q_data["review_reasons"].extend(q_data["triage_warnings"])

        # Inferred subject is unknown if it's out of standard bounds or unset
        if subj not in ["Physics", "Chemistry", "Biology", "Botany", "Zoology"]:
            q_data["needs_review"] = True
            q_data["review_reasons"].append("Subject detection uncertain")
            q_data["subject"] = "Unknown / Needs Review"
            if ext_status == "success":
                ext_status = "needs_review"

        # Lookup correct answer from cache if available
        correct_ans = ""
        ans_status = "unavailable"
        if str(q_num) in answers_cache:
            raw_val = answers_cache[str(q_num)]
            val = raw_val[0] if isinstance(raw_val, list) else str(raw_val)
            val = val.strip().upper()
            
            # Map 1-4 to A-D
            mapping = {"1": "A", "2": "B", "3": "C", "4": "D", "A": "A", "B": "B", "C": "C", "D": "D"}
            correct_ans = mapping.get(val, val)
            ans_status = "official_from_paper"

        # Compute Bounding Box of the question to align image coordinates
        q_blocks = q_data["blocks"]
        x0 = min(b[0] for b in q_blocks)
        y0 = min(b[1] for b in q_blocks)
        x1 = max(b[2] for b in q_blocks)
        y1 = max(b[3] for b in q_blocks)
        
        # Save question row
        q_obj = models.Question(
            id=str(uuid.uuid4()),
            paper_id=paper.id,
            year=year,
            exam_type=exam,
            paper_code=set_code,
            exam_program_id=exam,
            subject=q_data["subject"],
            question_number=q_num,
            question_number_global=q_num,
            question_number_subject=local_num,
            question_text=q_data["question_text"],
            option_a=q_data["options"]["A"],
            option_b=q_data["options"]["B"],
            option_c=q_data["options"]["C"],
            option_d=q_data["options"]["D"],
            answer=correct_ans,
            correct_option=correct_ans,
            solution_text="",
            difficulty="medium",
            source_pdf=filename,
            page_number=q_data["page_number"],
            extraction_confidence=0.85 if not q_data["needs_review"] else 0.6,
            needs_manual_review=q_data["needs_review"],
            source_type="real_pdf_extraction",
            is_mock=False,
            extraction_method="heuristic_triage_parser",
            extraction_model="fitz-regex-triage-v2",
            extraction_status=ext_status,
            incompatibility_flags=json.dumps(q_data["review_reasons"]) if q_data["needs_review"] else None,
            answer_status=ans_status,
            solution_source="none",
            solution_needs_review=True,
            scoring_eligible=False,
            publish_status="draft" # Draft state
        )
        db.add(q_obj)
        db.commit()
        db.refresh(q_obj)

        # 4. Handle Page Images/Diagrams associated with this question physically
        doc_page = doc.load_page(q_data["page_number"] - 1)
        image_list = doc_page.get_images(full=True)
        image_associated = False
        
        if image_list:
            for img in image_list:
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    if len(image_bytes) < 3000:
                        continue  # Skip header icons/decoration noise
                    
                    # Check drawing coordinates of the image
                    rects = doc_page.get_image_rects(xref)
                    if not rects:
                        continue
                    
                    # Align image coordinate with question column & vertical span
                    for r in rects:
                        # Column check
                        img_col = 0 if r.x0 < (page_width / 2) else 1
                        q_col = 0 if x0 < (page_width / 2) else 1
                        
                        if img_col == q_col:
                            # Vertical proximity check (image center lies within vertical span with margin)
                            img_center_y = (r.y0 + r.y1) / 2
                            if (y0 - 15) <= img_center_y <= (y1 + 15):
                                image_filename = f"q{q_num}_img_{xref}.{image_ext}"
                                image_path = os.path.join(assets_dir, image_filename)
                                
                                with open(image_path, "wb") as f:
                                    f.write(image_bytes)
                                    
                                asset = models.QuestionAsset(
                                    question_id=q_obj.id,
                                    asset_type="diagram",
                                    image_url=f"/data/assets/papers/{paper.id}/{image_filename}",
                                    caption=f"Extracted image/diagram for Q{q_num}",
                                    page_number=q_data["page_number"]
                                )
                                db.add(asset)
                                db.commit()
                                
                                # Tag question
                                q_obj.needs_manual_review = True
                                q_obj.extraction_status = "needs_review"
                                reasons = q_data["review_reasons"] + ["Diagram element associated"]
                                q_obj.incompatibility_flags = json.dumps(reasons)
                                image_associated = True
                                break
                    if image_associated:
                        break
                except Exception as e:
                    print(f"Error saving diagram for Q{q_num}: {e}")

        # 5. Fallback PDF Crop Asset if question is flagged for review or diagram keywords are present
        diagram_keywords = ["diagram", "figure", "graph", "circuit", "given below", "in the figure", "shown in"]
        has_keywords = any(kw in q_data["question_text"].lower() for kw in diagram_keywords)
        
        if q_obj.needs_manual_review or has_keywords:
            try:
                # Add small margin for crop
                margin = 8
                crop_rect = fitz.Rect(
                    max(0, x0 - margin),
                    max(0, y0 - margin),
                    min(page_width, x1 + margin),
                    min(page_height, y1 + margin)
                )
                
                pix = doc_page.get_pixmap(clip=crop_rect, dpi=150)
                crop_filename = f"q{q_num}_crop.png"
                crop_path = os.path.join(assets_dir, crop_filename)
                pix.save(crop_path)
                
                crop_asset = models.QuestionAsset(
                    question_id=q_obj.id,
                    asset_type="crop",
                    image_url=f"/data/assets/papers/{paper.id}/{crop_filename}",
                    caption=f"Original printed question crop for review",
                    page_number=q_data["page_number"]
                )
                db.add(crop_asset)
                db.commit()
            except Exception as e:
                print(f"Error creating fallback crop for Q{q_num}: {e}")

    # 5. Run validation checklist for Physics paper triage (Q1-Q45)
    questions_rows = db.query(models.Question).filter(models.Question.paper_id == paper.id).all()
    actual_nums = [q.question_number_global for q in questions_rows]
    expected_nums = set(range(1, 46))
    actual_set = set(actual_nums)
    
    missing_nums = sorted(list(expected_nums - actual_set))
    
    # duplicates
    seen_nums = set()
    dup_nums = set()
    for n in actual_nums:
        if n in seen_nums:
            dup_nums.add(n)
        seen_nums.add(n)
    dup_nums = sorted(list(dup_nums))
    
    fewer_than_4 = []
    with_diagrams = []
    needs_review_list = []
    for q in questions_rows:
        opts_count = sum(1 for opt in [q.option_a, q.option_b, q.option_c, q.option_d] if opt)
        if opts_count < 4:
            fewer_than_4.append(q.question_number_global)
        has_diag = db.query(models.QuestionAsset).filter(models.QuestionAsset.question_id == q.id, models.QuestionAsset.asset_type == "diagram").count() > 0
        if has_diag:
            with_diagrams.append(q.question_number_global)
        if q.needs_manual_review:
            needs_review_list.append(q.question_number_global)

    # Test readiness status calculation
    readiness = "Previewable"
    if dup_nums:
        readiness = "Not ready"
    elif missing_nums:
        readiness = "Not ready" if len(missing_nums) > 5 else "Needs review"
    elif len(fewer_than_4) > 5:
        readiness = "Needs review"
    elif len(questions_rows) < 40:
        readiness = "Not ready"
    # Add triage warnings count
    triage_warnings_total = sum(1 for q in questions_parsed if q.get('triage_warnings'))
    validation_log = {
        "expected_questions": 45,
        "detected_candidates": len(questions_rows),
        "missing_numbers": missing_nums,
        "duplicate_numbers": dup_nums,
        "fake_option_candidates": fake_option_candidates_count,
        "fewer_than_4_options": fewer_than_4,
        "with_diagrams": with_diagrams,
        "needs_review": needs_review_list,
        "triage_warnings_total": triage_warnings_total,
        "test_readiness": readiness
    }
    
    paper.solution_notes = json.dumps(validation_log)
    paper.expected_question_count = 45 # Set expected questions for Physics triage to 45
    db.commit()
    return paper.id

def _set_option_val(q: dict, opt_id: str, text: str):
    text = text.strip()
    mapping = {"1": "A", "2": "B", "3": "C", "4": "D", "A": "A", "B": "B", "C": "C", "D": "D"}
    key = mapping.get(opt_id)
    if key:
        q["options"][key] = text

def _parse_inline_options_dict(q: dict):
    text = q["question_text"]
    parts = re.split(r'\(([1-4A-Da-d])\)', text)
    if len(parts) > 1:
        q["question_text"] = parts[0].strip()
        for i in range(1, len(parts)-1, 2):
            _set_option_val(q, parts[i].upper(), parts[i+1])
    else:
        parts_dot = re.split(r'\b([1-4A-Da-d])\.\s+', text)
        if len(parts_dot) > 1:
            q["question_text"] = parts_dot[0].strip()
            for i in range(1, len(parts_dot)-1, 2):
                _set_option_val(q, parts_dot[i].upper(), parts_dot[i+1])

def _parse_inline_options_dict_raw(q: dict, text: str):
    parts = re.split(r'\(([1-4A-Da-d])\)', text)
    if len(parts) > 1:
        for i in range(1, len(parts)-1, 2):
            _set_option_val(q, parts[i].upper(), parts[i+1])
    else:
        parts_dot = re.split(r'\b([1-4A-Da-d])\.\s+', text)
        if len(parts_dot) > 1:
            for i in range(1, len(parts_dot)-1, 2):
                _set_option_val(q, parts_dot[i].upper(), parts_dot[i+1])
