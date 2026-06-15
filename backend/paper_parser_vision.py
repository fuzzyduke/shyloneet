import os
import re
import fitz
import io
import json
import base64
import requests
from PIL import Image
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import QuestionPaper, Question, QuestionAsset, FailedExtraction
import time

AGENT_ZERO_API_KEY = "sk-a0-jvjZaEPiDlpBJcj4Zk41eKS5owfpeVpzy0"
MODEL_NAME = "qwen-3-7-plus"

def robust_json_parse(content, paper_id, page_num, col_name, img_url, db):
    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        extracted = match.group(1)
    else:
        match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            extracted = match.group(1)
        else:
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                extracted = match.group(1)
            else:
                extracted = content
                
    try:
        return json.loads(extracted), "success"
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        failed_entry = FailedExtraction(
            paper_id=paper_id,
            page_number=page_num,
            column_name=col_name,
            image_url=img_url,
            raw_response=content,
            parse_error=str(e),
            response_format_incompatible=True,
            review_status="pending"
        )
        db.add(failed_entry)
        db.commit()
        return {"questions": []}, "error"

def call_vision_llm(base64_image, column_name, paper_id, page_num, img_url, db):
    headers = {
        "Authorization": f"Bearer {AGENT_ZERO_API_KEY}",
        "Accept": "application/json"
    }
    
    system_prompt = """You are an expert OCR and data extraction system. You are extracting multiple-choice questions from a column of a Physics test booklet.
Extract ONLY the Physics questions. If there are no questions, return an empty list.
Return the output strictly in the following JSON format:
{
  "questions": [
    {
      "question_number": int,
      "question_text": "string",
      "option_1": "string",
      "option_2": "string",
      "option_3": "string",
      "option_4": "string",
      "has_diagram": boolean,
      "diagram_description": "string (or null if none)",
      "extraction_confidence": float (0.0 to 1.0),
      "uncertainty_notes": "string (or null if perfect)"
    }
  ]
}
If an option is completely missing, set it to null. If a diagram is clearly part of the question, set has_diagram to true and describe it.
Do NOT output any markdown blocks or extra text outside the JSON object."""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Here is the image of {column_name}. Extract the questions now. Output strictly JSON."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://llm.agent-zero.ai/v1/chat/completions", headers=headers, json=payload, timeout=180)
    except requests.exceptions.Timeout as e:
        print(f"Request timed out for {column_name}")
        failed_entry = FailedExtraction(
            paper_id=paper_id,
            page_number=page_num,
            column_name=column_name,
            image_url=img_url,
            raw_response="TIMEOUT",
            parse_error=str(e),
            extraction_incomplete=True,
            review_status="pending"
        )
        db.add(failed_entry)
        db.commit()
        return {"questions": []}, "timeout"
    except Exception as req_err:
        print(f"Request failed for {column_name}: {req_err}")
        return {"questions": []}, "error"
        
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        return robust_json_parse(content, paper_id, page_num, column_name, img_url, db)
    else:
        print(f"API Error {response.status_code}: {response.text}")
        return {"questions": []}, "error"


def parse_paper_vision(filepath: str, db: Session, exam_type="NEET", year=2024, paper_code="T3"):
    start_time = time.time()
    stats = {
        "request_count": 0,
        "timeout_count": 0,
        "error_count": 0,
        "total_duration": 0
    }
    
    filename = os.path.basename(filepath)
    
    paper = db.query(QuestionPaper).filter(QuestionPaper.source_file == filename).first()
    if not paper:
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
    else:
        # Clean up existing vision extractions for this paper to avoid duplicates
        existing_qs = db.query(Question).filter(Question.paper_id == paper.id, Question.extraction_method == "vision_agentzero").all()
        for q in existing_qs:
            db.query(QuestionAsset).filter(QuestionAsset.question_id == q.id).delete()
            db.delete(q)
        db.commit()
        print(f"Cleaned up {len(existing_qs)} previous extractions for fresh start.")
        
    doc = fitz.open(filepath)
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets', 'papers', paper.id, 'columns')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Render at 150 DPI for real extraction (good balance of quality and size)
    zoom = 150 / 72
    mat = fitz.Matrix(zoom, zoom)
    
    physics_questions_processed = 0
    
    # Process pages 1 through 9 (inclusive) -> covers pages 2 to 10 of PDF where physics lives
    for page_num in range(1, 10):
        if physics_questions_processed >= 50:
            break
            
        print(f"Processing Page {page_num + 1}...")
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        width, height = img.size
        left_crop = img.crop((0, 0, width // 2, height))
        right_crop = img.crop((width // 2, 0, width, height))
        
        for col_idx, col_img in enumerate([left_crop, right_crop]):
            if physics_questions_processed >= 50:
                break
                
            col_name = f"page_{page_num+1}_col_{col_idx+1}"
            col_path = os.path.join(assets_dir, f"{col_name}.jpg")
            
            col_img = col_img.convert("RGB")
            col_img.save(col_path, format="JPEG", quality=85)
            
            buffered = io.BytesIO()
            col_img.save(buffered, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            print(f"  Sending {col_name} to Vision LLM... (Base64 size: {len(img_b64) / 1024:.2f} KB)")
            
            # Rate limit backoff
            time.sleep(3)
            
            stats["request_count"] += 1
            img_url = f"/data/assets/papers/{paper.id}/columns/{col_name}.jpg"
            result, req_status = call_vision_llm(img_b64, col_name, paper.id, page_num + 1, img_url, db)
            
            if req_status == "timeout":
                stats["timeout_count"] += 1
                continue
            elif req_status == "error":
                stats["error_count"] += 1
                continue
                
            questions = result.get("questions", [])
            
            for q_data in questions:
                q_num = q_data.get("question_number")
                if not q_num or int(q_num) > 50:
                    continue # Skip chemistry/biology
                    
                print(f"    Extracted Q{q_num}")
                
                needs_review = False
                flags = []
                if not q_data.get("option_1") or not q_data.get("option_4"):
                    needs_review = True
                    flags.append("missing_options")
                if q_data.get("uncertainty_notes"):
                    needs_review = True
                    flags.append("instruction_contamination")
                    
                q_model = Question(
                    paper_id=paper.id,
                    year=year,
                    exam_type=exam_type,
                    paper_code=paper_code,
                    subject="Physics",
                    question_number=int(q_num),
                    question_text=q_data.get("question_text", ""),
                    option_a=q_data.get("option_1"),
                    option_b=q_data.get("option_2"),
                    option_c=q_data.get("option_3"),
                    option_d=q_data.get("option_4"),
                    source_pdf=filename,
                    page_number=page_num + 1,
                    extraction_confidence=q_data.get("extraction_confidence", 1.0),
                    needs_manual_review=needs_review,
                    source_type="real_pdf_extraction",
                    is_mock=False,
                    extraction_method="vision_agentzero",
                    extraction_model=MODEL_NAME,
                    extraction_status="needs_review" if needs_review else "success",
                    exam_program_id="NEET",
                    incompatibility_flags=json.dumps(flags) if flags else None
                )
                db.add(q_model)
                db.commit()
                db.refresh(q_model)
                
                if q_data.get("has_diagram"):
                    asset = QuestionAsset(
                        question_id=q_model.id,
                        asset_type="diagram_referenced",
                        image_url=f"/data/assets/papers/{paper.id}/columns/{col_name}.jpg",
                        caption=q_data.get("diagram_description", "Diagram in column"),
                        page_number=page_num + 1
                    )
                    db.add(asset)
                    db.commit()
                    
                physics_questions_processed += 1

    stats["total_duration"] = time.time() - start_time
    paper.upload_status = "completed"
    paper.processing_status = "completed"
    db.commit()
    
    # Write stats to file for report generator
    with open(os.path.join(os.path.dirname(__file__), "run_stats.json"), "w") as f:
        json.dump(stats, f)
        
    print(f"Finished extracting {physics_questions_processed} questions. Stats saved.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python paper_parser_vision.py <path_to_paper_pdf>")
        sys.exit(1)
    
    path = sys.argv[1]
    db = SessionLocal()
    parse_paper_vision(path, db)
    db.close()
