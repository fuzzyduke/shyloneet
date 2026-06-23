import sqlite3

conn = sqlite3.connect('backend/neetvault.db')
cur = conn.cursor()
cur.execute("SELECT chunk_text FROM chapter_chunks WHERE chapter_id='ce85af06-5a44-4c1e-8750-ebc7d4ffbcd1' LIMIT 5")
print(cur.fetchall())
