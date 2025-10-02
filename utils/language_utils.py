import re

def detect_language(text):
    """
    Detect language from user input text
    Returns: 'odia', 'hindi', or 'english'
    """
    if not text or not isinstance(text, str):
        return 'english'
    
    # Clean text
    text = text.strip()
    
    # Check for explicit language indicators
    language_indicators = {
        'odia': ['odia', 'ଓଡ଼ିଆ', 'oriya'],
        'hindi': ['hindi', 'हिंदी', 'devanagari'],
        'english': ['english', 'angrezi']
    }
    
    text_lower = text.lower()
    for lang, indicators in language_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                return lang
    
    # Unicode script detection
    odia_count = count_script_chars(text, 'odia')
    hindi_count = count_script_chars(text, 'hindi')
    english_count = count_script_chars(text, 'english')
    
    # If any Indic script is present, prioritize it
    if odia_count > 0:
        return 'odia'
    elif hindi_count > 0:
        return 'hindi'
    elif english_count > 0:
        return 'english'
    
    # Fallback: check for common words in each language
    return detect_by_common_words(text)

def count_script_chars(text, script):
    """Count characters belonging to a specific script"""
    if script == 'odia':
        # Odia Unicode range: U+0B00–U+0B7F
        return sum(1 for char in text if '\u0B00' <= char <= '\u0B7F')
    elif script == 'hindi':
        # Devanagari Unicode range: U+0900–U+097F
        return sum(1 for char in text if '\u0900' <= char <= '\u097F')
    elif script == 'english':
        # Basic Latin: U+0000–U+007F
        return sum(1 for char in text if '\u0000' <= char <= '\u007F' and char.isalpha())
    return 0

def detect_by_common_words(text):
    """Detect language by common words"""
    text_lower = text.lower()
    
    # Common Odia words
    odia_words = [
        'କଣ', 'କେମିତି', 'କେବେ', 'କେଉଁ', 'ଜ୍ୱର', 'ଶର୍ଦି', 'ମଲେରିଆ', 'ଡେଙ୍ଗୁ',
        'ଟିକା', 'ବାଚ୍ଚା', 'ଶିଶୁ', 'ରୋଗ', 'ଚିକିତ୍ସା', 'ଡାକ୍ତର', 'ସ୍ୱାସ୍ଥ୍ୟ',
        'kana', 'kemiti', 'kebe', 'koun', 'jwara'
    ]
    
    # Common Hindi words
    hindi_words = [
        'क्या', 'कैसे', 'कब', 'कौन', 'बुखार', 'सर्दी', 'मलेरिया', 'डेंगू',
        'टीका', 'बच्चा', 'शिशु', 'बीमारी', 'इलाज', 'डॉक्टर', 'स्वास्थ्य',
        'kya', 'kaise', 'kab', 'kaun', 'bukhar'
    ]
    
    # Common English words
    english_words = [
        'what', 'how', 'when', 'which', 'fever', 'cold', 'malaria', 'dengue',
        'vaccine', 'baby', 'child', 'disease', 'treatment', 'doctor', 'health'
    ]
    
    # Count matches
    odia_matches = sum(1 for word in odia_words if word in text_lower)
    hindi_matches = sum(1 for word in hindi_words if word in text_lower)
    english_matches = sum(1 for word in english_words if word in text_lower)
    
    # Return language with most matches
    if odia_matches > hindi_matches and odia_matches > english_matches:
        return 'odia'
    elif hindi_matches > english_matches:
        return 'hindi'
    else:
        return 'english'

def get_language_from_dialogflow(parameters):
    """Extract language preference from Dialogflow parameters"""
    if not parameters:
        return 'english'
    
    # Check if language is explicitly set in parameters
    if 'language' in parameters:
        lang = parameters['language'].lower()
        if lang in ['odia', 'oriya', 'ଓଡ଼ିଆ']:
            return 'odia'
        elif lang in ['hindi', 'हिंदी']:
            return 'hindi'
        elif lang in ['english', 'angrezi']:
            return 'english'
    
    return 'english'

def normalize_disease_name(disease_input):
    """Normalize disease name from different languages to English key"""
    disease_mapping = {
        # Fever mappings
        'fever': 'fever',
        'ଜ୍ୱର': 'fever',
        'jwara': 'fever',
        'बुखार': 'fever',
        'bukhar': 'fever',
        
        # Cold mappings
        'cold': 'cold',
        'common cold': 'cold',
        'ଶର୍ଦି': 'cold',
        'sardi': 'cold',
        'सर्दी': 'cold',
        
        # Malaria mappings
        'malaria': 'malaria',
        'ମଲେରିଆ': 'malaria',
        'मलेरिया': 'malaria',
        
        # Dengue mappings
        'dengue': 'dengue',
        'dengue fever': 'dengue',
        'ଡେଙ୍ଗୁ': 'dengue',
        'डेंगू': 'dengue',
        
        # Asthma mappings
        'asthma': 'asthma',
        'ଆଜମା': 'asthma',
        'अस्थमा': 'asthma',
        
        # Diabetes mappings
        'diabetes': 'diabetes',
        'diabetes mellitus': 'diabetes',
        'ଡାଏବେଟିସ୍': 'diabetes',
        'ଡାଏବେଟିସ': 'diabetes',
        'डायबिटीज': 'diabetes',
        'मधुमेह': 'diabetes',
        
        # Hypertension mappings
        'hypertension': 'hypertension',
        'high blood pressure': 'hypertension',
        'ଉଚ୍ଚ ରକ୍ତଚାପ': 'hypertension',
        'उच्च रक्तचाप': 'hypertension',
        
        # Diarrhea mappings
        'diarrhea': 'diarrhea',
        'diarrhoea': 'diarrhea',
        'loose motion': 'diarrhea',
        'ଝାଡ଼ା': 'diarrhea',
        'jhada': 'diarrhea',
        'दस्त': 'diarrhea',
        'लूज मोशन': 'diarrhea',
        
        # Typhoid mappings
        'typhoid': 'typhoid',
        'typhoid fever': 'typhoid',
        'ଟାଇଫଏଡ୍': 'typhoid',
        'ଟାଇଫଏଡ': 'typhoid',
        'टाइफाइड': 'typhoid',
        
        # Tuberculosis mappings
        'tuberculosis': 'tuberculosis',
        'tb': 'tuberculosis',
        'ଯକ୍ଷ୍ମା': 'tuberculosis',
        'yakshma': 'tuberculosis',
        'तपेदिक': 'tuberculosis',
        'क्षय रोग': 'tuberculosis',
        
        # Jaundice mappings
        'jaundice': 'jaundice',
        'ଜଣ୍ଡିସ୍': 'jaundice',
        'ଜଣ୍ଡିସ': 'jaundice',
        'jandis': 'jaundice',
        'पीलिया': 'jaundice',
        
        # Chickenpox mappings
        'chickenpox': 'chickenpox',
        'chicken pox': 'chickenpox',
        'varicella': 'chickenpox',
        'ଚିକେନ୍‌ପକ୍ସ': 'chickenpox',
        'चिकनपॉक्स': 'chickenpox',
        
        # Migraine mappings
        'migraine': 'migraine',
        'migraine headache': 'migraine',
        'ମାଇଗ୍ରେନ୍': 'migraine',
        'माइग्रेन': 'migraine',
        
        # Gastritis mappings
        'gastritis': 'gastritis',
        'ଗ୍ୟାଷ୍ଟ୍ରାଇଟିସ୍': 'gastritis',
        'गैस्ट्राइटिस': 'gastritis',
        
        # Anemia mappings
        'anemia': 'anemia',
        'anaemia': 'anemia',
        'ରକ୍ତହୀନତା': 'anemia',
        'एनीमिया': 'anemia',
        'खून की कमी': 'anemia',
        
        # Pneumonia mappings
        'pneumonia': 'pneumonia',
        'ନିମୋନିଆ': 'pneumonia',
        'निमोनिया': 'pneumonia',
        
        # Kidney stone mappings
        'kidney stone': 'kidney_stone',
        'kidney stones': 'kidney_stone',
        'renal stone': 'kidney_stone',
        'renal calculi': 'kidney_stone',
        'କିଡନୀ ପଥର': 'kidney_stone',
        'किडनी स्टोन': 'kidney_stone',
        'पथरी': 'kidney_stone',
        
        # Hepatitis mappings
        'hepatitis': 'hepatitis',
        'ହେପାଟାଇଟିସ୍': 'hepatitis',
        'हेपेटाइटिस': 'hepatitis',
        
        # Arthritis mappings
        'arthritis': 'arthritis',
        'ଆର୍ଥ୍ରାଇଟିସ୍': 'arthritis',
        'गठिया': 'arthritis',
        
        # Ulcer mappings
        'ulcer': 'ulcer',
        'stomach ulcer': 'ulcer',
        'peptic ulcer': 'ulcer',
        'gastric ulcer': 'ulcer',
        'ଅଲସର୍': 'ulcer',
        'अल्सर': 'ulcer',
        
        # Thyroid mappings
        'thyroid': 'thyroid',
        'thyroid disorder': 'thyroid',
        'ଥାଇରଏଡ୍': 'thyroid',
        'थायराइड': 'thyroid',
        'hypothyroidism': 'thyroid',
        'hyperthyroidism': 'thyroid',
        
        # Bronchitis mappings
        'bronchitis': 'bronchitis',
        'ବ୍ରୋଙ୍କାଇଟିସ୍': 'bronchitis',
        'ब्रोंकाइटिस': 'bronchitis',
        
        # Scabies mappings
        'scabies': 'scabies',
        'ସ୍କାବିଜ୍': 'scabies',
        'स्केबीज': 'scabies',
        'खुजली': 'scabies',
        
        # UTI mappings
        'urinary tract infection': 'urinary_tract_infection',
        'uti': 'urinary_tract_infection',
        'urine infection': 'urinary_tract_infection',
        'ମୂତ୍ରନଳୀ ସଂକ୍ରମଣ': 'urinary_tract_infection',
        'मूत्र पथ संक्रमण': 'urinary_tract_infection',
        
        # Conjunctivitis mappings
        'conjunctivitis': 'conjunctivitis',
        'pink eye': 'conjunctivitis',
        'କଞ୍ଜଙ୍କଟିଭାଇଟିସ୍': 'conjunctivitis',
        'कंजंक्टिवाइटिस': 'conjunctivitis',
        'आंख आना': 'conjunctivitis'
    }
    
    if not disease_input:
        return None
    
    disease_lower = disease_input.lower().strip()
    
    # Direct mapping
    if disease_lower in disease_mapping:
        return disease_mapping[disease_lower]
    
    # Partial matching
    for key, value in disease_mapping.items():
        if key in disease_lower or disease_lower in key:
            return value
    
    return disease_lower

def normalize_vaccine_name(vaccine_input):
    """Normalize vaccine name from different languages"""
    vaccine_mapping = {
        'bcg': 'bcg',
        'polio': 'opv',
        'opv': 'opv',
        'ପୋଲିଓ': 'opv',
        'पोलियो': 'opv',
        
        'dpt': 'dpt',
        'diphtheria': 'dpt',
        'pertussis': 'dpt',
        'tetanus': 'dpt',
        
        'measles': 'measles',
        'ହମ୍ପ': 'measles',
        'खसरा': 'measles',
        
        'hepatitis': 'hepatitis_b',
        'hepatitis b': 'hepatitis_b',
        'ହେପାଟାଇଟିସ': 'hepatitis_b',
        'हेपेटाइटिस': 'hepatitis_b',
        
        'vaccine': 'complete',
        'vaccination': 'complete',
        'टीका': 'complete',
        'ଟିକା': 'complete',
        'baby': 'complete',
        'schedule': 'complete'
        
        
    }
    
    if not vaccine_input:
        return None
    
    vaccine_lower = vaccine_input.lower().strip()
    
    # Direct mapping
    if vaccine_lower in vaccine_mapping:
        return vaccine_mapping[vaccine_lower]
    
    # Partial matching
    for key, value in vaccine_mapping.items():
        if key in vaccine_lower:
            return value
    
    return vaccine_lower

def get_greeting_response(language):
    """Get greeting response in specified language"""
    greetings = {
        'odia': "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ସହାୟକ। ମୁଁ ରୋଗ ଓ ଟିକା ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି। କେମିତି ସାହାଯ୍ୟ କରିବି?",
        'english': "Hello! I'm your health assistant. I can help with diseases and vaccination information. How can I help you?",
        'hindi': "नमस्ते! मैं आपका स्वास्थ्य सहायक हूं। मैं बीमारी और टीकाकरण की जानकारी में मदद कर सकता हूं। मैं कैसे मदद कर सकता हूं?"
    }
    return greetings.get(language, greetings['english'])

def extract_temperature(text):
    """Extract temperature value from user input"""
    if not text:
        return None
    
    # Look for temperature patterns
    temp_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:degree|°|deg)?\s*(?:f|fahrenheit|फ|ଫ)?',
        r'(\d+(?:\.\d+)?)\s*(?:ଡିଗ୍ରୀ|डिग्री)',
        r'temperature\s+(\d+(?:\.\d+)?)',
        r'temp\s+(\d+(?:\.\d+)?)'
    ]
    
    text_lower = text.lower()
    for pattern in temp_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                continue
    
    return None
