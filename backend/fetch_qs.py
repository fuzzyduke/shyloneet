import sqlite3
conn = sqlite3.connect('neetvault.db')
c = conn.cursor()
c.execute("SELECT question_number, question_text, option_a, option_b, option_c, option_d FROM questions WHERE extraction_method='vision_agentzero'")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()
