import json

mock_json = {
    "paper": {
        "title": "NEET 2025 Paper Set F1",
        "exam": "NEET",
        "year": 2025,
        "set_code": "F1",
        "source": "PW",
        "paper_type": "questions_with_options_and_answer_key",
        "expected_question_count": 180,
        "subjects": ["Physics", "Chemistry", "Biology"]
    },
    "summary": {
        "expected": 180,
        "parsed": 180,
        "missing_questions": [],
        "needs_review": 10
    },
    "questions": []
}

for i in range(1, 181):
    subject = "Physics" if i <= 45 else ("Chemistry" if i <= 90 else "Biology")
    q_subject = i if i <= 45 else (i - 45 if i <= 90 else i - 90)
    
    q = {
        "question_number_global": i,
        "subject": subject,
        "question_number_subject": q_subject,
        "question_text": f"This is a mock question {i} for {subject}.",
        "options": {
            "A": f"Option A for {i}",
            "B": f"Option B for {i}",
            "C": f"Option C for {i}",
            "D": f"Option D for {i}"
        },
        "correct_option": "A",
        "solution_text": None,
        "source_page": (i // 10) + 1,
        "assets": [],
        "parse_confidence": 0.95,
        "needs_review": i % 18 == 0,
        "review_reasons": ["Low confidence"] if i % 18 == 0 else [],
        "extraction_method": "mock"
    }
    mock_json["questions"].append(q)

with open("paper_triage_mock.json", "w", encoding="utf-8") as f:
    json.dump(mock_json, f, indent=2)

print("Mock JSON written.")
