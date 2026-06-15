import sqlite3

def run_migration():
    conn = sqlite3.connect('neetvault.db')
    c = conn.cursor()
    
    print("Creating failed_extractions table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS failed_extractions (
            id VARCHAR PRIMARY KEY,
            paper_id VARCHAR,
            page_number INTEGER,
            column_name VARCHAR,
            image_url VARCHAR,
            raw_response TEXT,
            parse_error TEXT,
            review_status VARCHAR DEFAULT 'pending',
            response_format_incompatible BOOLEAN DEFAULT 0,
            schema_incompatible BOOLEAN DEFAULT 0,
            extraction_incomplete BOOLEAN DEFAULT 0,
            instruction_contamination BOOLEAN DEFAULT 0,
            missing_options BOOLEAN DEFAULT 0,
            duplicate_question_number BOOLEAN DEFAULT 0,
            missing_question_number BOOLEAN DEFAULT 0,
            diagram_asset_missing BOOLEAN DEFAULT 0,
            curriculum_boundary_violation BOOLEAN DEFAULT 0,
            subject_boundary_violation BOOLEAN DEFAULT 0,
            low_confidence_mapping BOOLEAN DEFAULT 0,
            embedding_llm_disagreement BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(paper_id) REFERENCES question_papers(id)
        )
    """)
    
    print("Migrating questions table...")
    try:
        c.execute("ALTER TABLE questions ADD COLUMN incompatibility_flags VARCHAR")
    except sqlite3.OperationalError as e:
        print(f"questions column error: {e}")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
