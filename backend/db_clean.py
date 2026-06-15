import sqlite3

def clean_db():
    conn = sqlite3.connect('neetvault.db')
    c = conn.cursor()
    
    # Clean up mock records
    c.execute("DELETE FROM questions WHERE paper_id IN (SELECT id FROM question_papers WHERE year=2024)")
    c.execute("DELETE FROM question_papers WHERE year=2024")
    
    # Add new provenance columns
    columns = [
        "source_type VARCHAR DEFAULT 'real_pdf_extraction'",
        "is_mock BOOLEAN DEFAULT 0",
        "extraction_method VARCHAR",
        "extraction_model VARCHAR",
        "extraction_status VARCHAR DEFAULT 'success'"
    ]
    
    for col in columns:
        try:
            c.execute(f"ALTER TABLE questions ADD COLUMN {col}")
            print(f"Added column: {col}")
        except Exception as e:
            print(f"Column may exist or error: {e}")
            
    conn.commit()
    conn.close()
    print("Database cleaned and schema updated.")

if __name__ == "__main__":
    clean_db()
