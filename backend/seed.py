import os
import sys
import datetime
import random
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import engine, Base, SessionLocal
from app.models import (
    User,
    Complaint,
    StatusHistory,
    Notification,
    AdminCorrection
)

# Realistic demographic weights for Odisha districts
DISTRICT_WEIGHTS = {
    "Khurda": 14,      # Bhubaneswar Capital metro (~22%)
    "Cuttack": 10,     # Historic commercial & judicial hub (~16%)
    "Ganjam": 10,      # Southern trade & agrarian center (~15%)
    "Sundargarh": 8,   # Rourkela industrial & steel hub (~12%)
    "Sambalpur": 5,    # Western Odisha education & trade (~8%)
    "Balasore": 4,     # Coastal northern trade (~7%)
    "Puri": 4,         # Pilgrim & coastal tourism (~6%)
    "Mayurbhanj": 2,
    "Koraput": 2,
    "Jharsuguda": 2,
    "Angul": 2,
    "Jajpur": 1,
    "Kendrapara": 1,
    "Bhadrak": 1,
    "Bargarh": 1,
    "Dhenkanal": 1,
    "Bolangir": 1,
    "Rayagada": 1
}

DISTRICT_COORDS = {
    "Khurda": (20.2961, 85.8245, "751001", ["Patia", "Saheed Nagar", "Chandrasekharpur", "Nayapalli", "Khandagiri", "Jatani"]),
    "Cuttack": (20.4625, 85.8828, "753001", ["Badambadi", "CDA Sector 9", "Link Road", "Bidanasi", "Ranihat", "Choudwar"]),
    "Ganjam": (19.3150, 84.7941, "760001", ["Berhampur Ward 7", "Gopalpur Road", "Aska Main Road", "Chatrapur", "Hinjilicut"]),
    "Sundargarh": (22.2604, 84.8536, "769001", ["Rourkela Sector 4", "Panposh", "Civil Township", "Uditnagar", "Vedvyas"]),
    "Sambalpur": (21.4669, 83.9812, "768001", ["Golbazar", "Burla Hospital Road", "Khetrajpur", "Ainthapali"]),
    "Balasore": (21.4934, 86.9135, "756001", ["Remuna", "Sahadevkhunta", "Jaleswar Road", "Fakir Mohan Golei"]),
    "Puri": (19.8135, 85.8312, "752001", ["Grand Road", "Pipili Market", "Swargadwar", "Konark Marine Drive"]),
    "Mayurbhanj": (21.9300, 86.7300, "757001", ["Baripada Ward 4", "Rairangpur Market"]),
    "Koraput": (18.8135, 82.7118, "764001", ["Jeypore Town", "Sunabeda Township"]),
    "Jharsuguda": (21.8500, 84.0000, "768201", ["Station Road", "Brajarajnagar"]),
    "Angul": (20.8400, 85.1000, "759122", ["Nalco Nagar", "Talcher Colliery"]),
    "Jajpur": (20.8500, 86.3300, "755001", ["Kalinganagar", "Jajpur Town"]),
    "Kendrapara": (20.5000, 86.4200, "754211", ["Duhuria Chowk", "Pattamundai"]),
    "Bhadrak": (21.0500, 86.5000, "756100", ["Charampa", "Bhadrak Market"]),
    "Bargarh": (21.3300, 83.6200, "768028", ["Barabazar", "Attabira"]),
    "Dhenkanal": (20.6600, 85.6000, "759001", ["Baji Chowk", "Gundichapada"]),
    "Bolangir": (20.7100, 83.4800, "767001", ["Rugudipada", "Titilagarh Road"]),
    "Rayagada": (19.1700, 83.4100, "765001", ["JK Pur", "Rayagada Town"])
}

CATEGORY_TEMPLATES = [
    {
        "category": "Water Supply",
        "department": "PHED",
        "sub_categories": ["Pipeline Leakage", "Contaminated Muddy Water", "Low Water Pressure", "Broken Tube Well"],
        "titles": [
            ("Drinking water pipeline burst causing heavy wastage", "Main water pipeline ruptured near municipal crossing; water running into gutters."),
            ("ଗ୍ରାମରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟି କାଦୁଅ ପାଣି ଆସୁଛି", "ପାଇପ୍ ଫାଟି ଯାଇଛି ଏବଂ ପିଇବା ପାଣିରେ କାଦୁଅ ଆସୁଛି, ପିଲାମାନେ ଅସୁସ୍ଥ ହେଉଛନ୍ତି।"),
            ("वार्ड में 3 दिनों से पीने के पानी की गंभीर किल्लत", "पाइपलाइन लीकेज के कारण पूरे इलाके में गंदा बदबूदार पानी आ रहा है।"),
            ("Ward 4 re pani pipe phatiki kadua pani asuchi", "Sakalu tap on kale yellow dirty water berocche, please fix pipeline.")
        ]
    },
    {
        "category": "Road Infrastructure",
        "department": "PWD",
        "sub_categories": ["Deep Potholes Hazard", "Broken Culvert / Bridge", "Waterlogged Roadway", "Missing Guard Rail"],
        "titles": [
            ("Severe deep potholes on arterial highway causing frequent accidents", "Heavy rain created half-meter craters on main road; two-wheelers slipping daily."),
            ("ମୁଖ୍ୟ ରାସ୍ତାରେ ବଡ଼ ବଡ଼ ଖାଲଖମା ଯୋଗୁଁ ଦୁର୍ଘଟଣା", "ରାସ୍ତା ମଝିରେ ଗାତ ହୋଇ ଗାଡ଼ି ଚଳାଚଳ ସମ୍ପୂର୍ଣ୍ଣ ବାଧାପ୍ରାପ୍ତ ହୋଇଛି।"),
            ("सड़क पर भारी गड्ढे और डामर उखड़ने से दुर्घटना का खतरा", "स्टेशन रोड पर गहरा गड्ढा है जिसमें कल रात एक बाइक सवार गिरकर घायल हो गया।"),
            ("Badambadi rasta re pothole heichi gaadi chali paruni", "Deep potholes right near the intersection creating massive traffic bottleneck.")
        ]
    },
    {
        "category": "Electricity",
        "department": "DISCOM",
        "sub_categories": ["Transformer Burnout", "Overhead Wire Sparking", "Persistent Blackout", "Streetlight Non-Operational"],
        "titles": [
            ("100 KVA electrical transformer burnt out causing total blackout", "Transformer caught fire last night with heavy sparks. 60 households in the dark."),
            ("ବିଦ୍ୟୁତ୍ ଟ୍ରାନ୍ସଫର୍ମର ପୋଡ଼ି ଯାଇଛି, ପୁରା ଗାଁ ଅନ୍ଧାରରେ ଅଛି", "ତାରରୁ ନିଆଁ ବାହାରି ଟ୍ରାନ୍ସଫର୍ମର ନଷ୍ଟ ହୋଇଛି, ପରୀକ୍ଷା ଚାଲିଥିବାରୁ ପିଲା ହଇରାଣ।"),
            ("11KV की बिजली तार टूटकर सड़क पर झूल रही है", "हाई वोल्टेज तार लटक रहा है, किसी भी समय बड़ा हादसा हो सकता है। लाइन काटें।"),
            ("Transformer re spark maruchi fire danger achhi jaldi aasa", "Live spark jumping onto nearby trees, emergency response needed.")
        ]
    },
    {
        "category": "Sanitation",
        "department": "Municipal Corporation",
        "sub_categories": ["Drain Overflow & Stagnation", "Garbage Dump Clearing", "Mosquito Breeding Hazard", "Open Drain Slab"],
        "titles": [
            ("Uncleaned municipal drain overflowing foul water onto market road", "Drainage completely choked with polythene; dirty sewage entering shop basements."),
            ("ଅଳିଆ ଜମି ରହି ବହୁତ ଦୁର୍ଗନ୍ଧ ହେଉଛି ଓ ମଶା ବଢ଼ୁଛନ୍ତି", "ଗତ ୫ ଦିନରୁ କଚରା ଗାଡ଼ି ଆସିନାହିଁ, ସବୁଆଡ଼େ ଦୁର୍ଗନ୍ଧ ବ୍ୟାପିଛି।"),
            ("कॉलोनी में 4 दिनों से कचरा गाड़ी नहीं आई, गंदगी का अंबार", "अस्पताल के पास खुला कचरा डंप है जिससे संक्रमण का भारी खतरा है।"),
            ("Gali re kachra alia bahut jamichi smell asuchi", "Drain cleaner gadi asuni gandha hauchhi masha badhuchhanti.")
        ]
    },
    {
        "category": "Public Health",
        "department": "Health & Family Welfare",
        "sub_categories": ["Absent Duty Doctor", "Anti-Rabies / Snake Bite Shortage", "Primary Health Center Sanitation", "Ambulance Unavailability"],
        "titles": [
            ("Duty doctor absent and anti-rabies vaccine out of stock at CHC", "Patients arriving with dog bites being turned away to distant district hospital."),
            ("ହସ୍ପିଟାଲରେ ଡାକ୍ତର ଅନୁପସ୍ଥିତ ଏବଂ ଜରୁରୀ ସାପ କାମୁଡ଼ା ଔଷଧ ନାହିଁ", "ଜରୁରୀକାଳୀନ ସ୍ଥିତିରେ କୌଣସି ଡାକ୍ତର ଉପସ୍ଥିତ ନାହାନ୍ତି।"),
            ("सामुदायिक स्वास्थ्य केंद्र में आवश्यक दवाओं की भारी कमी", "प्रसव कक्ष में बुनियादी सुविधाएं नहीं हैं और ड्यूटी स्टाफ गैरहाजिर है।"),
            ("DHH re snake bite injection nahi boluchhanti", "Patient serious condition re achhi emergency doctor absent.")
        ]
    },
    {
        "category": "Ration / PDS",
        "department": "Food Supplies & Consumer Welfare",
        "sub_categories": ["Under-weighing Food Grains", "Refusal to Issue Monthly Grain", "e-POS Biometric Machine Failure", "Overcharging for Rice"],
        "titles": [
            ("Fair price ration shop dealer refusing food grain disbursement", "Dealer claiming server down and cutting 3kg rice per BPL card holder."),
            ("ରାସନ ଡିଲର ପ୍ରତି କାର୍ଡରେ ୩ କିଲୋ ଚାଉଳ କମ୍ ଦେଉଛନ୍ତି", "ଡିଲର ମନମୁଖୀ ଭାବେ କୋଟା କାଟି ରସିଦ ଦେବାକୁ ମନା କରୁଛନ୍ତି।"),
            ("राशन डीलर द्वारा कम अनाज वितरण और ई-पॉस में अंगूठा लगाकर मना करना", "35 किलो के बदले मात्र 30 किलो खाद्यान्न दिया जा रहा है।"),
            ("Dealer ration card biometric scan re problem heuchi", "Machine error boliki dealer chawal deuni 15 days hela.")
        ]
    }
]

def generate_weighted_seed():
    print("Executing Weighted District Re-seed...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Primary Users
        rani = User(
            id="USR-8921",
            name="Rani Nayak",
            phone="9876543210",
            email="rani.nayak@example.gov.in",
            role="citizen",
            language="or",
            district="Ganjam",
            avatar="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=150&q=80"
        )
        admin = User(
            id="EMP-4402",
            name="Dr. Alok Mohapatra, OAS",
            phone="9876500000",
            email="alok.mohapatra@odisha.gov.in",
            employee_id="OD-ADM-2024-88",
            role="admin",
            department="Grievance & Public Administration",
            language="en",
            district="State Secretariat, Bhubaneswar"
        )
        guest = User(
            id="GUEST-0001",
            name="Guest Citizen",
            phone=None,
            email=None,
            role="guest",
            language="en"
        )
        db.add_all([rani, admin, guest])
        db.commit()

        # 2. Rani Nayak's exact demo complaints (GRV-1042, GRV-0987, GRV-0951)
        r1 = Complaint(
            id="GRV-1042",
            title="Water Supply Issue – Low pressure and pipeline blockage",
            description="Pipeline supplying drinking water to Ward 7, Berhampur has been contaminated and running at extremely low pressure for the past 4 days.",
            department="PHED",
            category="Water Supply",
            sub_category="Pipeline Contamination & Low Pressure",
            urgency="Medium",
            language="Odia",
            status="In Progress",
            district="Ganjam",
            area="Berhampur, Ward 7",
            pincode="760001",
            lat=19.3150,
            lng=84.7941,
            submitted_date="28 Oct 2026",
            expected_date="05 Nov 2026",
            days_remaining=2,
            user_id="USR-8921",
            citizen_phone="9876543210",
            assigned_officer_name="Er. S. K. Patnaik",
            assigned_officer_designation="Assistant Executive Engineer",
            assigned_officer_dept="PHED, Berhampur Division",
            assigned_officer_phone="+91 94370 12345",
            ai_confidence=0.96,
            needs_human_review=False,
            translated_text_en="Drinking water pipeline in Ward 7, Berhampur has contamination and extremely low pressure for 4 days.",
            sentiment="Frustrated",
            ai_summary="Water pipeline contamination and acute low pressure in Berhampur Ward 7.",
            source="ai_assistant"
        )
        h1 = [
            StatusHistory(complaint_id="GRV-1042", status="Submitted", date="28 Oct 2026", time="09:30 AM", officer="System AI Intake", note="Grievance registered via AI Voice Assistant in Odia. Auto-classified to PHED.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-1042", status="Assigned", date="29 Oct 2026", time="11:15 AM", officer="Er. S. K. Patnaik", note="Assigned to Division Executive Engineer for physical line inspection.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-1042", status="In Progress", date="30 Oct 2026", time="02:15 PM", officer="Er. S. K. Patnaik", note="Pipeline clearance and valve replacement team deployed on ground.", completed=True, current=True),
            StatusHistory(complaint_id="GRV-1042", status="Resolved", date="05 Nov 2026", time="Pending", officer="Pending Final Inspection", note="Target SLA deadline.", completed=False, current=False)
        ]

        r2 = Complaint(
            id="GRV-0987",
            title="Road Craters and Broken Pavement on Main Road",
            description="Deep potholes developed after heavy rainfall near the market square, creating severe accident risks for two-wheelers.",
            department="PWD",
            category="Road Infrastructure",
            sub_category="Potholes Hazard",
            urgency="High",
            language="Odia",
            status="Resolved",
            district="Ganjam",
            area="Aska Road, Berhampur",
            pincode="760002",
            lat=19.3210,
            lng=84.7890,
            submitted_date="15 Oct 2026",
            expected_date="20 Oct 2026",
            days_remaining=0,
            user_id="USR-8921",
            citizen_phone="9876543210",
            assigned_officer_name="Er. B. C. Pradhan",
            assigned_officer_designation="Divisional Road Engineer",
            assigned_officer_dept="PWD Roads Division",
            assigned_officer_phone="+91 94371 98765",
            feedback_rating=5,
            feedback_comment="Road was repaired within 4 days. Excellent work by PWD team.",
            ai_confidence=0.94,
            needs_human_review=False,
            translated_text_en="Deep potholes developed after heavy rainfall near the market square, creating severe accident risks.",
            sentiment="Satisfied",
            ai_summary="Deep pothole hazards on Aska Road, Berhampur repaired.",
            source="web_form"
        )
        h2 = [
            StatusHistory(complaint_id="GRV-0987", status="Submitted", date="15 Oct 2026", time="10:00 AM", officer="Citizen Portal", note="Complaint submitted via web form with geotagged photo.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0987", status="Assigned", date="16 Oct 2026", time="11:30 AM", officer="Er. B. C. Pradhan", note="Forwarded to Berhampur PWD Road Maintenance Cell.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0987", status="In Progress", date="17 Oct 2026", time="09:00 AM", officer="Er. B. C. Pradhan", note="Road bitumen patchwork crew mobilized.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0987", status="Resolved", date="19 Oct 2026", time="04:30 PM", officer="Er. B. C. Pradhan", note="Pothole patch work completed and certified safe by junior engineer.", completed=True, current=True)
        ]

        r3 = Complaint(
            id="GRV-0951",
            title="Streetlights Inoperative in Residential Colony",
            description="Entire block of 12 LED streetlights on 4th Cross Road has been dark for two weeks.",
            department="DISCOM",
            category="Electricity",
            sub_category="Streetlight Outage",
            urgency="Low",
            language="English",
            status="Resolved",
            district="Khurda",
            area="Patia, Bhubaneswar",
            pincode="751024",
            lat=20.3533,
            lng=85.8195,
            submitted_date="10 Oct 2026",
            expected_date="15 Oct 2026",
            days_remaining=0,
            user_id="USR-8921",
            citizen_phone="9876543210",
            assigned_officer_name="P. Mohanty",
            assigned_officer_designation="Electrical Line Inspector",
            assigned_officer_dept="TPCODL / DISCOM",
            assigned_officer_phone="+91 94375 55432",
            feedback_rating=4,
            feedback_comment="Resolved quickly once inspected.",
            ai_confidence=0.98,
            needs_human_review=False,
            translated_text_en="Entire block of 12 LED streetlights on 4th Cross Road has been dark for two weeks.",
            sentiment="Neutral",
            ai_summary="12 streetlights non-operational on Patia 4th Cross road.",
            source="ai_assistant"
        )
        h3 = [
            StatusHistory(complaint_id="GRV-0951", status="Submitted", date="10 Oct 2026", time="08:15 AM", officer="AI Intake", note="Reported via JanSamadhan Assistant in English.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0951", status="Assigned", date="11 Oct 2026", time="10:00 AM", officer="P. Mohanty", note="Assigned to Patia distribution substation lineman.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0951", status="In Progress", date="12 Oct 2026", time="03:20 PM", officer="P. Mohanty", note="Faulty phase transformer fuse and 4 blown LEDs replaced.", completed=True, current=False),
            StatusHistory(complaint_id="GRV-0951", status="Resolved", date="14 Oct 2026", time="06:00 PM", officer="P. Mohanty", note="All streetlights tested and verified active in evening inspection.", completed=True, current=True)
        ]

        db.add_all([r1, r2, r3])
        db.add_all(h1 + h2 + h3)
        db.commit()

        # 3. Generate weighted distribution across districts
        complaint_counter = 1043
        all_new_complaints = []
        all_new_histories = []

        statuses = ["Submitted", "Assigned", "In Progress", "Resolved"]
        status_weights = [0.20, 0.30, 0.30, 0.20]

        urgencies = ["Critical", "High", "Medium", "Low"]
        urgency_weights = [0.15, 0.40, 0.35, 0.10]

        for district, target_count in DISTRICT_WEIGHTS.items():
            base_lat, base_lng, base_pin, areas = DISTRICT_COORDS.get(district, (20.29, 85.82, "751001", ["Central Ward"]))

            # Subtract Rani's complaints already in Ganjam (2) and Khurda (1)
            count = target_count
            if district == "Ganjam":
                count = max(1, target_count - 2)
            elif district == "Khurda":
                count = max(1, target_count - 1)

            for i in range(count):
                comp_id = f"GRV-{complaint_counter}"
                complaint_counter += 1

                cat_info = random.choice(CATEGORY_TEMPLATES)
                title_pair = random.choice(cat_info["titles"])
                sub_cat = random.choice(cat_info["sub_categories"])
                status = random.choices(statuses, weights=status_weights)[0]
                urgency = random.choices(urgencies, weights=urgency_weights)[0]
                area = random.choice(areas)

                # Realistic jitter around district coordinates
                jitter_lat = base_lat + random.uniform(-0.04, 0.04)
                jitter_lng = base_lng + random.uniform(-0.04, 0.04)

                days_rem = 0 if status == "Resolved" else random.randint(1, 6)
                ai_conf = round(random.uniform(0.55, 0.98), 2)
                needs_review = (ai_conf < 0.60)

                langs = ["Odia", "Hindi", "Bengali", "Telugu", "English"]
                lang = random.choices(langs, weights=[0.45, 0.25, 0.10, 0.05, 0.15])[0]

                c = Complaint(
                    id=comp_id,
                    title=title_pair[0],
                    description=title_pair[1],
                    category=cat_info["category"],
                    sub_category=sub_cat,
                    department=cat_info["department"],
                    urgency=urgency,
                    language=lang,
                    status=status,
                    district=district,
                    area=f"{area}, Ward {random.randint(1, 25)}",
                    pincode=base_pin,
                    lat=round(jitter_lat, 4),
                    lng=round(jitter_lng, 4),
                    submitted_date="28 Oct 2026",
                    expected_date="05 Nov 2026",
                    days_remaining=days_rem,
                    user_id=None,
                    citizen_phone=f"98{random.randint(10000000, 99999999)}",
                    assigned_officer_name=f"Officer {random.choice(['Prusty', 'Sahu', 'Panda', 'Mohapatra', 'Behera'])}",
                    assigned_officer_designation="Nodal Field Engineer",
                    assigned_officer_dept=cat_info["department"],
                    ai_confidence=ai_conf,
                    needs_human_review=needs_review,
                    translated_text_en=title_pair[1],
                    sentiment=random.choice(["Frustrated", "Urgent", "Distressed", "Neutral"]),
                    ai_summary=f"{cat_info['category']} issue in {area}, {district}.",
                    source=random.choice(["ai_assistant", "web_form", "voice"])
                )
                all_new_complaints.append(c)

                h = StatusHistory(
                    complaint_id=comp_id,
                    status=status,
                    date="28 Oct 2026",
                    time="10:30 AM",
                    officer=f"Nodal Desk ({cat_info['department']})",
                    note=f"Grievance recorded and operational routing confirmed for {district}.",
                    completed=True,
                    current=True
                )
                all_new_histories.append(h)

        db.add_all(all_new_complaints)
        db.add_all(all_new_histories)
        db.commit()

        # 4. Seed initial Admin Corrections for human audit tracking
        c1 = AdminCorrection(
            complaint_id="GRV-1044",
            admin_id="EMP-4402",
            field_name="category",
            original_value="Water Supply",
            corrected_value="Sanitation"
        )
        c2 = AdminCorrection(
            complaint_id="GRV-1045",
            admin_id="EMP-4402",
            field_name="department",
            original_value="PWD",
            corrected_value="DISCOM"
        )
        db.add_all([c1, c2])

        # 5. Seed Notifications
        notifications = [
            Notification(
                id="NOTIF-1",
                user_id="USR-8921",
                title="Status Update: GRV-1042",
                message="GRV-1042 assigned to PHED, Berhampur. Work team deployed on site.",
                type="update",
                read=False,
                related_grv_id="GRV-1042",
                timestamp_str="30 Oct 2026 • 2:15 PM"
            ),
            Notification(
                id="NOTIF-2",
                user_id=None,
                title="New AI Assistant Capabilities",
                message="New feature: Chat with JanSamadhan Assistant in 6 Indian languages with voice input.",
                type="announcement",
                read=False,
                timestamp_str="25 Oct 2026 • 11:00 AM"
            ),
            Notification(
                id="NOTIF-3",
                user_id=None,
                title="Scheduled Maintenance Notice",
                message="System maintenance scheduled on 10 Nov 2026 from 02:00 AM to 04:00 AM IST.",
                type="announcement",
                read=True,
                timestamp_str="24 Oct 2026 • 06:30 PM"
            )
        ]
        db.add_all(notifications)
        db.commit()

        total = db.query(Complaint).count()
        print(f"Successfully re-seeded weighted database! Total Complaints: {total}")

    except Exception as e:
        db.rollback()
        print(f"Error during weighted seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    generate_weighted_seed()
