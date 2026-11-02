import os
import sys
import uuid
import random
import argparse
from datetime import datetime, timedelta
import bcrypt
from dotenv import load_dotenv

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from backend.db.database import get_conn, _exec, _ph
from backend.db.grievances import (
    init_grievance_tables,
    SLA_HOURS,
    run_escalation,
    get_stats
)

# Hindi/Odia text needs review by a fluent speaker

DEMO_TEMPLATES = [
    # 1. Water Supply
    {
        "category": "Water Supply",
        "department": "Public Health Engineering / Water Board",
        "priority": "High",
        "texts": {
            "en": {
                "text": "Main drinking water pipeline burst near the market square, water is flooding the street and households have zero supply.",
                "summary": "Burst drinking water pipeline causing street flooding and loss of water supply in residential area."
            },
            "hi": {
                "text": "मुख्य बाजार के पास पेयजल पाइपलाइन फट गई है, सड़क पर पानी भर गया है और घरों में पानी की आपूर्ति ठप है।",
                "summary": "पेयजल पाइपलाइन फटने से सड़क पर जलभराव और पानी की आपूर्ति बाधित।"
            },
            "or": {
                "text": "ମୁଖ୍ୟ ବଜାର ନିକଟରେ ପିଇବା ପାଣି ପାଇପ୍ ଫାଟିଯାଇଛି, ରାସ୍ତାରେ ପାଣି ଭରିଯାଇଛି ଏବଂ ଘରମାନଙ୍କରେ ପାଣି ବନ୍ଦ ରହିଛି।",
                "summary": "ପିଇବା ପାଣି ପାଇପ୍ ଫାଟିବା ଯୋଗୁଁ ଜଳ ଯୋଗାଣ ବନ୍ଦ ଏବଂ ରାସ୍ତାରେ ଜଳବନ୍ଦୀ।"
            }
        }
    },
    # 2. Electricity
    {
        "category": "Electricity",
        "department": "Power Distribution Company (DISCOM)",
        "priority": "Critical",
        "texts": {
            "en": {
                "text": "High-voltage electric wire snapped and hanging low across residential footpath, sparking constantly.",
                "summary": "Dangerous snapped live power wire hanging low over sidewalk, creating severe electrocution hazard."
            },
            "hi": {
                "text": "आवासीय फुटपाथ पर हाई-वोल्टेज बिजली का तार टूटकर लटक रहा है और लगातार चिंगारियां निकल रही हैं।",
                "summary": "फुटपाथ पर टूटा हुआ बिजली का तार लटकने से करंट लगने का गंभीर खतरा।"
            },
            "or": {
                "text": "ଆବାସିକ ଫୁଟପାଥ୍ ଉପରେ ହାଇ-ଭୋଲ୍ଟେଜ୍ ବିଦ୍ୟୁତ୍ ତାର ଛିଣ୍ଡି ଝୁଲୁଛି ଏବଂ ନିଆଁ ବାହାରୁଛି।",
                "summary": "ଫୁଟପାଥରେ ବିପଜ୍ଜନକ ଭାବେ ଛିଣ୍ଡି ଝୁଲୁଥିବା ବିଦ୍ୟୁତ୍ ତାର ଯୋଗୁଁ ଦୁର୍ଘଟଣା ଆଶଙ୍କା।"
            }
        }
    },
    # 3. Roads & Potholes
    {
        "category": "Roads & Potholes",
        "department": "Public Works Department",
        "priority": "Medium",
        "texts": {
            "en": {
                "text": "Large deep potholes formed along the main road after rain, causing daily vehicle traffic jams and accidents.",
                "summary": "Severe deep potholes on main road causing traffic congestion and vehicular accidents."
            },
            "hi": {
                "text": "बारिश के बाद मुख्य सड़क पर बड़े और गहरे गड्ढे बन गए हैं, जिससे रोज जाम लग रहा है और दुर्घटनाएं हो रही हैं।",
                "summary": "मुख्य सड़क पर गहरे गड्ढों के कारण यातायात जाम और दुर्घटनाओं का खतरा।"
            },
            "or": {
                "text": "ବର୍ଷା ପରେ ମୁଖ୍ୟ ରାସ୍ତାରେ ବଡ଼ ବଡ଼ ଖାଲଖମା ସୃଷ୍ଟି ହୋଇଛି, ଯାହା ଫଳରେ ଦୁର୍ଘଟଣା ଘଟୁଛି।",
                "summary": "ମୁଖ୍ୟ ରାସ୍ତାରେ ଗଭୀର ଖାଲଖମା ଯୋଗୁଁ ଯାନବାହନ ଚଳାଚଳରେ ଅସୁବିଧା ଏବଂ ଦୁର୍ଘଟଣା।"
            }
        }
    },
    # 4. Sanitation & Garbage
    {
        "category": "Sanitation & Garbage",
        "department": "Municipal Corporation - Solid Waste",
        "priority": "Medium",
        "texts": {
            "en": {
                "text": "Garbage collection truck has not visited our street for four days, huge pile of rotting trash on roadside.",
                "summary": "Missed municipal garbage collection for four consecutive days causing overflow of waste."
            },
            "hi": {
                "text": "कचरा उठाने वाली गाड़ी पिछले चार दिनों से हमारी गली में नहीं आई है, सड़क किनारे सड़ा हुआ कचरा जमा हो गया है।",
                "summary": "चार दिनों से कचरा न उठने के कारण सड़क पर भारी गंदगी और बदबू।"
            },
            "or": {
                "text": "ଗତ ଚାରି ଦିନ ହେବ ଆମ ଗଳିକୁ ଅଳିଆ ଗାଡ଼ି ଆସିନାହିଁ, ରାସ୍ତା କଡ଼ରେ ଅଳିଆ ଜମା ହୋଇ ଦୁର୍ଗନ୍ଧ ହେଉଛି।",
                "summary": "୪ ଦିନ ଧରି ଅଳିଆ ସଂଗ୍ରହ ନହେବା ଯୋଗୁଁ ରାସ୍ତା କଡ଼ରେ ଆବର୍ଜନା ଜମା ହୋଇ ଦୁର୍ଗନ୍ଧ।"
            }
        }
    },
    # 5. Drainage & Sewage
    {
        "category": "Drainage & Sewage",
        "department": "Municipal Corporation - Drainage & Sewage",
        "priority": "High",
        "texts": {
            "en": {
                "text": "Open sewer manhole overflowing with foul-smelling wastewater onto residential road, posing health risk.",
                "summary": "Overflowing sewer manhole spilling dirty wastewater across residential lane."
            },
            "hi": {
                "text": "खुले सीवर मैनहोल से बदबूदार गंदा पानी आवासीय सड़क पर बह रहा है, जिससे बीमारी का खतरा पैदा हो गया है।",
                "summary": "सीवर मैनहोल ओवरफ्लो होने से गंदे पानी का सड़कों पर फैलाव।"
            },
            "or": {
                "text": "ଖୋଲା ଡ୍ରେନ୍‌ରୁ ଦୁର୍ଗନ୍ଧଯୁକ୍ତ ମଇଳା ପାଣି ରାସ୍ତା ଉପରେ ଭାସୁଛି, ଯାହା ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରତି ବିପଦ ସୃଷ୍ଟି କରୁଛି।",
                "summary": "ଡ୍ରେନ୍ ଓଭରଫ୍ଲୋ ଯୋଗୁଁ ରାସ୍ତା ଉପରେ ଦୂଷିତ ଜଳ ପ୍ରବାହିତ ଏବଂ ସ୍ୱାସ୍ଥ୍ୟ ବିପଦ।"
            }
        }
    },
    # 6. Street Lighting
    {
        "category": "Street Lighting",
        "department": "Municipal Corporation - Electrical Department",
        "priority": "Low",
        "texts": {
            "en": {
                "text": "Streetlights across the entire street have been completely dark for over a week, feels unsafe at night.",
                "summary": "Non-functional streetlights along the full stretch of residential street for over one week."
            },
            "hi": {
                "text": "पूरी गली की स्ट्रीट लाइटें पिछले एक हफ्ते से पूरी तरह बंद हैं, रात में असुरक्षा महसूस होती है।",
                "summary": "एक हफ्ते से बंद स्ट्रीट लाइटों के कारण रात में अंधेरा और सुरक्षा चिंताएं।"
            },
            "or": {
                "text": "ସମ୍ପୂର୍ଣ୍ଣ ଗଳିର ଷ୍ଟ୍ରିଟ୍ ଲାଇଟ୍ ଗତ ଏକ ସପ୍ତାହ ହେବ ଜଳୁନାହିଁ, ରାତିରେ ଯିବା ଆସିବା ବିପଜ୍ଜନକ ହୋଇଛି।",
                "summary": "ସପ୍ତାହେ ଧରି ଷ୍ଟ୍ରିଟ୍ ଲାଇଟ୍ ବନ୍ଦ ରହିବା ଯୋଗୁଁ ଅନ୍ଧକାର ଏବଂ ସୁରକ୍ଷା ଅସୁବିଧା।"
            }
        }
    },
    # 7. Public Health
    {
        "category": "Public Health",
        "department": "Municipal Health Department",
        "priority": "Medium",
        "texts": {
            "en": {
                "text": "Stagnant water in vacant plot causing severe mosquito infestation; municipal fogging drive needed urgently.",
                "summary": "Heavy mosquito breeding in stagnant water on abandoned plot; fogging requested."
            },
            "hi": {
                "text": "खाली प्लॉट में जमा पानी से मच्छरों का भारी प्रकोप हो गया है; तुरंत नगरपालिका फॉगिंग की आवश्यकता है।",
                "summary": "जमा पानी में मच्छरों के प्रकोप के कारण नगरपालिका फॉगिंग की मांग।"
            },
            "or": {
                "text": "ଖାଲି ପ୍ଲଟରେ ଜମି ରହିଥିବା ପାଣିରେ ମଶା ବୃଦ୍ଧି ପାଇଛନ୍ତି; ତୁରନ୍ତ ଔଷଧ ସ୍ପ୍ରେ କରିବା ଆବଶ୍ୟକ।",
                "summary": "ଜମି ରହିଥିବା ପାଣିରେ ମଶା ଉତ୍ପାତ ବୃଦ୍ଧି ଏବଂ ଫଗିଂ ସ୍ପ୍ରେ ଅନୁରୋଧ।"
            }
        }
    },
    # 8. Police & Public Safety
    {
        "category": "Police & Public Safety",
        "department": "State Police / Traffic Police",
        "priority": "Medium",
        "texts": {
            "en": {
                "text": "Commercial trucks illegally parked on both sides of two-way road, blocking access for ambulances and residents.",
                "summary": "Illegal heavy truck parking obstructing traffic flow and emergency ambulance access."
            },
            "hi": {
                "text": "सड़क के दोनों ओर कमर्शियल ट्रक अवैध रूप से पार्क किए गए हैं, जिससे एंबुलेंस और निवासियों का रास्ता रुक गया है।",
                "summary": "अवैध ट्रक पार्किंग के कारण सड़क अवरुद्ध और आपातकालीन वाहनों की आवाजाही प्रभावित।"
            },
            "or": {
                "text": "ରାସ୍ତାର ଦୁଇ ପାଖରେ ବେଆଇନ ଭାବେ ଟ୍ରକ୍ ପାର୍କିଂ କରାଯାଇଛି, ଯାହା ଦ୍ୱାରା ଯାତାୟାତ ବାଧାପ୍ରାପ୍ତ ହେଉଛି।",
                "summary": "ବେଆଇନ ଗାଡ଼ି ପାର୍କିଂ ଯୋଗୁଁ ରାସ୍ତା ଅବରୋଧ ଏବଂ ଜରୁରୀକାଳୀନ ଯାତାୟାତରେ ବାଧା।"
            }
        }
    },
    # 9. Transport
    {
        "category": "Transport",
        "department": "State Road Transport Corporation",
        "priority": "Low",
        "texts": {
            "en": {
                "text": "City buses consistently skipping the scheduled bus stop during morning office hours, leaving commuters stranded.",
                "summary": "Scheduled city bus skipping commuter stop during peak morning peak hours."
            },
            "hi": {
                "text": "सुबह ऑफिस के समय सिटी बसें निर्धारित बस स्टॉप पर नहीं रुक रही हैं, जिससे यात्रियों को परेशानी हो रही है।",
                "summary": "व्यस्त समय में निर्धारित स्टॉप पर बस न रुकने से यात्रियों की असुविधा।"
            },
            "or": {
                "text": "ସକାଳ ସମୟରେ ସିଟି ବସ୍ ଗୁଡ଼ିକ ବସ୍ ଷ୍ଟପ୍‌ରେ ନରହି ଚାଲିଯାଉଛି, ଯାତ୍ରୀମାନେ ଅସୁବିଧାର ସମ୍ମୁଖୀନ ହେଉଛନ୍ତି।",
                "summary": "ବ୍ୟସ୍ତବହୁଳ ସମୟରେ ବସ୍ ଷ୍ଟପ୍ ଛାଡ଼ି ବସ୍ ଚାଲିଯିବା ଯୋଗୁଁ ଯାତ୍ରୀ ଅସନ୍ତୋଷ।"
            }
        }
    },
    # 10. Municipal Services & Property
    {
        "category": "Municipal Services & Property",
        "department": "Municipal Corporation - Revenue & Property",
        "priority": "Low",
        "texts": {
            "en": {
                "text": "Online birth certificate application submitted 25 days ago still marked pending without any officer remarks.",
                "summary": "Birth certificate verification delayed beyond standard service turnaround timeline."
            },
            "hi": {
                "text": "25 दिन पहले दिया गया ऑनलाइन जन्म प्रमाण पत्र आवेदन अभी भी बिना किसी टिप्पणी के लंबित दिखा रहा है।",
                "summary": "जन्म प्रमाण पत्र आवेदन पर 25 दिनों से कोई प्रगति न होने की शिकायत।"
            },
            "or": {
                "text": "୨୫ ଦିନ ତଳେ ଦାଖଲ କରାଯାଇଥିବା ଜନ୍ମ ପ୍ରମାଣପତ୍ର ଆବେଦନ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି କାରଣ ବିନା ବିଚାରାଧୀନ ରହିଛି।",
                "summary": "ଜନ୍ମ ପ୍ରମାଣପତ୍ର ଆବେଦନ ନିର୍ଦ୍ଧାରିତ ସମୟସୀମାଠାରୁ ଅଧିକ ସମୟ ଧରି ବିଚାରାଧୀନ।"
            }
        }
    }
]

AREAS = [
    "Saheed Nagar",
    "Patia",
    "Chandrasekharpur",
    "Old Town",
    "Nayapalli",
    "Khandagiri",
    "Baramunda",
    "Jharpada"
]

CLUSTERS = [
    {
        "id": "DEMO-CLUST-01",
        "category": "Water Supply",
        "department": "Public Health Engineering / Water Board",
        "area": "Patia"
    },
    {
        "id": "DEMO-CLUST-02",
        "category": "Street Lighting",
        "department": "Municipal Corporation - Electrical Department",
        "area": "Nayapalli"
    },
    {
        "id": "DEMO-CLUST-03",
        "category": "Sanitation & Garbage",
        "department": "Municipal Corporation - Solid Waste",
        "area": "Saheed Nagar"
    }
]

def reset_demo_data(conn):
    """Deletes all seeded demo rows, associated history, feedback, and orphaned clusters."""
    c = conn.cursor()
    _exec(c, "SELECT ticket_id FROM grievances WHERE citizen_name LIKE '[Demo]%'")
    rows = c.fetchall()
    tids = [r[0] if not isinstance(r, dict) else r["ticket_id"] for r in rows]

    if tids:
        for tid in tids:
            _exec(c, f"DELETE FROM grievance_feedback WHERE ticket_id = {_ph()}", (tid,))
            _exec(c, f"DELETE FROM grievance_history WHERE ticket_id = {_ph()}", (tid,))
        _exec(c, "DELETE FROM grievances WHERE citizen_name LIKE '[Demo]%'")

    _exec(c, "DELETE FROM clusters WHERE cluster_id NOT IN (SELECT DISTINCT cluster_id FROM grievances WHERE cluster_id IS NOT NULL)")
    conn.commit()
    print(f"Reset complete: Deleted {len(tids)} demo grievances and purged related history/clusters.")

def seed_demo(count: int = 50, reset: bool = False):
    if os.getenv("DEMO_SEED_ALLOWED") == "0":
        print("ERROR: DEMO_SEED_ALLOWED is set to 0. Demo seeding is disabled in this environment.", file=sys.stderr)
        sys.exit(1)

    init_grievance_tables()
    conn = get_conn()
    c = conn.cursor()

    if reset:
        reset_demo_data(conn)

    print(f"Seeding {count} demo civic grievances across Bhubaneswar localities...")

    # Fixed demo PIN for verification testing
    demo_pin = "123456"
    pin_hash = bcrypt.hashpw(demo_pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    now = datetime.utcnow()

    # Pre-calculate counts per status
    # Standard 50-count target: ~12 Submitted, 10 Assigned, 12 In Progress, 12 Resolved, 2 Reopened
    num_sub = max(1, int(round(count * 0.24)))
    num_asg = max(1, int(round(count * 0.20)))
    num_prog = max(1, int(round(count * 0.24)))
    num_res = max(1, int(round(count * 0.24)))
    num_reop = count - (num_sub + num_asg + num_prog + num_res)
    if num_reop < 1:
        num_reop = 1
        num_sub -= 1

    status_plan = (
        ["Submitted"] * num_sub +
        ["Assigned"] * num_asg +
        ["In Progress"] * num_prog +
        ["Resolved"] * num_res +
        ["Reopened"] * num_reop
    )
    random.shuffle(status_plan)

    # Pre-create cluster records
    for cl in CLUSTERS:
        _exec(c, f"""
            INSERT OR REPLACE INTO clusters (cluster_id, department, category, area, report_count, first_reported_at, last_reported_at)
            VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, 0, {_ph()}, {_ph()})
        """, (cl["id"], cl["department"], cl["category"], cl["area"], now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")))

    # Prepare language distribution: 50% en, 25% hi, 25% or
    lang_cycle = ["en", "en", "hi", "or"]

    seeded_tickets = []
    cluster_counts = {cl["id"]: 0 for cl in CLUSTERS}
    resolved_tids = []

    for idx in range(count):
        status = status_plan[idx]
        lang = lang_cycle[idx % len(lang_cycle)]
        tmpl = DEMO_TEMPLATES[idx % len(DEMO_TEMPLATES)]

        category = tmpl["category"]
        dept = tmpl["department"]
        priority = tmpl["priority"]
        area = AREAS[idx % len(AREAS)]

        content = tmpl["texts"].get(lang, tmpl["texts"]["en"])
        orig_text = content["text"]
        summary = content["summary"]
        trans_text = tmpl["texts"]["en"]["text"] if lang != "en" else orig_text

        # Spread created_at across past 14 days
        # Ensure a few unresolved Critical/High tickets are created 5-10 days ago so overdue appears
        is_overdue_candidate = (idx < 5 and priority in ("Critical", "High") and status != "Resolved")
        if is_overdue_candidate:
            days_ago = random.uniform(5.0, 10.0)
        else:
            days_ago = random.uniform(0.1, 13.5)

        created_dt = now - timedelta(days=days_ago)
        created_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")

        sla_hrs = SLA_HOURS.get(priority, 168)
        sla_due_dt = created_dt + timedelta(hours=sla_hrs)
        sla_due_str = sla_due_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Assign cluster to some tickets in matching areas
        assigned_cluster = None
        for cl in CLUSTERS:
            if cl["category"] == category and cl["area"] == area and cluster_counts[cl["id"]] < 6:
                assigned_cluster = cl["id"]
                cluster_counts[cl["id"]] += 1
                break

        # A few tickets marked needs_review = 1
        needs_rev = 1 if (idx % 11 == 0 and status != "Resolved") else 0

        gid = str(uuid.uuid4())
        tid = f"DEMO-{1000 + idx + 1}"
        cit_name = f"[Demo] Citizen {idx + 1}"
        cit_contact = f"900000{idx + 1:04d}"

        # Determine realistic updated_at based on status
        if status == "Submitted":
            updated_dt = created_dt
        elif status == "Assigned":
            updated_dt = created_dt + timedelta(hours=random.uniform(1.0, 4.0))
        elif status == "In Progress":
            updated_dt = created_dt + timedelta(hours=random.uniform(4.0, 18.0))
        elif status == "Resolved":
            updated_dt = created_dt + timedelta(hours=random.uniform(8.0, 48.0))
        else: # Reopened
            updated_dt = created_dt + timedelta(hours=random.uniform(48.0, 96.0))

        updated_str = min(updated_dt, now).strftime("%Y-%m-%d %H:%M:%S")

        _exec(c, f"""
            INSERT INTO grievances (
                id, ticket_id, citizen_name, contact, area, location,
                original_text, summary, language, translated_text, department, category,
                confidence, routing_reason, priority, status, sla_due_at,
                escalation_level, cluster_id, needs_review, pin_hash, created_at, updated_at
            ) VALUES (
                {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
                {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
                {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
                0, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}
            )
        """, (
            gid, tid, cit_name, cit_contact, area, f"{area}, Ward {random.randint(1, 25)}",
            orig_text, summary, lang, trans_text, dept, category,
            round(random.uniform(0.91, 0.98), 2), "Automated civic classifier triage", priority, status, sla_due_str,
            assigned_cluster, needs_rev, pin_hash, created_str, updated_str
        ))

        # Insert History Rows
        # 1. Submitted
        hist_1 = str(uuid.uuid4())
        _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
              (hist_1, tid, "Submitted", "Grievance intake verified via citizen portal", "Citizen", created_str))

        if status in ("Assigned", "In Progress", "Resolved", "Reopened"):
            hist_2 = str(uuid.uuid4())
            t2 = (created_dt + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
            _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (hist_2, tid, "Assigned", f"Assigned to {dept} field division", "System", t2))

        if status in ("In Progress", "Resolved", "Reopened"):
            hist_3 = str(uuid.uuid4())
            t3 = (created_dt + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
            _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (hist_3, tid, "In Progress", "Field inspection crew dispatched to area", "Department Staff", t3))

        if status in ("Resolved", "Reopened"):
            hist_4 = str(uuid.uuid4())
            t4 = (created_dt + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (hist_4, tid, "Resolved", "Repair and maintenance verified complete on site", "Department Staff", t4))
            resolved_tids.append((tid, t4))

        if status == "Reopened":
            hist_5 = str(uuid.uuid4())
            t5 = (created_dt + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
            _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (hist_5, tid, "Reopened", "Citizen reported recurrence of issue", "Citizen", t5))

        seeded_tickets.append(tid)

    # Seed feedback ratings on ~8 resolved tickets
    feedback_ratings = [5, 4, 5, 3, 5, 4, 5, 4]
    for i, rating in enumerate(feedback_ratings):
        if i < len(resolved_tids):
            t_id, t_time = resolved_tids[i]
            fid = str(uuid.uuid4())
            f_comm = "Prompt resolution by municipal staff." if rating >= 4 else "Resolution took longer than expected."
            _exec(c, f"INSERT INTO grievance_feedback (id, ticket_id, rating, comment, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (fid, t_id, rating, f_comm, t_time))

    # Update cluster report counts
    for cl_id, c_count in cluster_counts.items():
        if c_count > 0:
            _exec(c, f"UPDATE clusters SET report_count = {_ph()} WHERE cluster_id = {_ph()}", (c_count, cl_id))
        else:
            _exec(c, f"DELETE FROM clusters WHERE cluster_id = {_ph()}", (cl_id,))

    conn.commit()
    conn.close()

    # Trigger SLA escalation logic to update overdue flags and levels
    escalated_count = run_escalation(now)

    # Fetch stats summary
    stats = get_stats()
    print("\n" + "=" * 50)
    print("DEMO SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print(f"Total Seeded Grievances: {len(seeded_tickets)}")
    print(f"Status Breakdown:        {stats.get('by_status', {})}")
    print(f"Language Breakdown:      {stats.get('by_language', {})}")
    print(f"Overdue Count:           {stats.get('overdue_count', 0)}")
    print(f"Escalated Today:         {escalated_count}")
    print(f"Departments Covered:     {len(stats.get('by_department', {}))}")
    print("-" * 50)
    print(f"Official Demo Tracking PIN: {demo_pin}")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed realistic demo grievances for JanSamadhan.")
    parser.add_argument("--count", type=int, default=50, help="Number of demo tickets to generate (default 50)")
    parser.add_argument("--reset", action="store_true", help="Delete prior demo data before seeding")
    args = parser.parse_args()

    seed_demo(count=args.count, reset=args.reset)

