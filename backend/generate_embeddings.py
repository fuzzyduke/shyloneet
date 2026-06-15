import os
import json
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ChapterChunk

def run_embeddings():
    print("Loading sentence-transformers...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Please wait for sentence-transformers to finish installing.")
        return
        
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    db = SessionLocal()
    
    # Get all chunks that need embeddings or have the placeholder "[]"
    chunks = db.query(ChapterChunk).filter(
        (ChapterChunk.embedding == None) | (ChapterChunk.embedding == "[]")
    ).all()
    
    total = len(chunks)
    print(f"Found {total} chunks needing embeddings.")
    
    if total == 0:
        return
        
    batch_size = 256
    start_time = time.time()
    
    for i in range(0, total, batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c.chunk_text for c in batch]
        
        print(f"Generating embeddings for batch {i} to {i+len(batch)}...")
        embeddings = model.encode(texts, convert_to_numpy=True)
        
        for j, chunk in enumerate(batch):
            emb_list = embeddings[j].tolist()
            chunk.embedding = json.dumps(emb_list)
            
        db.commit()
        
    elapsed = time.time() - start_time
    print(f"Finished generating {total} embeddings in {elapsed:.1f} seconds.")
    db.close()

if __name__ == "__main__":
    run_embeddings()
