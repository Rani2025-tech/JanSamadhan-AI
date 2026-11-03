import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Complaint
from ai.duplicates import check_duplicate_complaint

def test_cross_language_duplicates():
    # In-memory SQLite session for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Existing complaint filed in Odia
    odia_complaint = Complaint(
        id="GRV-TEST-ODIA-101",
        title="ୱାର୍ଡ ୭ ବ୍ରହ୍ମପୁରରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି",
        description="ୱାର୍ଡ ୭ ବ୍ରହ୍ମପୁରରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି ଏବଂ କାଦୁଅ ପାଣି ବାହାରୁଛି",
        category="Water Supply",
        sub_category="Pipeline Leakage",
        department="PHED",
        urgency="Critical",
        sentiment="Distressed",
        status="Submitted",
        district="Ganjam",
        area="Ward 7, Berhampur",
        language="Odia",
        user_id="user-citizen-1",
        submitted_date="28 Oct 2026",
        expected_date="05 Nov 2026",
        days_remaining=2
    )
    db.add(odia_complaint)
    db.commit()

    # 2. New incoming complaint in Hindi describing the exact same issue in the same ward
    hindi_text = "वार्ड 7 ब्रह्मपुर में पीने के पानी का पाइप फूट गया है और गंदा पानी आ रहा है"
    
    result = check_duplicate_complaint(
        new_text=hindi_text,
        district="Ganjam",
        category="Water Supply",
        db=db,
        threshold=0.55
    )

    print("\n--- Cross-Language Duplicate Detection Test ---")
    print(f"Odia Complaint:  {odia_complaint.description}")
    print(f"Hindi Complaint: {hindi_text}")
    print(f"Is Duplicate:    {result['is_duplicate']}")
    print(f"Confidence:      {result['confidence']}")
    print(f"Matched ID:      {result['matched_complaint_id']}")
    print(f"Message:         {result['message']}")

    assert result["is_duplicate"] is True, f"Expected duplicate to be True, got {result}"
    assert result["matched_complaint_id"] == "GRV-TEST-ODIA-101"
    assert result["confidence"] >= 0.55

    # 3. Non-duplicate test: Road pothole in different ward
    non_dup_text = "वार्ड 12 में सड़क पर गड्ढे हैं और गाड़ियां दुर्घटनाग्रस्त हो रही हैं"
    non_dup_res = check_duplicate_complaint(
        new_text=non_dup_text,
        district="Ganjam",
        category="Road Infrastructure",  # Different category
        db=db
    )
    assert non_dup_res["is_duplicate"] is False
    print("Non-duplicate test passed successfully.")
    print("ALL CROSS-LANGUAGE DUPLICATE TESTS PASSED!\n")

if __name__ == "__main__":
    test_cross_language_duplicates()
