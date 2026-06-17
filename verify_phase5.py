import sys
import os

sys.path.append(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")

from database import SessionLocal
from main import generate_test, TestGenerationRequest

def verify():
    db = SessionLocal()
    
    # Simulate a request without a specific paper (just chapter IDs)
    # The NEET 2024 paper is marked as unavailable, so scoring should be disabled.
    req = TestGenerationRequest(
        subject="Physics",
        chapter_ids=[],
        paper_id=None,
        question_count=180
    )
    
    result = generate_test(req, db)
    
    print(f"Scoring Mode: {result['scoring_mode']}")
    print(f"Scoring Enabled: {result['scoring_enabled']}")
    print(f"Solution Status: {result['solution_status']}")
    print(f"Disabled Controls: {result['disabled_controls']}")
    print(f"Questions Returned: {len(result['questions'])}")
    
    if result['scoring_mode'] == 'unscored' and result['scoring_enabled'] == False:
        print("SUCCESS: generate_test correctly identified the test as unscored.")
    else:
        print("ERROR: generate_test failed to enforce unscored mode.")

if __name__ == "__main__":
    verify()
