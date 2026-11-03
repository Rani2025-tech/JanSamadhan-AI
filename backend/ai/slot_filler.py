import json
from typing import Dict, Any, Tuple, Optional
from .extractor import extract
from .rag import rag_engine
from .classifier import extract_location, get_department_for_state

class SlotFillingAssistant:
    def __init__(self):
        # Mandatory logical slots required before filing
        self.mandatory_slots = ["issue", "category", "location"]

    def process_turn(
        self,
        user_message: str,
        current_state: str,
        existing_slots: Dict[str, Any],
        language: str = "or"
    ) -> Tuple[str, str, Dict[str, Any], bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]], bool]:
        """
        Processes conversational interaction with All-India slot-filling logic.
        Returns:
          (reply_text, next_state, updated_slots, ready_to_file, confirmation_card, detected_faq, suggest_human_agent)
        """
        text_lower = user_message.strip().lower()

        # 1. Check if this is an FAQ inquiry using Multilingual RAG
        faq_match = rag_engine.search_faq(user_message)
        
        # 2. Check if user is confirming a pending card
        is_confirmation = any(w in text_lower for w in [
            "yes", "confirm", "file", "proceed", "submit", "ok", "sure", "done",
            "हाँ", "हा", "हाँ दर्ज करें", "ठीक है", "ঠিক আছে", "হ্যাঁ", "ହଁ", "ଠିକ୍ ଅଛି", "ଦାଖଲ କରନ୍ତୁ",
            "avunu", "sari", "ho", "ahe", "chaleel"
        ])

        if current_state == "confirming" and is_confirmation:
            # User confirmed! Ready to file
            reply = self._get_localized_text("filing_success", language)
            return (reply, "filed", existing_slots, True, existing_slots, faq_match, False)

        # 3. Extract entities from user utterance
        extraction = extract(user_message)
        
        # Determine response language: align with detected language if regional script
        lang_code_map = {
            "Odia": "or", "Hindi": "hi", "Bengali": "bn", "Marathi": "mr",
            "Tamil": "ta", "Telugu": "te", "English": "en"
        }
        effective_lang = language
        if extraction.language in ["Hindi", "Odia", "Bengali", "Marathi", "Tamil", "Telugu"]:
            effective_lang = lang_code_map.get(extraction.language, language)

        # Merge slots
        updated_slots = dict(existing_slots)
        
        if not updated_slots.get("category"):
            updated_slots["category"] = extraction.category
            
        if not updated_slots.get("urgency"):
            updated_slots["urgency"] = extraction.urgency

        if not updated_slots.get("issue"):
            # If user message has substantive issue content (> 8 chars and not pure location name)
            if len(user_message.strip()) > 8 and not (extraction.location.get("has_location") and len(user_message.split()) <= 3):
                updated_slots["issue"] = user_message.strip()
                updated_slots["summary"] = extraction.summary
                updated_slots["translated_text_en"] = extraction.translated_text_en
                updated_slots["sentiment"] = extraction.sentiment
            elif not updated_slots.get("issue"):
                updated_slots["issue"] = user_message.strip()

        # 4. Location extraction & slot resolution
        # Check current extraction location first, then direct text fallback
        loc = extraction.location or {}
        if not loc.get("has_location"):
            # Check directly via location classifier
            loc = extract_location(user_message)

        if loc.get("has_location"):
            if loc.get("state") and not updated_slots.get("state"):
                updated_slots["state"] = loc["state"]
            if loc.get("district") and not updated_slots.get("district"):
                updated_slots["district"] = loc["district"]
            if loc.get("area") and not updated_slots.get("area"):
                updated_slots["area"] = loc["area"]
            elif not updated_slots.get("area") and loc.get("district"):
                updated_slots["area"] = f"{loc['district']} Central Area"

        # Determine location completeness:
        # Location slot is filled if ANY recognisable place (city, district, state, village, landmark) is present
        has_filled_location = bool(
            (updated_slots.get("district") and updated_slots.get("area")) or
            (updated_slots.get("district")) or
            (updated_slots.get("area") and updated_slots.get("state")) or
            (loc.get("has_location"))
        )

        # Default state if district is known
        if updated_slots.get("district") and not updated_slots.get("state"):
            if loc.get("state"):
                updated_slots["state"] = loc["state"]
            else:
                updated_slots["state"] = "Odisha"

        # Set appropriate department for category & state
        current_state_name = updated_slots.get("state") or "Odisha"
        updated_slots["department"] = get_department_for_state(
            updated_slots.get("category", "Water Supply"),
            state=current_state_name
        )

        # 5. Evaluate slot completeness
        missing_slots = []
        if not updated_slots.get("issue"):
            missing_slots.append("issue")
        if not has_filled_location:
            missing_slots.append("location")

        # 6. Formulate response based on missing slots
        suggest_human = (extraction.confidence < 0.60)
        human_offer_suffix = ""
        if suggest_human:
            offers = {
                "or": "\n\n💡 ଆପଣ ଚାହିଁଲେ ସିଧାସଳଖ ଜଣେ ଅଧିକାରୀଙ୍କ ସହ କଥା ହୋଇପାରିବେ (ହେଲ୍ପଲାଇନ୍: 1800-123-4567)।",
                "hi": "\n\n💡 आप चाहें तो सीधे किसी मानव अधिकारी से बात कर सकते हैं (हेल्पलाइन: 1800-123-4567)।",
                "bn": "\n\n💡 আপনি চাইলে সরাসরি একজন মানব কর্মকর্তার সাথে কথা বলতে পারেন (হেল্পলাইন: 1800-123-4567)।",
                "en": "\n\n💡 Need extra help? You can tap 'Talk to a Human Officer' or call our toll-free helpline 1800-123-4567."
            }
            human_offer_suffix = offers.get(effective_lang, offers["en"])

        if not missing_slots:
            # All slots are present! Present the confirmation card
            reply = self._get_localized_text("ask_confirmation", effective_lang, updated_slots) + (human_offer_suffix if suggest_human else "")
            
            district_val = updated_slots.get("district") or loc.get("district") or "Central"
            area_val = updated_slots.get("area") or loc.get("area") or f"{district_val} Central Area"
            state_val = updated_slots.get("state") or loc.get("state") or "Odisha"

            confirmation_card = {
                "title": updated_slots.get("issue", "Civic Grievance")[:60],
                "description": updated_slots.get("issue", ""),
                "category": updated_slots.get("category", "Water Supply"),
                "department": updated_slots.get("department", "Public Works"),
                "urgency": updated_slots.get("urgency", "Medium"),
                "state": state_val,
                "district": district_val,
                "area": area_val,
                "language": extraction.language
            }
            return (reply, "confirming", updated_slots, False, confirmation_card, faq_match, suggest_human)

        elif "issue" in missing_slots:
            reply = self._get_localized_text("ask_issue", effective_lang) + (human_offer_suffix if suggest_human else "")
            return (reply, "collecting_info", updated_slots, False, None, faq_match, suggest_human)

        elif "location" in missing_slots:
            reply = self._get_localized_text("ask_location", effective_lang)
            return (reply, "awaiting_location", updated_slots, False, None, faq_match, suggest_human)

        reply = "Please share more details about your grievance." + (human_offer_suffix if suggest_human else "")
        return (reply, "collecting_info", updated_slots, False, None, faq_match, suggest_human)

    def _get_localized_text(self, template_key: str, lang: str, slots: Optional[Dict[str, Any]] = None) -> str:
        s = slots or {}
        lang = lang.lower()

        templates = {
            "ask_location": {
                "or": "ଆପଣଙ୍କ ଅଭିଯୋଗଟି କେଉଁ ଜିଲ୍ଲା ବା ସହରରେ (ଯଥା: ପୁରୀ, ଭୁବନେଶ୍ୱର, କଟକ, ଗଞ୍ଜାମ, ପୁଣେ, ଲକ୍ଷ୍ନୌ)? ଦୟାକରି ଜିଲ୍ଲା ବା ସହରର ନାମ ଲେଖନ୍ତୁ।",
                "hi": "आपकी शिकायत किस जिले या शहर (जैसे: लखनऊ, पुणे, मुंबई, कटक, दिल्ली, पुरी) से संबंधित है? कृपया जिले या शहर का नाम बताएं।",
                "bn": "আপনার অভিযোগটি কোন জেলা বা শহরের (যেমন: কলকাতা, হাওড়া, কটক, পুরী)? দয়া করে জেলা বা শহরের নাম লিখুন।",
                "mr": "आपली तक्रार कोणत्या जिल्हा किंवा शहराशी संबंधित आहे (उदा. पुणे, मुंबई, नागपूर, नाशिक)? कृपया जिल्हा किंवा शहराचे नाव सांगा.",
                "ta": "உங்கள் புகார் எந்த மாவட்டம் அல்லது நகரத்தைச் சேர்ந்தது (எ.கா. சென்னை, கோயம்புத்தூர், மதுரை)? மாவட்டத்தின் பெயரை குறிப்பிடவும்.",
                "te": "మీ ఫిర్యాదు ఏ జిల్లా లేదా నగరానికి సంబంధించినది (ఉదా. హైదరాబాద్, విశాఖపట్నం, విజయవాడ)? దయచేసి జిల్లా లేదా నగరం పేరు పేర్కొనండి.",
                "en": "Which district or city is this grievance located in (e.g. Puri, Pune, Lucknow, Bengaluru, Mumbai)?"
            },
            "ask_issue": {
                "or": "ଦୟାକରି ଆପଣଙ୍କ ନାଗରିକ ସମସ୍ୟା ବିଷୟରେ ବିସ୍ତୃତ ଭାବେ ଲେଖନ୍ତୁ, ଯାହାଦ୍ୱାରା ଏହାକୁ ସଠିକ୍ ବିଭାଗକୁ ପଠାଯାଇପାରିବ।",
                "hi": "कृपया अपनी नागरिक समस्या का विस्तार से वर्णन करें ताकि इसे सही विभाग को भेजा जा सके।",
                "bn": "আপনার নাগরিক অভিযোগটি বিস্তারিতভাবে বর্ণনা করুন যাতে সংশ্লিষ্ট বিভাগে পাঠানো যায়।",
                "mr": "कृपया आपल्या नागरी समस्येचे सविस्तर वर्णन करा जेणेकरून ती संबंधित विभागाकडे पाठवता येईल.",
                "ta": "சம்பந்தப்பட்ட துறைக்கு அனுப்ப உங்கள் புகாரை விரிவாக விவரிக்கவும்.",
                "te": "దయచేసి మీ పౌర సమస్యను వివరంగా వివరించండి, తద్వారా సంబంధిత విభాగానికి పంపవచ్చు.",
                "en": "Please describe your civic grievance in detail so we can route it to the appropriate department."
            },
            "ask_confirmation": {
                "or": f"ମୁଁ ଆପଣଙ୍କ ଅଭିଯୋଗ ବିବରଣୀ ପ୍ରସ୍ତୁତ କରିଛି:\n• ବିଭାଗ: {s.get('department')}\n• ଶ୍ରେଣୀ: {s.get('category')}\n• ସ୍ଥାନ: {s.get('area')}, {s.get('district')} ({s.get('state', 'Odisha')})\n• ଜରୁରୀକାଳୀନତା: {s.get('urgency')}\n\nଏହି ଅଭିଯୋଗ ଦାଖଲ କରିବାକୁ 'ହଁ' ଲେଖନ୍ତୁ କିମ୍ବା ତଳେ ଥିବା ବଟନ କ୍ଲିକ୍ କରନ୍ତୁ।",
                "hi": f"मैंने आपकी शिकायत का विवरण तैयार कर लिया है:\n• विभाग: {s.get('department')}\n• श्रेणी: {s.get('category')}\n• स्थान: {s.get('area')}, {s.get('district')} ({s.get('state', 'India')})\n• प्राथमिकता: {s.get('urgency')}\n\nक्या आप इस शिकायत को आधिकारिक रूप से दर्ज करना चाहते हैं? कृपया 'हाँ' कहें या नीचे पुष्टि बटन दबाएं।",
                "bn": f"আপনার অভিযোগ বিবরণ তৈরি করা হয়েছে:\n• বিভাগ: {s.get('department')}\n• বিষয়: {s.get('category')}\n• অবস্থান: {s.get('area')}, {s.get('district')} ({s.get('state', 'India')})\n\nঅভিযোগটি জমা করতে 'হ্যাঁ' লিখুন অথবা নিচের বোতাম চাপুন।",
                "mr": f"मी आपल्या तक्रारीचा तपशील तयार केला आहे:\n• विभाग: {s.get('department')}\n• श्रेणी: {s.get('category')}\n• ठिकाण: {s.get('area')}, {s.get('district')} ({s.get('state', 'Maharashtra')})\n• प्राधान्य: {s.get('urgency')}\n\nतक्रार दाखल करण्यासाठी 'हो' म्हणा किंवा पुष्टी बटण दाबा.",
                "ta": f"உங்கள் புகார் விவரங்கள்:\n• துறை: {s.get('department')}\n• வகை: {s.get('category')}\n• இடம்: {s.get('area')}, {s.get('district')}\n\nபுகாரை பதிவு செய்ய 'ஆம்' என பதிலளிக்கவும்.",
                "te": f"మీ ఫిర్యాదు వివరాలు సిద్ధంగా ఉన్నాయి:\n• విభాగం: {s.get('department')}\n• వర్గం: {s.get('category')}\n• ప్రాంతం: {s.get('area')}, {s.get('district')}\n\nనమోదు చేయడానికి 'అవును' అని చెప్పండి.",
                "en": f"I have prepared your grievance details:\n• Department: {s.get('department')}\n• Category: {s.get('category')}\n• Location: {s.get('area')}, {s.get('district')} ({s.get('state', 'India')})\n• Urgency: {s.get('urgency')}\n\nWould you like to register this ticket? Reply 'Yes' or click the confirmation button."
            },
            "filing_success": {
                "or": "ଧନ୍ୟବାଦ! ଆପଣଙ୍କ ଅଭିଯୋଗ ସଫଳତାର ସହ ଦାଖଲ ହୋଇଛି। ଆପଣଙ୍କୁ ଏକ ଅଫିସିଆଲ ଟ୍ରାକିଂ ନମ୍ବର (GRV) ପ୍ରଦାନ କରାଯାଉଛି।",
                "hi": "धन्यवाद! आपकी शिकायत सफलतापूर्वक दर्ज कर ली गई है। आपको एक आधिकारिक ट्रैकिंग आईडी (GRV) जारी की जा रही है।",
                "bn": "ধন্যবাদ! আপনার অভিযোগ সফলভাবে নথিভুক্ত করা হয়েছে। আপনাকে একটি ট্র্যাকিং নম্বর (GRV) প্রদান করা হচ্ছে।",
                "mr": "धन्यवाद! आपली तक्रार यशस्वीरीत्या नोंदवली गेली आहे. आपल्याला अधिकृत ट्रॅकिंग क्रमांक (GRV) दिला जात आहे.",
                "ta": "நன்றி! உங்கள் புகார் வெற்றிகரமாக பதிவு செய்யப்பட்டுள்ளது.",
                "te": "ధన్యవాదాలు! మీ ఫిర్యాదు విజయవంతంగా నమోదైంది.",
                "en": "Thank you! Your grievance has been officially registered. Generating your tracking ticket..."
            }
        }

        lang_templates = templates.get(template_key, {})
        # Map or-IN, hi-IN, etc. to base code
        base_lang = lang.split("-")[0] if "-" in lang else lang
        return lang_templates.get(base_lang, lang_templates.get("en", "Please provide more details."))

slot_filling_assistant = SlotFillingAssistant()
