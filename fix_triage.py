import json
import re

with open("paper_triage.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("parsed_answers.json", "r", encoding="utf-8") as f:
    answers = json.load(f)

questions_by_num = {}

for q in data["questions"]:
    q_num = q["question_number"]
    if q_num not in questions_by_num:
        questions_by_num[q_num] = []
    questions_by_num[q_num].append(q)

new_questions = []

for q_num in range(1, 46):
    if q_num not in questions_by_num:
        continue
    chunks = questions_by_num[q_num]
    
    # Combine all raw text
    combined_raw_text = "\n".join(chunk["raw_text"] for chunk in chunks)
    
    # We will try to parse out the question text and options 1, 2, 3, 4
    # A simple regex to find options
    # Often options look like "1. ", "2. ", "3. ", "4. " or "(1)", "(2)"
    # We can split the text based on these.
    
    options = {"1": "", "2": "", "3": "", "4": ""}
    question_text = combined_raw_text
    
    # Attempt to split out options if they exist
    # Let's find indices of (1), (2), (3), (4) or 1., 2., 3., 4.
    
    # We'll use a very basic heuristic: just provide the combined text and let the user review it,
    # because trying to reliably parse two-column PDF text with regex is why it failed in the first place!
    # But let's try to extract at least something.
    for chunk in chunks:
        for k, v in chunk["options"].items():
            if v and not options[k]:
                options[k] = v
                
    has_diagram = any(c.get("has_diagram") for c in chunks)
    diagram_url = next((c.get("diagram_url") for c in chunks if c.get("diagram_url")), None)
    
    ans = ""
    if str(q_num) in answers:
        ans = answers[str(q_num)][0]
        
    new_q = {
        "id": chunks[0]["id"],
        "question_number": q_num,
        "question_text": combined_raw_text,
        "options": options,
        "answer": ans,
        "has_diagram": has_diagram,
        "diagram_url": diagram_url,
        "page_number": chunks[0]["page_number"],
        "needs_review": True,
        "review_reasons": ["Auto-merged from fragments"]
    }
    new_questions.append(new_q)

data["questions"] = new_questions
data["stats"]["total_parsed"] = len(new_questions)

with open("paper_triage_fixed.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Fixed JSON written to paper_triage_fixed.json")
