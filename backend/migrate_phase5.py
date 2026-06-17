import sqlite3

db_path = r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend\neetvault.db"

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Update question_papers table
    paper_columns = [
        "solution_status TEXT DEFAULT 'unavailable'",
        "scoring_enabled BOOLEAN DEFAULT 0",
        "scoring_source TEXT DEFAULT 'none'",
        "solution_confidence REAL",
        "solution_review_required BOOLEAN DEFAULT 0",
        "solution_notes TEXT",
        "answer_key_detected BOOLEAN DEFAULT 0",
        "answer_key_source_page INTEGER",
        "solution_extraction_method TEXT DEFAULT 'none'",
        "solution_last_verified_at DATETIME"
    ]
    for col in paper_columns:
        try:
            cursor.execute(f"ALTER TABLE question_papers ADD COLUMN {col};")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass
            else:
                raise e

    # 2. Update questions table
    question_columns = [
        "answer_status TEXT DEFAULT 'unavailable'",
        "solution_source TEXT DEFAULT 'none'",
        "solution_confidence REAL",
        "solution_needs_review BOOLEAN DEFAULT 0",
        "scoring_eligible BOOLEAN DEFAULT 0"
    ]
    for col in question_columns:
        try:
            cursor.execute(f"ALTER TABLE questions ADD COLUMN {col};")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass
            else:
                raise e

    # Backfill missing states
    cursor.execute("UPDATE question_papers SET solution_status = 'unavailable', scoring_enabled = 0, scoring_source = 'none', answer_key_detected = 0;")
    cursor.execute("UPDATE questions SET answer_status = 'unavailable', solution_source = 'none', scoring_eligible = 0;")

    conn.commit()
    conn.close()
    print("Migration complete. Added Solution and Scoring columns.")

if __name__ == "__main__":
    migrate()
