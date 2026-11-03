import re
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Load all India locations data
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "india_locations.json"
INDIA_LOCATIONS: Dict[str, Any] = {}
if DATA_PATH.exists():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            INDIA_LOCATIONS = json.load(f)
    except Exception as e:
        print(f"Error loading india_locations.json: {e}")

# Build inverted lookup maps
ALL_DISTRICTS_MAP: Dict[str, Tuple[str, str]] = {}  # lowercase district -> (canonical_district, state)
ALL_ALIASES_MAP: Dict[str, Tuple[str, str]] = {}    # lowercase alias -> (canonical_district, state)
STATE_NAMES_MAP: Dict[str, str] = {}                 # lowercase state/alias -> canonical_state

for state, sdata in INDIA_LOCATIONS.items():
    s_clean = state.strip()
    STATE_NAMES_MAP[s_clean.lower()] = s_clean
    
    # State aliases
    if s_clean == "Odisha":
        STATE_NAMES_MAP["orissa"] = "Odisha"
    elif s_clean == "Maharashtra":
        STATE_NAMES_MAP["mh"] = "Maharashtra"
    elif s_clean == "Uttar Pradesh":
        STATE_NAMES_MAP["up"] = "Uttar Pradesh"
    elif s_clean == "Tamil Nadu":
        STATE_NAMES_MAP["tn"] = "Tamil Nadu"
    elif s_clean == "West Bengal":
        STATE_NAMES_MAP["wb"] = "West Bengal"
    elif s_clean == "Madhya Pradesh":
        STATE_NAMES_MAP["mp"] = "Madhya Pradesh"
    elif s_clean == "Andhra Pradesh":
        STATE_NAMES_MAP["ap"] = "Andhra Pradesh"
    elif s_clean == "Jammu and Kashmir":
        STATE_NAMES_MAP["j&k"] = "Jammu and Kashmir"
        STATE_NAMES_MAP["jk"] = "Jammu and Kashmir"

    for d in sdata.get("districts", []):
        d_clean = d.strip()
        ALL_DISTRICTS_MAP[d_clean.lower()] = (d_clean, s_clean)

    for alias, target_dist in sdata.get("aliases", {}).items():
        ALL_ALIASES_MAP[alias.strip().lower()] = (target_dist.strip(), s_clean)

# Native script cities and districts
NATIVE_LOCATIONS: Dict[str, Tuple[str, str]] = {
    # Hindi / Devanagari
    "लखनऊ": ("Lucknow", "Uttar Pradesh"),
    "पुणे": ("Pune", "Maharashtra"),
    "मुंबई": ("Mumbai City", "Maharashtra"),
    "दिल्ली": ("New Delhi", "Delhi"),
    "नई दिल्ली": ("New Delhi", "Delhi"),
    "पटना": ("Patna", "Bihar"),
    "जयपुर": ("Jaipur", "Rajasthan"),
    "कानपुर": ("Kanpur Nagar", "Uttar Pradesh"),
    "वाराणसी": ("Varanasi", "Uttar Pradesh"),
    "बनारस": ("Varanasi", "Uttar Pradesh"),
    "काशी": ("Varanasi", "Uttar Pradesh"),
    "प्रयागराज": ("Prayagraj", "Uttar Pradesh"),
    "इलाहाबाद": ("Prayagraj", "Uttar Pradesh"),
    "आगरा": ("Agra", "Uttar Pradesh"),
    "नोएडा": ("Gautam Buddha Nagar", "Uttar Pradesh"),
    "गाजियाबाद": ("Ghaziabad", "Uttar Pradesh"),
    "गोरखपुर": ("Gorakhpur", "Uttar Pradesh"),
    "अयोध्या": ("Ayodhya", "Uttar Pradesh"),
    "भोपाल": ("Bhopal", "Madhya Pradesh"),
    "इंदौर": ("Indore", "Madhya Pradesh"),
    "पुरी": ("Puri", "Odisha"),
    "कटक": ("Cuttack", "Odisha"),
    "भुवनेश्वर": ("Khurda", "Odisha"),
    "संबलपुर": ("Sambalpur", "Odisha"),
    "गंजाम": ("Ganjam", "Odisha"),
    "बालेश्वर": ("Balasore", "Odisha"),
    # Odia script
    "ପୁରୀ": ("Puri", "Odisha"),
    "କଟକ": ("Cuttack", "Odisha"),
    "ଭୁବନେଶ୍ୱର": ("Khurda", "Odisha"),
    "ସମ୍ବଲପୁର": ("Sambalpur", "Odisha"),
    "ଗଞ୍ଜାମ": ("Ganjam", "Odisha"),
    "ବାଲେଶ୍ୱର": ("Balasore", "Odisha"),
    "ବ୍ରହ୍ମପୁର": ("Ganjam", "Odisha"),
    "ରାଉରକେଲା": ("Sundargarh", "Odisha"),
    "ଅନୁଗୋଳ": ("Angul", "Odisha"),
    "ବଲାଙ୍ଗୀର": ("Bolangir", "Odisha"),
    "ଯାଜପୁର": ("Jajpur", "Odisha"),
    "ଭଦ୍ରକ": ("Bhadrak", "Odisha"),
    # Bengali script
    "কলকাতা": ("Kolkata", "West Bengal"),
    "হাওড়া": ("Howrah", "West Bengal"),
    "শিলিগুড়ি": ("Darjeeling", "West Bengal"),
    # Tamil script
    "சென்னை": ("Chennai", "Tamil Nadu"),
    "கோயம்புத்தூர்": ("Coimbatore", "Tamil Nadu"),
    "மதுரை": ("Madurai", "Tamil Nadu"),
    # Telugu script
    "హైదరాబాద్": ("Hyderabad", "Telangana"),
    "విశాఖపట్నం": ("Visakhapatnam", "Andhra Pradesh"),
    "విజయవాడ": ("NTR", "Andhra Pradesh"),
}

# Generic & State-Specific Departments
STATE_DEPARTMENTS: Dict[str, Dict[str, str]] = {
    "Odisha": {
        "Water Supply": "PHED",
        "Road Infrastructure": "PWD",
        "Electricity": "DISCOM",
        "Sanitation": "Municipal Corporation",
        "Public Health": "Health & Family Welfare",
        "Ration / PDS": "Food Supplies & Consumer Welfare"
    },
    "Maharashtra": {
        "Water Supply": "MJP",
        "Road Infrastructure": "PWD",
        "Electricity": "MSEDCL",
        "Sanitation": "Municipal Corporation (BMC/PMC)",
        "Public Health": "Public Health Department",
        "Ration / PDS": "Food & Civil Supplies"
    },
    "Uttar Pradesh": {
        "Water Supply": "UP Jal Nigam",
        "Road Infrastructure": "PWD",
        "Electricity": "UPPCL",
        "Sanitation": "Nagar Nigam",
        "Public Health": "Medical Health & Family Welfare",
        "Ration / PDS": "Food & Civil Supplies"
    },
    "Delhi": {
        "Water Supply": "Delhi Jal Board",
        "Road Infrastructure": "PWD Delhi",
        "Electricity": "BSES / TPDDL",
        "Sanitation": "MCD",
        "Public Health": "Directorate of Health Services",
        "Ration / PDS": "Food & Supplies Department"
    },
    "Karnataka": {
        "Water Supply": "BWSSB",
        "Road Infrastructure": "PWD",
        "Electricity": "BESCOM",
        "Sanitation": "BBMP",
        "Public Health": "Health and Family Welfare",
        "Ration / PDS": "Food & Civil Supplies"
    },
    "Tamil Nadu": {
        "Water Supply": "TWAD Board",
        "Road Infrastructure": "Highways Department",
        "Electricity": "TANGEDCO",
        "Sanitation": "Greater Chennai Corp",
        "Public Health": "Public Health & Preventive Medicine",
        "Ration / PDS": "Civil Supplies"
    },
    "West Bengal": {
        "Water Supply": "PHE West Bengal",
        "Road Infrastructure": "PWD",
        "Electricity": "WBSEDCL / CESC",
        "Sanitation": "KMC",
        "Public Health": "Health & Family Welfare",
        "Ration / PDS": "Food & Supplies"
    },
    "Telangana": {
        "Water Supply": "HMWSSB",
        "Road Infrastructure": "R&B Department",
        "Electricity": "TSSPDCL",
        "Sanitation": "GHMC",
        "Public Health": "Health, Medical & Family Welfare",
        "Ration / PDS": "Civil Supplies"
    }
}

GENERIC_DEPARTMENTS: Dict[str, str] = {
    "Water Supply": "Water Supply Department",
    "Road Infrastructure": "Public Works Department (PWD)",
    "Electricity": "Electricity Department",
    "Sanitation": "Municipal Corporation",
    "Public Health": "Public Health Department",
    "Ration / PDS": "Food & Civil Supplies Department"
}

def get_department_for_state(category: str, state: str = "Odisha") -> str:
    if state and state in STATE_DEPARTMENTS:
        return STATE_DEPARTMENTS[state].get(category, GENERIC_DEPARTMENTS.get(category, "Public Works"))
    return GENERIC_DEPARTMENTS.get(category, "Public Works")

# Multilingual Category Lexicon
CATEGORY_KEYWORDS = {
    "Water Supply": {
        "dept": "Water Supply Department",
        "keywords": [
            "ପାଣି", "ପାଇପ୍", "ଜଳ", "ପାଇପ", "ନଳକୂପ", "ଫାଟି",
            "पानी", "पाइप", "नल", "जल", "लीक", "दूषित",
            "জল", "পাইপ", "কলের জল", "নলকূপ",
            "నీరు", "పైపు", "తాగునీరు",
            "தண்ணீர்", "குழாய்",
            "पाणी", "पाईप", "नळ", "गढूळ",
            "pani", "paani", "pipe", "pipeline", "leak", "leakage", "drinking water",
            "water supply", "tap water", "water contamination", "ganda pani", "kadua pani",
            "motor pump", "tanker", "low pressure", "water cut", "jol", "phatichi", "asuni", "water"
        ]
    },
    "Road Infrastructure": {
        "dept": "Public Works Department (PWD)",
        "keywords": [
            "ରାସ୍ତା", "ଖାଲ", "ଖାଲଖମା", "ପୋଲ", "ବ୍ରିଜ୍", "ଦୁର୍ଘଟଣା",
            "सड़क", "गड्ढा", "गड्ढे", "पुल", "दुर्घटना", "तारकोल",
            "রাস্তা", "গর্ত", "পুল", "দুর্ঘটনা",
            "రహదారి", "గుంతలు",
            "சாலை", "குழி",
            "रस्ता", "खड्डे", "पूल",
            "rasta", "sadak", "road", "pothole", "potholes", "gaddha", "bridge", "pool",
            "accident", "asphalt", "bitumen", "tar", "cave-in", "traffic", "damaged road",
            "kharap rasta", "gaadi chali paruni", "garta", "speed breaker", "highway"
        ]
    },
    "Electricity": {
        "dept": "Electricity Department",
        "keywords": [
            "ବିଦ୍ୟୁତ୍", "କରେଣ୍ଟ", "ଟ୍ରାନ୍ସଫର୍ମର", "ତାର", "ଆଲୁଅ", "ଅନ୍ଧାର", "ସ୍ପାର୍କ",
            "बिजली", "करंट", "ट्रांसफार्मर", "तार", "अंधेरा", "स्पार्क", "वोल्टेज",
            "বিদ্যুৎ", "কারেন্ট", "ট্রান্সফরমার", "আলো", "অন্ধকার",
            "విద్యుత్", "కరెంట్", "ట్రాన్స్‌ఫార్మర్",
            "மின்சாரம்", "மின்விளக்கு",
            "वीज", "लाईट", "विद्युत",
            "bijli", "bijuli", "current", "power", "light", "transformer", "voltage",
            "power cut", "wire", "spark", "sparking", "dark", "andhera", "andhar",
            "streetlight", "street light", "led", "low voltage", "fuse", "meter",
            "blast", "podigala", "jolche na", "blackout", "load shedding"
        ]
    },
    "Sanitation": {
        "dept": "Municipal Corporation",
        "keywords": [
            "ଅଳିଆ", "ନର୍ଦ୍ଦମା", "ଡ୍ରେନ୍", "ନାଳ", "ସଫେଇ", "ଦୁର୍ଗନ୍ଧ", "ମଶା",
            "कचरा", "नाली", "गंदगी", "सफाई", "बदबू", "मच्छर", "ड्रेनेज",
            "আবর্জনা", "নর্দমা", "ড্রেন", "দুর্গন্ধ", "মশা",
            "చెత్త", "కాలువ",
            "குப்பை", "சாக்கடை",
            "कचरा", "घाण", "नाली",
            "kachra", "garbage", "waste", "drain", "drainage", "sewer", "gutter",
            "naali", "nala", "alia", "nardaama", "badboo", "smell", "gandha", "mosquito",
            "dump", "solid waste", "cleaning", "safai", "overflow", "stagnant"
        ]
    },
    "Public Health": {
        "dept": "Public Health Department",
        "keywords": [
            "ଡାକ୍ତରଖାନା", "ଔଷଧ", "ଡାକ୍ତର", "ରୋଗ", "ଡେଙ୍ଗୁ", "ଜ୍ୱର", "ଇଞ୍ଜେକ୍ସନ",
            "अस्पताल", "दवा", "डॉक्टर", "डेंगू", "मलेरिया", "बीमारी", "इंजेक्शन",
            "হাসপাতাল", "ওষুধ", "ডাক্তার", "ডেঙ্গু", "ম্যালেরিয়া",
            "ఆసుపత్రి", "మందులు", "వైద్యుడు",
            "மருத்துவமனை", "மருந்து",
            "दवाखाना", "रुग्णालय", "औषध", "डॉक्टर",
            "hospital", "doctor", "medicine", "dawa", "dengue", "malaria", "fever",
            "nurse", "injection", "health center", "chc", "phc", "dhh", "treatment", "snake bite"
        ]
    },
    "Ration / PDS": {
        "dept": "Food & Civil Supplies Department",
        "keywords": [
            "ରାସନ", "ଚାଉଳ", "ଗହମ", "ଡିଲର", "କାର୍ଡ",
            "राशन", "चावल", "गेहूं", "डीलर", "कोटा", "राशन कार्ड",
            "রেশন", "চাল", "গম", "রেশন কার্ড",
            "రేషన్", "బియ్యం", "రేషన్ కార్డు",
            "ரேஷன்", "அரிசி",
            "रेशन", "धान्य", "तांदूळ", "रेशन कार्ड",
            "ration", "chaul", "chaula", "chawal", "gehun", "dealer", "quota",
            "ration card", "pds", "fps", "subsidized", "kerosene", "food grains"
        ]
    }
}

def detect_language(text: str) -> str:
    """Multilingual script and token-based language detection."""
    # 1. Native script detection
    if re.search(r'[\u0B00-\u0B7F]', text):
        return "Odia"
    if re.search(r'[\u0980-\u09FF]', text):
        return "Bengali"
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "Telugu"
    if re.search(r'[\u0B80-\u0BFF]', text):
        return "Tamil"

    # Devanagari: Check Marathi vs Hindi
    if re.search(r'[\u0900-\u097F]', text):
        marathi_markers = [
            "\u0933", "\u0931", "\u0972",  # ळ, ऱ, ॲ
            "आहे", "आहेत", "नाही", "नाहीत", "झाले", "झाली", "झाला",
            "केले", "करावे", "करा", "येथे", "रस्ता", "पाणी", "खड्डे",
            "विहीर", "विहिरीतील", "गढूळ", "आरोग्य", "दवाखाना", "वीज",
            "तक्रार", "लवकर", "पाहिजे", "अडकले", "दूषित"
        ]
        if any(m in text for m in marathi_markers):
            return "Marathi"
        return "Hindi"

    # 2. Roman script / Code-mixed text scoring
    words = re.findall(r'[a-zA-Z]+', text.lower())
    
    odia_lexicon = {
        "re", "pain", "hauchhi", "houchi", "heichi", "heigala", "achhi",
        "asuchi", "karantu", "gachha", "pakhare", "chali", "paruni",
        "phatiki", "kadua", "alia", "jamichi", "boluchhanti", "chaula",
        "sakalu", "gandha", "badhuchhanti", "karuchi", "aasa", "asuni",
        "maruchi", "heuchi", "ru", "aji", "pani", "rasta", "poti"
    }
    hindi_lexicon = {
        "hai", "hain", "nahi", "raha", "rahe", "rahi", "hoga", "gaya",
        "gayi", "karo", "sadak", "kachra", "bijli", "bohot", "hume",
        "hamari", "me", "par", "bada", "khamba", "gir", "naali",
        "badboo", "aa", "dukan", "band", "rakhta", "chawal", "dhuwan",
        "fek", "tut", "koi", "bhi", "sakta", "raste", "pani", "samasya", "se"
    }
    bengali_lexicon = {
        "ache", "hoche", "korun", "dhori", "khub", "shob", "sob",
        "rastar", "jolche", "berocche", "nongra", "sobai", "theke",
        "bondho", "raate", "andhokar", "asche", "dhore", "jol", "ganda"
    }
    marathi_roman = {
        "aahe", "nahi", "jhala", "jhali", "kela", "karava", "paani", "rasta", "khadde", "ahe"
    }
    tamil_roman = {
        "illa", "theriyala", "vanthathu", "irukku", "venum", "thanneer", "salai", "kuppai"
    }
    telugu_roman = {
        "ledu", "undi", "ravadam", "cheyandi", "neeru", "roaddhu", "chetha"
    }

    scores = {
        "Odia": sum(1 for w in words if w in odia_lexicon),
        "Hindi": sum(1 for w in words if w in hindi_lexicon),
        "Bengali": sum(1 for w in words if w in bengali_lexicon),
        "Marathi": sum(1 for w in words if w in marathi_roman),
        "Tamil": sum(1 for w in words if w in tamil_roman),
        "Telugu": sum(1 for w in words if w in telugu_roman),
    }

    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    if best_score >= 1:
        return best_lang

    return "English"

def extract_category_and_dept(text: str, state: str = "Odisha") -> Tuple[str, str, float]:
    lower = text.lower()
    scores: Dict[str, int] = {}
    
    for cat, info in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in info["keywords"]:
            if kw in lower or kw in text:
                score += 2 if len(kw) > 4 else 1
        scores[cat] = score

    best_cat, max_score = max(scores.items(), key=lambda x: x[1])
    
    if max_score > 0:
        conf = min(0.98, 0.65 + (max_score * 0.08))
        dept = get_department_for_state(best_cat, state)
        return best_cat, dept, conf
    
    dept = get_department_for_state("Sanitation", state)
    return "Sanitation", dept, 0.50

def extract_urgency(text: str) -> str:
    lower = text.lower()
    if any(k in lower or k in text for k in [
        "died", "death", "blast", "live wire", "spark", "sparking", "fire",
        "emergency", "hospital", "snake bite", "electrocution",
        "ଦୁର୍ଘଟଣା", "ମୃତ୍ୟୁ", "ନିଆଁ", "ସ୍ପାର୍କ", "ଭୟଙ୍କର",
        "मौत", "दुर्घटना", "आग", "ब्लास्ट", "करंट लग",
        "দুর্ঘটনা", "আগুন", "মৃত্যু", "ঝুঁকি"
    ]):
        return "Critical"
    
    if any(k in lower or k in text for k in [
        "accident", "overflow", "blackout", "contamination", "kadua", "dengue",
        "urgent", "immediately", "4 days", "danger",
        "ପାଣି ନାହିଁ", "ଅନ୍ଧାର", "ଖାଲ", "ଡେଙ୍ଗୁ",
        "अंधेरा", "गड्ढा", "दूषित", "सड़", "खराब"
    ]):
        return "High"
    
    if any(k in lower or k in text for k in [
        "not working", "leak", "cleaning", "pothole", "bad smell", "slow", "dim", "week", "since a week",
        "nahi hai", "nahi", "କାମ କରୁନାହିଁ", "ଲିକ", "ସଫା", "ଫାଟିଛି",
        "काम नहीं", "लीक", "सफाई", "धीमा", "नहीं है", "नाही", "नाहीत"
    ]):
        return "Medium"
    
    return "Low"

def extract_location(text: str) -> Dict[str, Any]:
    """
    Robust All-India Location Extractor.
    Extracts city, district, state, village, landmark, ward, or street from free text.
    Returns:
      {
        "has_location": bool,
        "state": str,
        "district": str,
        "area": str
      }
    """
    lower = text.lower()
    
    detected_state: Optional[str] = None
    detected_dist: Optional[str] = None
    detected_area: str = ""
    has_location: bool = False

    # 1. Check Native Script Mappings first (e.g. "लखनऊ", "पुणे", "पुरी", "କଟକ")
    for native_word, (can_dist, can_state) in NATIVE_LOCATIONS.items():
        if native_word in text:
            detected_dist = can_dist
            detected_state = can_state
            has_location = True
            break

    # 2. Check explicitly mentioned State names / acronyms
    if not detected_state:
        for s_key, s_canonical in STATE_NAMES_MAP.items():
            pattern = rf'\b{re.escape(s_key)}\b'
            if re.search(pattern, lower):
                detected_state = s_canonical
                has_location = True
                break

    # 3. Check known aliases (e.g. kothrud -> Pune/Maharashtra, bbsr -> Khurda/Odisha, gomti nagar -> Lucknow/UP)
    for alias, (can_dist, can_state) in ALL_ALIASES_MAP.items():
        pattern = rf'\b{re.escape(alias)}\b'
        if re.search(pattern, lower):
            detected_dist = can_dist
            detected_state = can_state
            if not detected_area or detected_area == f"{can_dist} Central Area":
                detected_area = alias.title()
            has_location = True
            break

    # 4. Check district names across all Indian states
    if not detected_dist:
        for dist_key, (can_dist, can_state) in ALL_DISTRICTS_MAP.items():
            pattern = rf'\b{re.escape(dist_key)}\b'
            if re.search(pattern, lower):
                detected_dist = can_dist
                detected_state = can_state
                has_location = True
                break

    # 5. Extract Area / Landmark from Free Text Patterns
    # a) "Ward N <Optional Name>" e.g. "Ward 12 Kothrud", "Ward 7"
    ward_match = re.search(r'\b(ward\s*(?:no\.?|number)?\s*\d+(?:\s+[a-zA-Z0-9]+)?)\b', text, re.IGNORECASE)
    if ward_match:
        ward_str = ward_match.group(1).title()
        detected_area = ward_str
        has_location = True

    # b) "Near <Landmark>" e.g. "near bus stand", "near civil hospital", "near railway station"
    near_match = re.search(
        r'\b(?:near|close to|opp(?:osite)?(?:\s+to)?|behind|beside|adjacent to)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:in\b|at\b|re\b|me\b|par\b|since\b|for\b|from\b|\d+|$|,|\.|\n))',
        text,
        re.IGNORECASE
    )
    if near_match:
        landmark = near_match.group(1).strip()
        if detected_dist and landmark.lower().endswith(detected_dist.lower()):
            landmark = landmark[:-len(detected_dist)].strip()
        if len(landmark) >= 3 and landmark.lower() not in ["a", "the", "my"]:
            detected_area = f"near {landmark}"
            has_location = True

    # c) Native script near patterns e.g. "ପାଖରେ", "निकट", "पास", "सामने"
    native_near = re.search(r'([^\s,]+)\s*(?:ପାଖରେ|ପାଖ|निकट|पास|सामने|काছে)', text)
    if native_near:
        detected_area = native_near.group(0).strip()
        has_location = True

    # d) Specific landmarks: bus stand, railway station, hospital, market, etc.
    if not detected_area:
        landmark_match = re.search(r'\b(?:bus\s*stand|railway\s*station|metro\s*station|hospital|market|chowk|chhak|bazaar|square|main\s*road|station\s*road)\b', lower)
        if landmark_match:
            lm_text = landmark_match.group(0)
            if "near" in lower:
                detected_area = f"near {lm_text}"
            else:
                detected_area = lm_text.title()
            has_location = True

    # e) Check Devanagari locality like "गोमती नगर"
    if "गोमती नगर" in text or "gomti nagar" in lower:
        detected_area = "गोमती नगर"
        detected_dist = "Lucknow"
        detected_state = "Uttar Pradesh"
        has_location = True

    # If state is known but district not explicitly separate, use city name as district
    if not detected_dist and detected_area:
        # Check if detected_area contains a known city
        for alias, (can_dist, can_state) in ALL_ALIASES_MAP.items():
            if alias in detected_area.lower():
                detected_dist = can_dist
                detected_state = can_state
                break

    # If district is found but no specific area landmark, formulate a clean area
    if detected_dist and not detected_area:
        detected_area = f"{detected_dist} Central Area"

    # Default state if district is known
    if detected_dist and not detected_state:
        dist_entry = ALL_DISTRICTS_MAP.get(detected_dist.lower())
        if dist_entry:
            detected_state = dist_entry[1]
        else:
            detected_state = "Odisha"

    return {
        "has_location": has_location,
        "state": detected_state or "",
        "district": detected_dist or "",
        "area": detected_area or ""
    }

def extract_sentiment(text: str, urgency: str) -> str:
    lower = text.lower()
    if urgency == "Critical":
        return "Urgent"
    if any(w in lower for w in ["died", "injured", "crying", "ill", "sick", "suffering", "child"]):
        return "Distressed"
    if any(w in lower for w in ["daily", "fed up", "kharap", "problem", "angry", "terrible", "4 days", "since a week"]):
        return "Frustrated"
    if any(w in lower for w in ["smell", "dark", "inconvenience", "water cut"]):
        return "Inconvenienced"
    return "Neutral"

def rule_based_extract(text: str) -> Dict[str, Any]:
    """Complete rule-based NLP extraction pipeline for All-India Grievances."""
    lang = detect_language(text)
    loc = extract_location(text)
    state = loc.get("state") or "Odisha"
    cat, dept, conf = extract_category_and_dept(text, state=state)
    urgency = extract_urgency(text)
    sentiment = extract_sentiment(text, urgency)
    
    # Subcategory deduction
    sub_category = f"{cat} Redressal Requirement"
    lower = text.lower()
    if "pothole" in lower or "gaddha" in lower or "ଖାଲ" in lower:
        sub_category = "Potholes & Road Damage"
    elif "pipe" in lower or "leak" in lower or "ଫାଟି" in lower:
        sub_category = "Pipeline Leakage"
    elif "transformer" in lower or "spark" in lower:
        sub_category = "Transformer Failure"
    elif "street light" in lower or "streetlight" in lower:
        sub_category = "Street Light Outage"
    elif "garbage" in lower or "kachra" in lower or "ଅଳିଆ" in lower:
        sub_category = "Garbage Accumulation"
    elif "doctor" in lower or "injection" in lower or "ଡାକ୍ତର" in lower:
        sub_category = "Doctor & Drug Availability"
    elif "dealer" in lower or "quota" in lower or "ରାସନ" in lower:
        sub_category = "PDS Distribution"

    # Summary
    place_str = f" at {loc['area']}, {loc['district']}" if loc.get("has_location") else ""
    summary = f"{urgency} urgency {cat.lower()} issue{place_str}."

    # English translation proxy if native script
    trans_en = text
    if lang != "English":
        trans_en = f"Citizen grievance regarding {sub_category} reported{place_str}."

    return {
        "language": lang,
        "translated_text_en": trans_en,
        "category": cat,
        "sub_category": sub_category,
        "department": dept,
        "urgency": urgency,
        "sentiment": sentiment,
        "location": loc,
        "summary": summary,
        "confidence": conf
    }
