import sqlite3
import os
from ncert_chapter_map import parse_ncert_filename, get_chapter_name

def fix_database_titles():
    db_path = "neetvault.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, file_name, subject, class_level, chapter_number, chapter_name FROM chapters")
    chapters = cursor.fetchall()
    
    updated_count = 0
    for ch in chapters:
        ch_id = ch["id"]
        file_name = ch["file_name"]
        
        parsed = parse_ncert_filename(file_name)
        if not parsed:
            continue
            
        subject, class_level, correct_chapter_number, raw_code = parsed
        correct_chapter_name = get_chapter_name(subject, class_level, correct_chapter_number)
        
        # Check if anything changed
        if ch["chapter_number"] != correct_chapter_number or ch["chapter_name"] != correct_chapter_name:
            print(f"Updating {file_name}: Ch {ch['chapter_number']} '{ch['chapter_name']}' -> Ch {correct_chapter_number} '{correct_chapter_name}'")
            cursor.execute("""
                UPDATE chapters 
                SET chapter_number = ?, chapter_name = ?
                WHERE id = ?
            """, (correct_chapter_number, correct_chapter_name, ch_id))
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f"Fixed {updated_count} chapters successfully.")

if __name__ == "__main__":
    fix_database_titles()
