import os
import shutil
from database import SessionLocal
from models import Chapter, ChapterChunk, ChapterAsset

db = SessionLocal()

CHAPTER_MAP = {
    "leph101.pdf": (1, "Electric Charges and Fields"),
    "leph102.pdf": (2, "Electrostatic Potential and Capacitance"),
    "leph103.pdf": (3, "Current Electricity"),
    "leph104.pdf": (4, "Moving Charges and Magnetism"),
    "leph105.pdf": (5, "Magnetism and Matter"),
    "leph106.pdf": (6, "Electromagnetic Induction"),
    "leph107.pdf": (7, "Alternating Current"),
    "leph108.pdf": (8, "Electromagnetic Waves"),
    "leph201.pdf": (9, "Ray Optics and Optical Instruments"),
    "leph202.pdf": (10, "Wave Optics"),
    "leph203.pdf": (11, "Dual Nature of Radiation and Matter"),
    "leph204.pdf": (12, "Atoms"),
    "leph205.pdf": (13, "Nuclei"),
    "leph206.pdf": (14, "Semiconductor Electronics")
}

FILES_TO_DELETE = ["leph1an.pdf", "leph2an.pdf", "leph1ps.pdf", "leph2ps.pdf"]

# 1. Delete the 4 non-chapter files
for f in FILES_TO_DELETE:
    chapter = db.query(Chapter).filter(Chapter.file_name == f).first()
    if chapter:
        # Delete chunks
        db.query(ChapterChunk).filter(ChapterChunk.chapter_id == chapter.id).delete()
        # Delete assets
        db.query(ChapterAsset).filter(ChapterAsset.chapter_id == chapter.id).delete()
        
        # Remove asset directory
        asset_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets', 'chapters', chapter.id)
        if os.path.exists(asset_dir):
            shutil.rmtree(asset_dir)
            
        # Delete chapter
        db.delete(chapter)

db.commit()

# 2. Update the 14 valid files with correct numbers and names
chapters = db.query(Chapter).all()
for c in chapters:
    if c.file_name in CHAPTER_MAP:
        num, name = CHAPTER_MAP[c.file_name]
        c.chapter_number = num
        c.chapter_name = name

db.commit()
db.close()
print("Database fixed!")
