import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neetvault.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Alter QuestionPaper
    try:
        c.execute("ALTER TABLE question_papers ADD COLUMN paper_type VARCHAR")
        c.execute("ALTER TABLE question_papers ADD COLUMN expected_question_count INTEGER DEFAULT 180")
        c.execute("ALTER TABLE question_papers ADD COLUMN subjects_included VARCHAR")
        c.execute("ALTER TABLE question_papers ADD COLUMN import_status VARCHAR DEFAULT 'draft'")
        print("QuestionPaper altered successfully.")
    except sqlite3.OperationalError as e:
        print("QuestionPaper columns might already exist:", e)

    # Alter Question
    try:
        c.execute("ALTER TABLE questions ADD COLUMN question_number_global INTEGER")
        c.execute("ALTER TABLE questions ADD COLUMN question_number_subject INTEGER")
        c.execute("ALTER TABLE questions ADD COLUMN publish_status VARCHAR DEFAULT 'draft'")
        c.execute("ALTER TABLE questions ADD COLUMN correct_option VARCHAR")
        print("Question altered successfully.")
    except sqlite3.OperationalError as e:
        print("Question columns might already exist:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
