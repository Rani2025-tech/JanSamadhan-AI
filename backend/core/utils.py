import os
from dotenv import load_dotenv
try:
    from langdetect import detect
except Exception:
    detect = None

load_dotenv()

DATA_PATH        = os.getenv("DATA_PATH", "data/")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")

def get_all_pdfs() -> list:
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        return []
    pdfs = [
        os.path.join(DATA_PATH, f)
        for f in os.listdir(DATA_PATH)
        if f.endswith(".pdf")
    ]
    return pdfs

def faiss_index_exists() -> bool:
    return os.path.exists(FAISS_INDEX_PATH)

def ensure_folders():
    for folder in [DATA_PATH, FAISS_INDEX_PATH]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")

def detect_language(text: str) -> str:
    """Detect language of input text. Returns 'en', 'hi', or 'or'."""
    try:
        lang = detect(text)
        if lang == "hi":
            return "hi"
        elif lang in ["or", "te", "kn", "bn"]:
            # Check for Odia script characters
            odia_chars = ["ର", "େ", "ଷ", "ଟ", "ଲ", "ଫ", "କ", "ତ", "ଅ", "ଆ", "ଇ", "ଈ", "ଉ", "ଊ", "ଏ", "ଐ", "ଓ", "ଔ"]
            if any(char in text for char in odia_chars):
                return "or"
            return "en"
        else:
            return "en"
    except:
        # Fallback: check for Odia script
        odia_chars = ["ର", "େ", "ଷ", "ଟ", "ଲ", "ଫ", "କ", "ତ", "ଅ", "ଆ", "ଇ", "ଈ", "ଉ", "ଊ", "ଏ", "ଐ", "ଓ", "ଔ"]
        if any(char in text for char in odia_chars):
            return "or"
        return "en"

def get_language_name(lang_code: str) -> str:
    mapping = {
        "en": "English",
        "hi": "Hindi",
        "or": "Odia",
        "mr": "Marathi",
        "te": "Telugu",
        "ta": "Tamil",
        "bn": "Bengali"
    }
    return mapping.get(lang_code, "English")