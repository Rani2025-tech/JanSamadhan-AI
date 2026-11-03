import re

def mask_phone_numbers(text: str) -> str:
    """
    Backwards-compatible alias for sanitize_pii.
    Masks phone numbers, 12-digit ID numbers, and email addresses.
    """
    return sanitize_pii(text)

def sanitize_pii(text: str) -> str:
    """
    Masks sensitive Personally Identifiable Information (PII) before
    any content is transmitted to external AI models or LLM providers.
    Masks:
      1. Indian mobile phone numbers (+91, 10-digit 6-9xxxxxxxxx, toll-free 1800-xxx-xxxx)
      2. 12-digit national ID numbers (e.g. Aadhaar 12-digit continuous or 4-4-4 grouped)
      3. Email addresses
    """
    if not text:
        return text

    # 1. Email addresses
    pattern_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    masked = re.sub(pattern_email, '[EMAIL_REDACTED]', text)

    # 2. 12-digit ID numbers (e.g. Aadhaar 4-4-4 grouped or 12 continuous digits)
    pattern_12digit_grouped = r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'
    pattern_12digit_continuous = r'\b\d{12}\b'
    masked = re.sub(pattern_12digit_grouped, '[ID_12DIGIT_REDACTED]', masked)
    masked = re.sub(pattern_12digit_continuous, '[ID_12DIGIT_REDACTED]', masked)

    # 3. Phone numbers (+91 prefix, 10-digit starting with 6-9, spaced/hyphenated)
    pattern_with_prefix = r'(?:\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}'
    pattern_standalone = r'\b[6-9]\d{9}\b'
    pattern_toll_free = r'\b1800[\s\-]?\d{3}[\s\-]?\d{4}\b'

    masked = re.sub(pattern_with_prefix, '[PHONE_MASKED]', masked)
    masked = re.sub(pattern_standalone, '[PHONE_MASKED]', masked)
    masked = re.sub(pattern_toll_free, '[HELPLINE_MASKED]', masked)

    return masked
