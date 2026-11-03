import re
import hashlib
import numpy as np
from typing import List, Optional
from app.config import settings

# Semantic Concept Bank for Multilingual Civic Redressal
# Maps concepts across Indian languages (Odia, Hindi, Bengali, Telugu, Tamil, Marathi, English)
CONCEPT_CLUSTERS = [
    # Water supply - pipe burst & leakage
    {
        "id": "concept_water_pipe_leak",
        "terms": [
            "water", "drinking water", "tap", "pipe", "pipeline", "burst", "leak", "broken",
            "pani", "peene ka pani", "paani", "phatiki", "leakage", "phuti",
            "ପିଇବା ପାଣି", "ପାଣି", "ପାଇପ୍", "ଫାଟି", "ଲିକ୍",
            "पीने का पानी", "पानी", "पाइप", "फूट", "टूटी", "लीक",
            "পানীয় জল", "জল", "পাইপ", "ফেটে", "লিক",
            "తాగునీరు", "నీరు", "పైపు", "లీకేజ్",
            "குடிநீர்", "தண்ணீர்", "குழாய்", "கசிவு",
            "पिण्याचे पाणी", "पाणी", "पाईप", "गळती"
        ]
    },
    # Water supply - contamination & muddy water
    {
        "id": "concept_water_contamination",
        "terms": [
            "muddy", "dirty", "contaminated", "foul smell", "yellow", "brown", "germs", "smell",
            "kadua", "ganda", "badboo", "durgandh",
            "କାଦୁଅ", "ଦୁର୍ଗନ୍ଧ", "ମଇଳା", "ଅପରିଷ୍କାର",
            "गंदा", "कीचड़", "बदबू", "दूषित", "दुर्गंध",
            "ঘোলা", "নোংরা", "দুর্গন্ধ",
            "కలుషిత", "బురద", "దుర్వాసన",
            "கலங்கிய", "துர்நாற்றம்",
            "गढूळ", "घाणेरडे"
        ]
    },
    # Road - potholes & accidents
    {
        "id": "concept_road_pothole",
        "terms": [
            "road", "pothole", "potholes", "crater", "accident", "highway", "street", "damage",
            "rasta", "sadak", "gaddha", "khadde", "khalakhama",
            "ରାସ୍ତା", "ଖାଲଖମା", "ଖାଲ", "ଦୁର୍ଘଟଣା",
            "सड़क", "गड्ढा", "गड्ढे", "दुर्घटना",
            "রাস্তা", "গর্ত", "দুর্ঘটনা",
            "రహదారి", "రోడ్డు", "గుంతలు", "ప్రమాదం",
            "சாலை", "குழி", "விபத்து",
            "रस्ता", "खड्डे", "अपघात"
        ]
    },
    # Electricity - transformer & power cuts
    {
        "id": "concept_power_outage_transformer",
        "terms": [
            "electricity", "power", "transformer", "spark", "sparking", "blast", "fire", "wire", "blackout", "dark",
            "bijli", "current", "andhera", "andhokar", "karant",
            "ବିଦ୍ୟୁତ୍", "ଟ୍ରାନ୍ସଫର୍ମର", "ପୋଡ଼ି", "ତାର", "ଅନ୍ଧାର",
            "बिजली", "ट्रांसफार्मर", "जल गया", "चिंगारी", "अंधेरा", "तार",
            "বিদ্যুৎ", "ট্রান্সফরমার", "অন্ধকার", "আগুন",
            "విద్యుత్", "కరెంట్", "ట్రాన్స్‌ఫార్మర్", "చీకటి",
            "மின்சாரம்", "டிரான்ஸ்பார்மர்", "இருட்டு",
            "वीज", "ट्रान्सफॉर्मर", "अंधार"
        ]
    },
    # Sanitation - garbage & drain overflow
    {
        "id": "concept_sanitation_garbage_drain",
        "terms": [
            "garbage", "waste", "drain", "drainage", "sewer", "gutter", "overflow", "mosquito",
            "kachra", "alia", "naali", "masha", "macchar",
            "ଅଳିଆ", "ନର୍ଦ୍ଦମା", "ମଶା", "ଦୁର୍ଗନ୍ଧ", "ଜମି",
            "कचरा", "नाली", "गंदगी", "मच्छर", "सड़ांध",
            "ময়লা", "ড্রেন", "নর্দমা", "মশা",
            "చెత్త", "కాలువ", "దోమలు",
            "குப்பை", "சாக்கடை", "கொசு",
            "कचरा", "गटार", "डास"
        ]
    },
    # Public Health - hospital & medicine
    {
        "id": "concept_health_hospital_medicine",
        "terms": [
            "hospital", "doctor", "medicine", "injection", "anti-rabies", "snake bite", "emergency", "clinic",
            "daktar", "chikitsa", "oushadha", "dawai",
            "ହସ୍ପିଟାଲ", "ଡାକ୍ତର", "ଔଷଧ", "ଚିକିତ୍ସା", "ସାପ କାମୁଡ଼ା",
            "अस्पताल", "डॉक्टर", "दवा", "सुई", "इंजेक्शन", "इलाज",
            "হাসপাতাল", "ডাক্তার", "ওষুধ",
            "ఆసుపత్రి", "వైద్యుడు", "మందులు",
            "மருத்துவமனை", "மருத்துவர்", "மருந்து",
            "रुग्णालय", "डॉक्टर", "औषध"
        ]
    },
    # PDS / Ration
    {
        "id": "concept_ration_pds",
        "terms": [
            "ration", "dealer", "pds", "rice", "wheat", "food grain", "biometric", "quota",
            "chawal", "chaula", "rashan",
            "ରାସନ", "ଡିଲର", "ଚାଉଳ", "କୋଟା",
            "राशन", "डीलर", "चावल", "गेहूं", "कोटा",
            "রেশন", "ডিলার", "চাল",
            "రేషన్", "డీలర్", "బియ్యం",
            "ரேஷன்", "அரிசி",
            "रेशन", "धान्य"
        ]
    }
]

# Ward & Number Normalization (Indian numerals to standard digits)
NUMERAL_MAP = {
    '୦': '0', '୧': '1', '୨': '2', '୩': '3', '୪': '4',
    '୫': '5', '୬': '6', '୭': '7', '୮': '8', '୯': '9',
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
    '౦': '0', '౧': '1', '౨': '2', '౩': '3', '౪': '4',
    '౫': '5', '౬': '6', '౭': '7', '౮': '8', '౯': '9',
}

DIMENSION = 384

def _normalize_numerals(text: str) -> str:
    res = []
    for ch in text:
        res.append(NUMERAL_MAP.get(ch, ch))
    return "".join(res)

def _hash_to_vector(token: str, dim: int = DIMENSION) -> np.ndarray:
    """Deterministic pseudo-random vector for an out-of-cluster subword token."""
    h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
    rng = np.random.RandomState(h % (2**32))
    v = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(v)
    return v / (norm + 1e-9)

# Pre-generate basis vectors for each concept cluster
CONCEPT_BASIS: List[np.ndarray] = []
for i, cluster in enumerate(CONCEPT_CLUSTERS):
    rng = np.random.RandomState(42000 + i)
    v = rng.standard_normal(DIMENSION).astype(np.float32)
    v = v / (np.linalg.norm(v) + 1e-9)
    CONCEPT_BASIS.append(v)

def local_multilingual_embedding(text: str) -> np.ndarray:
    """
    Local Multilingual Embedding Fallback (Multilingual Concept & Subword Projection).
    Produces cross-lingual semantic embeddings aligned across Odia, Hindi, Bengali,
    Telugu, Tamil, Marathi, and English without requiring heavy external model weights.
    """
    clean_text = _normalize_numerals(text.lower())
    vec = np.zeros(DIMENSION, dtype=np.float32)
    matches_found = 0

    # 1. Concept activations across all supported languages
    for idx, cluster in enumerate(CONCEPT_CLUSTERS):
        cluster_hits = 0
        for term in cluster["terms"]:
            term_clean = term.lower()
            if term_clean in clean_text:
                cluster_hits += 1
        if cluster_hits > 0:
            weight = np.log1p(cluster_hits) * 2.5
            vec += weight * CONCEPT_BASIS[idx]
            matches_found += 1

    # 2. Ward / Area number identification (e.g. Ward 7, Ward 4)
    ward_match = re.search(r'(?:ward|ୱାର୍ଡ|वार्ड|ওয়ার্ড|వార్డు|வார்டு)\s*(\d+)', clean_text, re.IGNORECASE)
    if ward_match:
        ward_num = int(ward_match.group(1))
        ward_token = f"entity_ward_{ward_num}"
        ward_vec = _hash_to_vector(ward_token, DIMENSION)
        vec += 3.0 * ward_vec
        matches_found += 1

    # 3. Known city/district entity activations
    districts = [
        ("ganjam", ["ganjam", "berhampur", "brahmapur", "ବ୍ରହ୍ମପୁର", "ଗଞ୍ଜାମ", "ब्रह्मपुर", "गंजम"]),
        ("khurda", ["khurda", "khordha", "bhubaneswar", "ଭୁବନେଶ୍ୱର", "ଖୋର୍ଦ୍ଧା", "भुवनेश्वर"]),
        ("cuttack", ["cuttack", "କଟକ", "कटक", "badambadi", "ବାଦାମବାଡ଼ି"]),
        ("sambalpur", ["sambalpur", "ସମ୍ବଲପୁର", "संबलपुर"]),
        ("sundargarh", ["sundargarh", "rourkela", "ରାଉରକେଲା", "राउरकेला"]),
        ("puri", ["puri", "ପୁରୀ", "पुरी"]),
        ("balasore", ["balasore", "ବାଲେଶ୍ୱର", "बालेश्वर"])
    ]
    for dist_id, dist_terms in districts:
        if any(dt in clean_text for dt in dist_terms):
            dist_vec = _hash_to_vector(f"entity_district_{dist_id}", DIMENSION)
            vec += 2.5 * dist_vec
            matches_found += 1

    # 4. Fallback subword character n-grams
    ngrams = re.findall(r'[a-zA-Z\u0B00-\u0B7F\u0900-\u097F\u0980-\u09FF\u0C00-\u0C7F\u0B80-\u0BFF]{3,6}', clean_text)
    for ng in ngrams[:12]:
        vec += 0.15 * _hash_to_vector(f"subword_{ng}", DIMENSION)

    norm = np.linalg.norm(vec)
    if norm < 1e-9:
        return _hash_to_vector(clean_text, DIMENSION)
    return vec / norm

def get_embedding(text: str) -> np.ndarray:
    """
    Returns multilingual embedding vector.
    Tries Gemini text-embedding-004 first if client is available;
    falls back cleanly to local multilingual semantic projection.
    """
    from ai.gemini_client import embed_content
    gemini_vec = embed_content(text)
    if gemini_vec is not None and len(gemini_vec) > 0:
        arr = np.array(gemini_vec, dtype=np.float32)
        norm = np.linalg.norm(arr)
        return arr / (norm + 1e-9) if norm > 1e-9 else arr

    return local_multilingual_embedding(text)

def compute_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    sim = np.dot(v1, v2) / (n1 * n2)
    return float(np.clip(sim, 0.0, 1.0))

