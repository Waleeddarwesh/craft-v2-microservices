from deep_translator import GoogleTranslator

def translate_text(text, source='auto', target='ar'):
    """
    Translate text dynamically using deep-translator (Google Translate).
    If translation fails due to network or API limits, returns the original text.
    """
    if not text or not isinstance(text, str) or text.strip() == "":
        return ""
    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
        return translated if translated else text
    except Exception:
        # Fallback to original text on failure to prevent database save crashes
        return text
