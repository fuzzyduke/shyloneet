import sys
import os
import shutil

# Copy DB for testing
db_path = r"neetvault.db"
test_db_path = r"test_vault.db"
os.chdir(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")
shutil.copy(db_path, test_db_path)

# Update database URL
os.environ["DATABASE_URL"] = "sqlite:///./test_vault.db"
sys.path.append(r"C:\Users\edsel\.gemini\antigravity-ide\scratch\shyloneet\backend")
import database
database.DATABASE_URL = "sqlite:///./test_vault.db"
database.engine = database.create_engine(database.DATABASE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = database.sessionmaker(autocommit=False, autoflush=False, bind=database.engine)

os.environ["DATABASE_URL"] = "sqlite:///./test_vault.db"

from database import SessionLocal
import models
from main import (
    get_review_summary, get_review_queue, approve_question_mapping,
    update_question_mapping, mark_bad_extraction, generate_test, get_chapters,
    TestGenerationRequest, UpdateMappingRequest, app
)
from fastapi.testclient import TestClient

client = TestClient(app)

def test_api():
    db = SessionLocal()
    try:
        print("=== 1. Review Queue ===")
        queue = get_review_queue(db)
        print(f"Auto Approved: {len(queue['auto_approved'])}")
        assert len(queue['auto_approved']) == 13
        
        # Test missing endpoint GET /api/admin/questions/{question_id}
        # If not implemented, we will add it. Let's hit it via client to see.
        resp = client.get("/api/admin/questions/some_id")
        if resp.status_code == 404 and "Not Found" in resp.text:
            print("WARNING: GET /api/admin/questions/{question_id} not implemented yet.")
        
        print("=== 2. Chapters Boundary ===")
        chaps = get_chapters(exam_program_id="NEET", subject="Physics", source="NCERT", class_level=12, db=db)
        print(f"Returned chapters count: {len(chaps)}")
        # If the endpoint doesn't filter by exam_program_id, we need to fix it.
        # Actually main.py doesn't have exam_program_id filter in get_chapters!
        
        print("=== 3. DB Mutation ===")
        q = queue['mandatory_review'][0]
        qid = q['question']['id']
        mid = q['mapping']['mapping_id']
        print(f"Testing mutations on Question ID: {qid}")
        
        # 3.1 Approve Mapping
        res = approve_question_mapping(qid, db)
        assert res["status"] == "approved"
        db.commit()
        
        # Verify db state
        m = db.query(models.QuestionChapterMap).filter_by(id=mid).first()
        assert m.approved_by_admin == True
        assert m.needs_manual_review == False
        
        # 3.2 Update Mapping
        primary_ch = db.query(models.Chapter).first().id
        sec_ch = db.query(models.Chapter).offset(1).first().id
        req = UpdateMappingRequest(primary_chapter_id=primary_ch, secondary_chapter_ids=[sec_ch])
        update_question_mapping(qid, req, db)
        
        m_new = db.query(models.QuestionChapterMap).filter_by(question_id=qid).all()
        assert len(m_new) == 2
        primaries = [x for x in m_new if x.is_primary]
        secondaries = [x for x in m_new if not x.is_primary]
        assert len(primaries) == 1
        assert len(secondaries) == 1
        assert primaries[0].mapping_method == "manual_admin"
        assert secondaries[0].mapping_method == "manual_admin"
        
        # 3.3 Mark bad extraction
        unmapped_q = queue['unmapped'][0]['question']['id']
        mark_bad_extraction(unmapped_q, db)
        unq = db.query(models.Question).filter_by(id=unmapped_q).first()
        assert unq.extraction_status == "bad_extraction"
        
        print("=== 4. Student API Safety ===")
        test_req = TestGenerationRequest(subject="Physics", chapter_ids=[primary_ch])
        test_qs = generate_test(test_req, db)
        for tq in test_qs:
            db_q = db.query(models.Question).filter_by(id=tq['id']).first()
            assert db_q.is_mock == False
            assert db_q.extraction_status == "success"
            
        print("All backend tests passed!")
    finally:
        db.close()
        
if __name__ == "__main__":
    test_api()
