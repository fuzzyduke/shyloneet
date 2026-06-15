import sqlite3
import json
import collections

db_path = "neetvault.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def run_query(query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()

def single_val(query, params=()):
    cursor.execute(query, params)
    res = cursor.fetchone()
    return res[0] if res else None

# 1. Total records in questions table for the 2024 NEET Physics paper.
q1 = single_val("SELECT count(*) FROM questions WHERE exam_program_id='NEET' AND year=2024 AND subject='Physics'")

# 2. Count of unique question_number values.
q2 = single_val("SELECT count(DISTINCT question_number) FROM questions WHERE exam_program_id='NEET' AND year=2024 AND subject='Physics'")

# 3. List of all question_number values currently present.
all_q_rows = run_query("SELECT question_number FROM questions WHERE exam_program_id='NEET' AND year=2024 AND subject='Physics' ORDER BY question_number ASC")
q3 = [row["question_number"] for row in all_q_rows]

# 4. Any duplicate question numbers.
counter = collections.Counter(q3)
q4 = [k for k, v in counter.items() if v > 1]

# 5. Any question numbers outside expected Physics range 1–50.
q5 = [k for k in q3 if k < 1 or k > 50]

# 6. Any records where subject is not Physics.
q6 = single_val("SELECT count(*) FROM questions WHERE exam_program_id='NEET' AND year=2024 AND subject != 'Physics'")

# 7. Any records where source_type is not real_pdf_extraction.
q7 = run_query("SELECT id, source_type, question_number FROM questions WHERE exam_program_id='NEET' AND year=2024 AND source_type != 'real_pdf_extraction'")

# 8. Any records where is_mock = true.
q8 = run_query("SELECT id, question_number FROM questions WHERE exam_program_id='NEET' AND year=2024 AND is_mock = 1")

# 9. Any records with extraction_status not in success/clean/approved equivalent.
q9 = run_query("SELECT id, extraction_status, question_number FROM questions WHERE exam_program_id='NEET' AND year=2024 AND extraction_status NOT IN ('success', 'clean', 'approved', 'mock_validation_only')")

# 10. Total records in question_chapter_map.
q10 = single_val("SELECT count(*) FROM question_chapter_map")

# 11. Whether 58 refers to unique questions, mappings, primary+secondary, duplicates, etc.
mappings_by_method = run_query("SELECT mapping_method, count(*) as c FROM question_chapter_map GROUP BY mapping_method")
total_mappings = sum([row["c"] for row in mappings_by_method])
unique_mapped_questions = single_val("SELECT count(DISTINCT question_id) FROM question_chapter_map")

auto_approved_rows = run_query("""
    SELECT q.question_number, q.id 
    FROM questions q 
    JOIN question_chapter_map m ON q.id = m.question_id 
    WHERE m.needs_manual_review = 0 AND m.mapping_method LIKE 'llm%' AND q.subject='Physics'
    GROUP BY q.id
""")
auto_approved = [r["question_number"] for r in auto_approved_rows]

mandatory_rows = run_query("""
    SELECT q.question_number, q.id 
    FROM questions q 
    JOIN question_chapter_map m ON q.id = m.question_id 
    WHERE (m.mapping_method = 'embedding_fallback' OR m.needs_manual_review = 1) AND q.subject='Physics'
    GROUP BY q.id
""")
mandatory_review = [r["question_number"] for r in mandatory_rows]

output = {
    "1_total_physics_questions": q1,
    "2_unique_question_numbers": q2,
    "3_all_question_numbers": q3,
    "4_duplicate_question_numbers": q4,
    "5_out_of_range_question_numbers": q5,
    "6_non_physics_count": q6,
    "7_non_real_pdf_extraction": [dict(r) for r in q7],
    "8_is_mock": [dict(r) for r in q8],
    "9_non_success_status": [dict(r) for r in q9],
    "10_total_mappings": q10,
    "11_mappings_by_method": [dict(r) for r in mappings_by_method],
    "11_unique_mapped_questions": unique_mapped_questions,
    "auto_approved_q_nums": auto_approved,
    "mandatory_review_q_nums": mandatory_review
}

print(json.dumps(output, indent=2))
