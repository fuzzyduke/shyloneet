import sqlite3

conn = sqlite3.connect('backend/neetvault.db')
cur = conn.cursor()
cur.execute("SELECT id FROM chapters WHERE subject='Physics' AND class_level=11 AND chapter_number=1")
res = cur.fetchone()
if res:
    chapter_id = res[0]
    print("Chapter ID:", chapter_id)
    cur.execute("SELECT image_url FROM chapter_assets WHERE chapter_id=?", (chapter_id,))
    images = cur.fetchall()
    print("Images:", images)
else:
    print("Not found")
