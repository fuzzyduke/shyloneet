import sqlite3

def run_migration():
    conn = sqlite3.connect('neetvault.db')
    c = conn.cursor()
    
    print("Migrating chapters table...")
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN exam_program_id VARCHAR")
        c.execute("ALTER TABLE chapters ADD COLUMN source_type VARCHAR DEFAULT 'reference_book'")
        c.execute("ALTER TABLE chapters ADD COLUMN source_name VARCHAR")
        c.execute("ALTER TABLE chapters ADD COLUMN year INTEGER")
        c.execute("ALTER TABLE chapters ADD COLUMN paper_code VARCHAR")
        c.execute("CREATE INDEX ix_chapters_exam_program_id ON chapters(exam_program_id)")
    except sqlite3.OperationalError as e:
        print(f"chapters column error: {e}")

    print("Migrating question_papers table...")
    try:
        c.execute("ALTER TABLE question_papers ADD COLUMN exam_program_id VARCHAR")
        c.execute("ALTER TABLE question_papers ADD COLUMN source_type VARCHAR DEFAULT 'question_paper'")
        c.execute("ALTER TABLE question_papers ADD COLUMN source_name VARCHAR")
        c.execute("ALTER TABLE question_papers ADD COLUMN subject VARCHAR")
        c.execute("ALTER TABLE question_papers ADD COLUMN class_level INTEGER")
        c.execute("CREATE INDEX ix_question_papers_exam_program_id ON question_papers(exam_program_id)")
    except sqlite3.OperationalError as e:
        print(f"question_papers column error: {e}")
        
    print("Migrating questions table...")
    try:
        c.execute("ALTER TABLE questions ADD COLUMN exam_program_id VARCHAR")
        c.execute("CREATE INDEX ix_questions_exam_program_id ON questions(exam_program_id)")
    except sqlite3.OperationalError as e:
        print(f"questions column error: {e}")

    print("Creating curriculum_bridges table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS curriculum_bridges (
            id VARCHAR PRIMARY KEY,
            source_exam_program_id VARCHAR,
            target_exam_program_id VARCHAR,
            source_chapter_id VARCHAR,
            target_chapter_id VARCHAR,
            topic_name VARCHAR,
            similarity_score FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_chapter_id) REFERENCES chapters(id),
            FOREIGN KEY(target_chapter_id) REFERENCES chapters(id)
        )
    """)
    try:
        c.execute("CREATE INDEX ix_curriculum_bridges_source_exam_program_id ON curriculum_bridges(source_exam_program_id)")
        c.execute("CREATE INDEX ix_curriculum_bridges_target_exam_program_id ON curriculum_bridges(target_exam_program_id)")
    except sqlite3.OperationalError:
        pass

    # Update legacy data so it isn't orphaned
    print("Backfilling legacy data with 'NEET' exam_program_id...")
    c.execute("UPDATE chapters SET exam_program_id = 'NEET', source_name = 'NCERT' WHERE exam_program_id IS NULL")
    c.execute("UPDATE question_papers SET exam_program_id = 'NEET', source_name = 'NTA' WHERE exam_program_id IS NULL")
    c.execute("UPDATE questions SET exam_program_id = 'NEET' WHERE exam_program_id IS NULL")
    
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
