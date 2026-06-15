import os
import glob
import fitz # PyMuPDF
import json
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import Chapter, ChapterChunk, ChapterAsset

# Create tables
Base.metadata.create_all(bind=engine)

def ingest_pdf(db: Session, filepath: str, subject: str = "Physics", class_level: int = 12):
    filename = os.path.basename(filepath)
    # Extract number from filename like leph101.pdf using regex
    import re
    match = re.search(r'\d+', filename)
    chapter_num = int(match.group()) if match else 0
    chapter_name = f"Chapter {chapter_num}"
    chapter_name = f"Chapter {chapter_num}"
    
    print(f"Processing {filename}...")
    
    # Check if chapter already exists
    chapter = db.query(Chapter).filter(Chapter.file_name == filename).first()
    if not chapter:
        chapter = Chapter(
            subject=subject,
            source="NCERT",
            class_level=class_level,
            chapter_number=chapter_num,
            chapter_name=chapter_name,
            file_name=filename
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
    
    # Open PDF
    doc = fitz.open(filepath)
    
    # Setup assets directory
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets', 'chapters', chapter.id)
    os.makedirs(assets_dir, exist_ok=True)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract text chunks
        # A simple approach: paragraph by paragraph
        blocks = page.get_text("blocks")
        for idx, block in enumerate(blocks):
            text = block[4].strip()
            if len(text) > 20: # Ignore very short artifacts
                chunk = ChapterChunk(
                    chapter_id=chapter.id,
                    page_number=page_num + 1,
                    chunk_text=text,
                    chunk_type="text",
                    embedding="[]" # Placeholder for embedding
                )
                db.add(chunk)
        
        # Extract images (diagrams)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Filter out tiny artifacts/icons
            if len(image_bytes) < 5000:
                continue
                
            image_filename = f"page_{page_num+1}_img_{img_index}.{image_ext}"
            image_path = os.path.join(assets_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
                
            asset = ChapterAsset(
                chapter_id=chapter.id,
                page_number=page_num + 1,
                asset_type="diagram",
                image_url=f"/data/assets/chapters/{chapter.id}/{image_filename}",
                caption=f"Image from page {page_num + 1}"
            )
            db.add(asset)
            
    db.commit()
    print(f"Finished processing {filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ingest_ncert.py <path_to_pdf_directory_or_file>")
        sys.exit(1)
        
    path = sys.argv[1]
    db = SessionLocal()
    
    if os.path.isdir(path):
        pdf_files = glob.glob(os.path.join(path, "*.pdf"))
        for pdf in pdf_files:
            ingest_pdf(db, pdf)
    elif os.path.isfile(path) and path.endswith('.pdf'):
        ingest_pdf(db, path)
    else:
        print("Invalid path provided.")
    
    db.close()
