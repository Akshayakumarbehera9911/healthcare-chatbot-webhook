import json
import os

def load_data():
    """Load disease and phrases data from JSON files"""
    try:
        # Load diseases data
        with open('data/diseases.json', 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        # Load phrases data
        with open('data/phrases.json', 'r', encoding='utf-8') as f:
            phrases = json.load(f)
        
        return diseases, phrases
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}, {}

def detect_language(text):
    """Simple language detection based on script"""
    if not text:
        return 'english'
    
    # Check for Odia script (Unicode range for Odia)
    odia_chars = sum(1 for char in text if '\u0B00' <= char <= '\u0B7F')
    # Check for Hindi script (Devanagari)
    hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
    
    if odia_chars > 0:
        return 'odia'
    elif hindi_chars > 0:
        return 'hindi'
    else:
        return 'english'

def check_emergency_condition(disease_name, user_input):
    """Check if user input indicates emergency condition"""
    diseases, phrases = load_data()
    
    # Check for fever above 103
    if disease_name == 'fever':
        # Look for temperature numbers in input
        words = user_input.lower().split()
        for word in words:
            if word.replace('.', '').replace('°', '').replace('f', '').isdigit():
                temp = float(word.replace('°', '').replace('f', ''))
                if temp >= 103:
                    return 'fever_above_103'
    
    # Check for emergency keywords
    emergency_keywords = {
        'severe_stomach_pain': ['severe pain', 'गंभीर दर्द', 'ଗଭୀର ଯନ୍ତ୍ରଣା', 'stomach pain', 'पेट दर्द', 'ପେଟ ଯନ୍ତ୍ରଣା'],
        'difficulty_breathing': ['can\'t breathe', 'सांस नहीं', 'ଦମ ନେବାରେ କଷ୍ଟ', 'breathing problem'],
        'blood_vomiting': ['blood vomit', 'खून की उल्टी', 'ରକ୍ତ ବାନ୍ତି']
    }
    
    user_input_lower = user_input.lower()
    for condition, keywords in emergency_keywords.items():
        for keyword in keywords:
            if keyword.lower() in user_input_lower:
                return condition
    
    return None

def get_disease_info(disease_name, language='english', user_input=''):
    """Get disease information in specified language"""
    diseases, phrases = load_data()
    
    if not disease_name:
        return get_fallback_response(language)
    
    # Normalize disease name
    disease_name = disease_name.lower()
    
    # Check for emergency condition first
    emergency = check_emergency_condition(disease_name, user_input)
    
    response = ""
    
    # Add emergency alert if needed
    if emergency and emergency in phrases['emergency_responses']:
        response += phrases['emergency_responses'][emergency][language] + "\n\n"
    
    # Get disease information
    if disease_name in diseases:
        disease_info = diseases[disease_name][language]
        response += disease_info
    else:
        # Try to find partial match
        for disease_key in diseases.keys():
            if disease_key in disease_name or disease_name in disease_key:
                disease_info = diseases[disease_key][language]
                response += disease_info
                break
        else:
            response += get_disease_not_found_response(language)
    
    # Add disclaimer
    response += "\n\n" + phrases['disclaimers']['medical_advice'][language]
    
    return response

def get_disease_not_found_response(language):
    """Return response when disease is not found"""
    responses = {
        'odia': "ଦୁଃଖିତ, ଏହି ରୋଗ ବିଷୟରେ ମୋର ସୂଚନା ନାହିଁ। ମୁଁ ଜ୍ୱର, ଶର୍ଦି, ମଲେରିଆ, ଡେଙ୍ଗୁ ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି।",
        'english': "Sorry, I don't have information about this disease. I can help with fever, cold, malaria, dengue.",
        'hindi': "खुशी, मुझे इस बीमारी की जानकारी नहीं है। मैं बुखार, सर्दी, मलेरिया, डेंगू के बारे में मदद कर सकता हूं।"
    }
    return responses.get(language, responses['english'])

def get_fallback_response(language):
    """Return fallback response when no disease is specified"""
    responses = {
        'odia': "ମୁଁ ଜ୍ୱର, ଶର୍ଦି, ମଲେରିଆ, ଡେଙ୍ଗୁ ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି। କେଉଁ ରୋଗ ବିଷୟରେ ଜାଣିବାକୁ ଚାହାଁନ୍ତି?",
        'english': "I can help with fever, cold, malaria, dengue. Which disease would you like to know about?",
        'hindi': "मैं बुखार, सर्दी, मलेरिया, डेंगू के बारे में मदद कर सकता हूं। आप किस बीमारी के बारे में जानना चाहते हैं?"
    }
    return responses.get(language, responses['english'])

def get_available_diseases():
    """Return list of available diseases"""
    diseases, _ = load_data()
    return list(diseases.keys())  
