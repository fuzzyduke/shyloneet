import sqlite3
conn = sqlite3.connect('neetvault.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM questions WHERE extraction_method='vision_agentzero'")
print('Inserted questions:', c.fetchone()[0])
conn.close()
