import fitz
import sys

pdf_path = r"C:\Users\edsel\OneDrive\Pictures\hackinga0\neet 2020_2025\2024 neet pw.pdf"
try:
    doc = fitz.open(pdf_path)
    for i in range(1, 4):
        page = doc.load_page(i)
        print(f"\n--- PAGE {i+1} ---")
        text = page.get_text()
        print(text[:1500].encode('ascii', 'ignore').decode('ascii'))
except Exception as e:
    print(f"Error: {e}")
