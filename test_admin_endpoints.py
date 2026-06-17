import sys
import os

sys.path.append(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")

from database import SessionLocal
from main import get_review_summary, get_review_queue

def test_endpoints():
    db = SessionLocal()
    try:
        print("=== Review Summary ===")
        summary = get_review_summary(db)
        print(summary)
        
        print("\n=== Review Queue ===")
        queue = get_review_queue(db)
        print(f"Auto Approved: {len(queue['auto_approved'])}")
        print(f"Mandatory Review: {len(queue['mandatory_review'])}")
        print(f"Review Recommended: {len(queue['review_recommended'])}")
        print(f"Unmapped: {len(queue['unmapped'])}")
        print(f"Failed Extractions: {len(queue['failed_extractions'])}")
        
        # Validation checks
        assert summary['auto_approved'] == len(queue['auto_approved']), "Mismatch in auto_approved count"
        assert summary['mandatory_review'] == len(queue['mandatory_review']), "Mismatch in mandatory_review count"
        assert summary['review_recommended'] == len(queue['review_recommended']), "Mismatch in review_recommended count"
        assert summary['unmapped'] == len(queue['unmapped']), "Mismatch in unmapped count"
        assert summary['failed_extractions'] == len(queue['failed_extractions']), "Mismatch in failed count"
        
        print("\nSUCCESS: All endpoint logic executed without errors and counts matched!")
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
