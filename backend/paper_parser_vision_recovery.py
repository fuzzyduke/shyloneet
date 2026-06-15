import os
import re
import json
import base64
import requests
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import QuestionPaper, Question, QuestionAsset, FailedExtraction
import time

AGENT_ZERO_API_KEY = "sk-a0-jvjZaEPiDlpBJcj4Zk41eKS5owfpeVpzy0"
MODEL_NAME = "qwen-3-7-plus"

def robust_json_parse(content, paper_id, page_num, col_name, img_url, db):
    # Try to find JSON in markdown fences
    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        extracted = match.group(1)
    else:
        # Try generic fences
        match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            extracted = match.group(1)
        else:
            # As a last resort or to clean up, find everything between first { and last }
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                extracted = match.group(1)
            else:
                extracted = content
                
    try:
        return json.loads(extracted), "success"
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        # Log to failed_extractions
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


def recover_failed_columns(db: Session, exam_type="NEET", year=2024, paper_code="T3"):
    start_time = time.time()
    
    paper = db.query(QuestionPaper).filter(QuestionPaper.source_file == "2024 neet pw.pdf").first()
    if not paper:
        print("Paper not found")
        return
        
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets', 'papers', paper.id, 'columns')
    
    # Specific missing columns
    failed_columns = [
        "page_2_col_1", "page_4_col_1", "page_4_col_2", "page_6_col_2", "page_7_col_2", 
        "page_8_col_1", "page_8_col_2", "page_9_col_1", "page_9_col_2", "page_10_col_1", "page_10_col_2"
    ]
    
    physics_questions_recovered = 0
    
    for col_name in failed_columns:
        col_path = os.path.join(assets_dir, f"{col_name}.jpg")
        img_url = f"/data/assets/papers/{paper.id}/columns/{col_name}.jpg"
        if not os.path.exists(col_path):
            print(f"Missing image for {col_name}")
            continue
            
        print(f"Recovering {col_name}...")
        
        with open(col_path, "rb") as image_file:
            img_b64 = base64.b64encode(image_file.read()).decode('utf-8')
            
        time.sleep(3)
        
        page_match = re.search(r'page_(\d+)', col_name)
        page_num = int(page_match.group(1)) if page_match else 0
        
        result, req_status = call_vision_llm(img_b64, col_name, paper.id, page_num, img_url, db)
        
        if req_status != "success":
            print(f"  Still failed {col_name}")
            continue
            
        questions = result.get("questions", [])
        
        for q_data in questions:
            q_num = q_data.get("question_number")
            if not q_num or int(q_num) > 50:
                continue
                
            existing_q = db.query(Question).filter(
                Question.paper_id == paper.id,
                Question.question_number == int(q_num),
                Question.extraction_method == "vision_agentzero"
            ).first()
            
            if existing_q:
                print(f"    Q{q_num} already exists. Skipping duplicate.")
                continue
                
            print(f"    RECOVERED Q{q_num}!")
            
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
                source_pdf=paper.source_file,
                page_number=page_num,
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
                    image_url=img_url,
                    caption=q_data.get("diagram_description", "Diagram in column"),
                    page_number=page_num
                )
                db.add(asset)
                db.commit()
                
            physics_questions_recovered += 1

    print(f"Finished recovering {physics_questions_recovered} questions.")

if __name__ == "__main__":
    db = SessionLocal()
    recover_failed_columns(db)
    db.close()
