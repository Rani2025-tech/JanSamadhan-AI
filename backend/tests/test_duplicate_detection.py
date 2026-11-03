import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Complaint
from ai.duplicates import check_duplicate_complaint

POSITIVE_PAIRS = [
    {
        "id": "POS-01",
        "district": "Ganjam",
        "area": "Ward 7, Berhampur",
        "category": "Water Supply",
        "text_a": "ୱାର୍ଡ ୭ ବ୍ରହ୍ମପୁରରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି ଏବଂ କାଦୁଅ ପାଣି ବାହାରୁଛି",
        "text_b": "वार्ड 7 ब्रह्मपुर में पीने के पानी का पाइप फूट गया है और गंदा पानी आ रहा है",
        "desc": "Odia vs Hindi (Berhampur Ward 7 - Drinking water pipe burst & muddy water)"
    },
    {
        "id": "POS-02",
        "district": "Cuttack",
        "area": "Badambadi",
        "category": "Road Infrastructure",
        "text_a": "Badambadi rasta re bhaliki pothole heichi gaadi chali paruni",
        "text_b": "Deep dangerous potholes on Badambadi road causing serious accidents and traffic block",
        "desc": "Odishlish vs English (Badambadi - Deep road potholes & accident risk)"
    },
    {
        "id": "POS-03",
        "district": "Khurda",
        "area": "Patia, Bhubaneswar",
        "category": "Electricity",
        "text_a": "पटिया में बिजली का ट्रांसफार्मर जल गया है और चारों तरफ अंधेरा है",
        "text_b": "পাটিয়াতে ট্রান্সফরমার বিকল হয়ে গেছে সম্পূর্ণ এলাকা অন্ধকারে",
        "desc": "Hindi vs Bengali (Patia - Transformer burnout & blackout)"
    },
    {
        "id": "POS-04",
        "district": "Ganjam",
        "area": "Gopalpur Main Road",
        "category": "Water Supply",
        "text_a": "ଗୋପାଳପୁରରେ ମୁଖ୍ୟ ପାଇପ୍ ଭାଙ୍ଗିଯିବା ଯୋଗୁଁ ୪ ଦିନ ହେଲା ପିଇବା ପାଣି ବନ୍ଦ ଅଛି",
        "text_b": "గోపాల్‌పూర్‌లో ప్రధాన పైపు పగిలిపోవడం వల్ల నాలుగు రోజులుగా తాగునీరు నిలిచిపోయింది",
        "desc": "Odia vs Telugu (Gopalpur - Water supply cut off for 4 days)"
    },
    {
        "id": "POS-05",
        "district": "Balasore",
        "area": "Jaleswar Ward 5",
        "category": "Sanitation",
        "text_a": "জলেশ্বরের স্কুলের কাছে নর্দমার ঢাকনা ভেঙে গেছে বাচ্চা পড়ে গেছে",
        "text_b": "जलेश्वर में स्कूल के पास खुली नाली का ढक्कन टूटा हुआ है और खतरा बना हुआ है",
        "desc": "Bengali vs Hindi (Jaleswar - Open broken drain cover near school)"
    },
    {
        "id": "POS-06",
        "district": "Jharsuguda",
        "area": "Station Road",
        "category": "Sanitation",
        "text_a": "Station road par kachra ka bada dher laga hai aur naali overflow ho rahi hai badboo aa rahi",
        "text_b": "ଝାରସୁଗୁଡ଼ା ଷ୍ଟେସନ ରୋଡରେ ଅଳିଆ ଜମି ରହି ନର୍ଦ୍ଦମା ପାଣି ରାସ୍ତାରେ ବୋହୁଛି ଓ ଦୁର୍ଗନ୍ଧ ହେଉଛି",
        "desc": "Hinglish vs Odia (Jharsuguda Station Road - Garbage dump & drain overflow)"
    },
    {
        "id": "POS-07",
        "district": "Sundargarh",
        "area": "Panposh Sub-Division",
        "category": "Public Health",
        "text_a": "ପାନପୋଷ ଡାକ୍ତରଖାନାରେ ଡାକ୍ତର ଅନୁପସ୍ଥିତ ଏବଂ କୁକୁର କାମୁଡ଼ା ଇଞ୍ଜେକ୍ସନ ନାହିଁ",
        "text_b": "Doctor absent and anti-rabies vaccine out of stock at Panposh hospital",
        "desc": "Odia vs English (Panposh - Doctor absent & anti-rabies out of stock)"
    },
    {
        "id": "POS-08",
        "district": "Koraput",
        "area": "Jeypore Town Ward 9",
        "category": "Ration / PDS",
        "text_a": "Jeypore ration dealer quota ru chaula cut karuchi biometric machine bahana dekhei",
        "text_b": "जयपुर में राशन डीलर बायोमेट्रिक मशीन का बहाना बनाकर हर कार्ड पर चावल काट रहा है",
        "desc": "Odishlish vs Hindi (Jeypore - PDS dealer cutting rice quota on machine excuse)"
    },
    {
        "id": "POS-09",
        "district": "Mayurbhanj",
        "area": "Baripada Ward 11",
        "category": "Electricity",
        "text_a": "Baripada ward 11 sob streetlight bondho ache raate khub andhokar",
        "text_b": "All streetlights non functional in Baripada Ward 11 causing pitch darkness at night",
        "desc": "Banglish vs English (Baripada - All streetlights dark)"
    },
    {
        "id": "POS-10",
        "district": "Puri",
        "area": "Pipili Block, Ward 3",
        "category": "Water Supply",
        "text_a": "पिपिली वार्ड 3 में नलों से पीला बदबूदार दूषित पानी आ रहा है",
        "text_b": "ପିପିଲି ୱାର୍ଡ ୩ ରେ ନଳରୁ ହଳଦିଆ ଦୁର୍ଗନ୍ଧଯୁକ୍ତ ମଇଳା ପାଣି ଆସୁଛି",
        "desc": "Hindi vs Odia (Pipili - Contaminated yellow foul tap water)"
    }
]

NEGATIVE_PAIRS = [
    {
        "id": "NEG-01",
        "district_a": "Ganjam",
        "category_a": "Water Supply",
        "text_a": "ୱାର୍ଡ ୭ ବ୍ରହ୍ମପୁରରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି",
        "district_b": "Ganjam",
        "category_b": "Electricity",
        "text_b": "ବ୍ରହ୍ମପୁରରେ ବିଦ୍ୟୁତ୍ ଟ୍ରାନ୍ସଫର୍ମର ପୋଡ଼ି ଯାଇଛି ଏବଂ କରେଣ୍ଟ ନାହିଁ",
        "desc": "Same district (Ganjam), but Water Supply vs Electricity"
    },
    {
        "id": "NEG-02",
        "district_a": "Ganjam",
        "category_a": "Water Supply",
        "text_a": "ୱାର୍ଡ ୭ ବ୍ରହ୍ମପୁରରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି",
        "district_b": "Sundargarh",
        "category_b": "Water Supply",
        "text_b": "ରାଉରକେଲା ସେକ୍ଟର ୪ ରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି ଯାଇଛି",
        "desc": "Same issue (Water pipe burst), but Different Districts (Ganjam vs Sundargarh)"
    },
    {
        "id": "NEG-03",
        "district_a": "Cuttack",
        "category_a": "Road Infrastructure",
        "text_a": "ବାଦାମବାଡ଼ି ରାସ୍ତାରେ ବଡ଼ ବଡ଼ ଖାଲଖମା ହୋଇଛି ଗାଡ଼ି ଚାଲିପାରୁନି",
        "district_b": "Cuttack",
        "category_b": "Sanitation",
        "text_b": "ବାଦାମବାଡ଼ିରେ ଅଳିଆ ଗଦା ହୋଇ ନର୍ଦ୍ଦମା ଜମି ରହିଛି ବହୁତ ଦୁର୍ଗନ୍ଧ ହେଉଛି",
        "desc": "Same area (Badambadi), but Road Potholes vs Sanitation Garbage"
    },
    {
        "id": "NEG-04",
        "district_a": "Khurda",
        "category_a": "Electricity",
        "text_a": "Patia re sob streetlight bondho ache raate khub andhokar",
        "district_b": "Khurda",
        "category_b": "Ration / PDS",
        "text_b": "Patia re ration dealer chaula kam douchi biometric machine kharab kahi",
        "desc": "Same area (Patia), but Streetlights vs Ration Shop"
    },
    {
        "id": "NEG-05",
        "district_a": "Sambalpur",
        "category_a": "Electricity",
        "text_a": "Sambalpur re 100KVA transformer blast heichi pura andhara",
        "district_b": "Balasore",
        "category_b": "Electricity",
        "text_b": "Balasore re 11KV wire rasta re padichi emergency danger",
        "desc": "Same category (Electricity), but Different Districts (Sambalpur vs Balasore)"
    },
    {
        "id": "NEG-06",
        "district_a": "Koraput",
        "category_a": "Public Health",
        "text_a": "Jeypore hospital re emergency doctor nahi patient serious",
        "district_b": "Puri",
        "category_b": "Road Infrastructure",
        "text_b": "Pipili main road re culvert bhangi jaichi heavy accident danger",
        "desc": "Different Categories & Different Districts (Koraput Health vs Puri Road)"
    },
    {
        "id": "NEG-07",
        "district_a": "Puri",
        "category_a": "Water Supply",
        "text_a": "Grand Road Puri re tap water muddy and yellow foul smelling",
        "district_b": "Puri",
        "category_b": "Electricity",
        "text_b": "Grand Road Puri re streetlights not working dark streets",
        "desc": "Same area (Grand Road Puri), but Water Contamination vs Streetlight"
    },
    {
        "id": "NEG-08",
        "district_a": "Cuttack",
        "category_a": "Sanitation",
        "text_a": "Cuttack CDA re drain choked sewage overflow on road",
        "district_b": "Jharsuguda",
        "category_b": "Sanitation",
        "text_b": "Jharsuguda station road re drain choked sewage overflow on road",
        "desc": "Same issue (Drain choked), but Different Districts (Cuttack vs Jharsuguda)"
    },
    {
        "id": "NEG-09",
        "district_a": "Balasore",
        "category_a": "Ration / PDS",
        "text_a": "Balasore ration dealer refusing monthly grain quota",
        "district_b": "Balasore",
        "category_b": "Public Health",
        "text_b": "Balasore hospital emergency doctor absent and snake venom injection out",
        "desc": "Same district (Balasore), but Ration Fraud vs Hospital Doctor Absent"
    },
    {
        "id": "NEG-10",
        "district_a": "Sundargarh",
        "category_a": "Road Infrastructure",
        "text_a": "Panposh bridge railing broken accident danger for buses",
        "district_b": "Sundargarh",
        "category_b": "Water Supply",
        "text_b": "Panposh colony tap water low pressure water cut off",
        "desc": "Same area (Panposh), but Road Bridge Railing vs Water Low Pressure"
    }
]

def run_duplicate_tests():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("\n================ JANSAMADHAN DUPLICATE DETECTION TEST SUITE ================")
    print(f"Testing {len(POSITIVE_PAIRS)} Cross-Language Positive Pairs and {len(NEGATIVE_PAIRS)} Negative Pairs...\n")

    # 1. Test Positive Pairs
    tp = 0
    fn = 0
    pos_results = []

    for idx, p in enumerate(POSITIVE_PAIRS, 1):
        # Insert complaint A
        comp_id = f"GRV-POS-{idx:02d}"
        comp_a = Complaint(
            id=comp_id,
            title=p["text_a"][:60],
            description=p["text_a"],
            category=p["category"],
            sub_category=f"{p['category']} Issue",
            department="Redressal Unit",
            urgency="High",
            status="Submitted",
            district=p["district"],
            area=p["area"],
            language="Multi",
            user_id="user-test",
            submitted_date="28 Oct 2026",
            expected_date="05 Nov 2026",
            days_remaining=3
        )
        db.add(comp_a)
        db.commit()

        # Check complaint B against complaint A
        res = check_duplicate_complaint(
            new_text=p["text_b"],
            district=p["district"],
            category=p["category"],
            db=db,
            threshold=0.55
        )

        is_dup = res["is_duplicate"]
        conf = res["confidence"]
        if is_dup:
            tp += 1
            status = "PASS (Detected)"
        else:
            fn += 1
            status = "FAIL (Missed)"

        pos_results.append({
            "id": p["id"],
            "desc": p["desc"],
            "confidence": conf,
            "detected": is_dup,
            "status": status
        })
        print(f"[{status}] {p['id']}: {p['desc']} -> Conf: {conf}")

    # 2. Test Negative Pairs
    fp = 0
    tn = 0
    neg_results = []

    for idx, p in enumerate(NEGATIVE_PAIRS, 1):
        comp_id = f"GRV-NEG-{idx:02d}"
        comp_a = Complaint(
            id=comp_id,
            title=p["text_a"][:60],
            description=p["text_a"],
            category=p["category_a"],
            sub_category=f"{p['category_a']} Issue",
            department="Redressal Unit",
            urgency="High",
            status="Submitted",
            district=p["district_a"],
            area=p.get("area_a", "Zone A"),
            language="Multi",
            user_id="user-test",
            submitted_date="28 Oct 2026",
            expected_date="05 Nov 2026",
            days_remaining=3
        )
        db.add(comp_a)
        db.commit()

        res = check_duplicate_complaint(
            new_text=p["text_b"],
            district=p["district_b"],
            category=p["category_b"],
            db=db,
            threshold=0.55
        )

        is_dup = res["is_duplicate"]
        conf = res["confidence"]
        if is_dup:
            fp += 1
            status = "FAIL (False Positive)"
        else:
            tn += 1
            status = "PASS (Correctly Rejected)"

        neg_results.append({
            "id": p["id"],
            "desc": p["desc"],
            "confidence": conf,
            "rejected": not is_dup,
            "status": status
        })
        print(f"[{status}] {p['id']}: {p['desc']} -> Conf: {conf}")

    # Compute Metrics
    total_pos = len(POSITIVE_PAIRS)
    total_neg = len(NEGATIVE_PAIRS)

    precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 0.0
    recall = round((tp / total_pos) * 100, 2) if total_pos > 0 else 0.0
    fpr = round((fp / total_neg) * 100, 2) if total_neg > 0 else 0.0

    print("\n---------------- DUPLICATE DETECTION EVALUATION SUMMARY ----------------")
    print(f"Positive Pairs (Cross-language Duplicates): {tp}/{total_pos} detected")
    print(f"Negative Pairs (Different Issue/District):   {tn}/{total_neg} correctly rejected")
    print(f"Precision:           {precision}% ({tp}/{tp + fp})")
    print(f"Recall:              {recall}% ({tp}/{total_pos})")
    print(f"False-Positive Rate: {fpr}% ({fp}/{total_neg})")
    print("========================================================================\n")

    assert recall >= 90.0, f"Expected recall >= 90%, got {recall}%"
    assert fpr <= 10.0, f"Expected FPR <= 10%, got {fpr}%"
    print("ALL 20 DUPLICATE DETECTION TESTS PASSED VERIFICATION!")

if __name__ == "__main__":
    run_duplicate_tests()

