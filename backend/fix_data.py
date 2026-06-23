import os
import sqlite3
import fitz
from ncert_chapter_map import parse_ncert_filename, get_chapter_name

# The known locations of the PDFs based on the user's ingestion commands
PDF_DIRS = [
    r"C:\Users\graci\Documents\projectschaos\shylo\pdfs\physics",
    r"C:\Users\graci\Documents\projectschaos\shylo\pdfs\chemistry",
    r"C:\Users\graci\Documents\projectschaos\shylo\pdfs\biology"
]

def find_pdf_path(filename):
    for d in PDF_DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None

def fix_chapters():
    db_path = os.path.join(os.path.dirname(__file__), 'neetvault.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT id, file_name FROM chapters")
    chapters = cur.fetchall()
    
    for row in chapters:
        chapter_id, filename = row
        parsed = parse_ncert_filename(filename)
        if not parsed:
            continue
            
        subject, class_level, chapter_number, _ = parsed
        chapter_name = get_chapter_name(subject, class_level, chapter_number)
        
        # 1. Update the database record with the CORRECT class and chapter numbers
        print(f"Updating DB for {filename} -> Class {class_level}, Ch {chapter_number}: {chapter_name}")
        cur.execute("""
            UPDATE chapters 
            SET class_level=?, chapter_number=?, chapter_name=?, subject=?
            WHERE id=?
        """, (class_level, chapter_number, chapter_name, subject, chapter_id))
        
        # 2. Re-extract images correctly
        pdf_path = find_pdf_path(filename)
        if not pdf_path:
            print(f"  [WARN] PDF not found for {filename}, skipping image re-extraction.")
            continue
            
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "data", "assets", "chapters", chapter_id)
        os.makedirs(assets_dir, exist_ok=True)
        
        # Delete old assets in DB and filesystem
        cur.execute("DELETE FROM chapter_assets WHERE chapter_id=?", (chapter_id,))
        for f in os.listdir(assets_dir):
            try:
                os.remove(os.path.join(assets_dir, f))
            except Exception:
                pass
                
        doc = fitz.open(pdf_path)
        images_saved = 0
        seen_xrefs = set()
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    image_bytes = pix.tobytes("png")
                    image_ext = "png"
                    pix = None
                except Exception as e:
                    print(f"    [WARN] Could not extract image xref {xref} on page {page_num + 1}: {e}")
                    continue
                    
                if len(image_bytes) < 5000:
                    continue
                    
                import uuid
                asset_id = str(uuid.uuid4())
                image_filename = f"page_{page_num + 1}_img_{img_index}.{image_ext}"
                image_path = os.path.join(assets_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                    
                cur.execute("""
                    INSERT INTO chapter_assets (id, chapter_id, page_number, asset_type, image_url, caption)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    asset_id,
                    chapter_id,
                    page_num + 1,
                    "diagram",
                    f"/data/assets/chapters/{chapter_id}/{image_filename}",
                    f"Image from page {page_num + 1}"
                ))
                images_saved += 1
                
        doc.close()
        print(f"  Re-extracted {images_saved} images correctly.")
        
    conn.commit()
    conn.close()
    print("Done fixing database and images.")

if __name__ == "__main__":
    fix_chapters()
