import json
import logging
from typing import Dict, Any
from app.schemas import AIExtractionResult
from .gemini_client import gemini_client
from .classifier import rule_based_extract

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are JanSamadhan AI, the official grievance redressal classification and intelligence engine for citizens across India.
Analyze the citizen grievance input (which may be written in Odia, Hindi, Bengali, Telugu, Tamil, Marathi, English, or Romanized transliterations such as Hinglish or Odishlish).

You MUST output ONLY a valid JSON object matching this exact schema:
{
  "language": "string (Odia, Hindi, Bengali, Telugu, Tamil, Marathi, English)",
  "translated_text_en": "string (fluent, accurate English translation)",
  "category": "string (Water Supply, Road Infrastructure, Electricity, Sanitation, Public Health, Ration / PDS)",
  "sub_category": "string (specific issue name)",
  "department": "string (state-specific or generic public authority, e.g. PHED, PWD, DISCOM, UPPCL, MSEDCL, Municipal Corporation, Health & Family Welfare, Food & Civil Supplies)",
  "urgency": "string (Low, Medium, High, Critical)",
  "sentiment": "string (Frustrated, Distressed, Urgent, Inconvenienced, Neutral)",
  "location": {
    "state": "string (Indian state or UT, e.g. Odisha, Maharashtra, Uttar Pradesh, Delhi, Karnataka)",
    "district": "string (district or major city, e.g. Puri, Pune, Lucknow, Bengaluru, Mumbai, Cuttack)",
    "area": "string (locality, ward, street, landmark, e.g. near bus stand, Ward 12 Kothrud, Gomti Nagar)",
    "has_location": true
  },
  "summary": "string (one concise sentence in English summarizing the civic problem)",
  "confidence": 0.95
}
If NO recognisable place (no city, district, state, village, or landmark) is mentioned, set "location": {"has_location": false, "state": "", "district": "", "area": ""}.
Do not include any markdown wrappers or commentary, return ONLY the raw JSON object."""

def extract(text: str) -> AIExtractionResult:
    """Extract structured grievance data using Gemini with fallback to rule-based classifier."""
    if not text or not text.strip():
        # Fallback for empty
        fallback_data = rule_based_extract("General citizen inquiry")
        return AIExtractionResult(**fallback_data)

    if gemini_client.is_available:
        for attempt in range(2):
            try:
                prompt = f"Citizen Grievance Text:\n\"\"\"\n{text}\n\"\"\"\nProvide the JSON analysis."
                response_text = gemini_client.generate_content(prompt, system_instruction=SYSTEM_PROMPT)
                
                if response_text:
                    cleaned = response_text.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    cleaned = cleaned.strip()
                    
                    data = json.loads(cleaned)
                    return AIExtractionResult(**data)
            except Exception as e:
                logger.warning(f"Gemini extraction attempt {attempt+1} failed: {e}")

    # Fallback to high-precision multilingual rule-based extraction
    logger.info("Using rule-based extraction fallback.")
    fallback_dict = rule_based_extract(text)
    return AIExtractionResult(**fallback_dict)

