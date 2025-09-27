import json
import os

def load_vaccine_data():
    """Load vaccine data from JSON file"""
    try:
        with open('data/vaccines.json', 'r', encoding='utf-8') as f:
            vaccines = json.load(f)
        
        with open('data/phrases.json', 'r', encoding='utf-8') as f:
            phrases = json.load(f)
            
        return vaccines, phrases
    except Exception as e:
        print(f"Error loading vaccine data: {e}")
        return {}, {}

def get_vaccine_info(vaccine_name=None, language='english'):
    """Get vaccination information in specified language"""
    vaccines, phrases = load_vaccine_data()
    
    if not vaccine_name or vaccine_name.lower() in ['baby', 'schedule', 'complete', 'all']:
        # Return complete vaccination schedule
        if 'complete_schedule' in vaccines:
            response = vaccines['complete_schedule'][language]
        else:
            response = get_complete_schedule_manual(vaccines, language)
    else:
        # Return specific vaccine information
        vaccine_name = vaccine_name.lower().replace(' ', '_')
        
        # Handle vaccine name variations
        vaccine_mapping = {
            'bcg': 'bcg',
            'polio': 'opv',
            'opv': 'opv',
            'dpt': 'dpt',
            'diphtheria': 'dpt',
            'pertussis': 'dpt', 
            'tetanus': 'dpt',
            'measles': 'measles',
            'hepatitis': 'hepatitis_b',
            'hepatitis_b': 'hepatitis_b'
        }
        
        matched_vaccine = None
        for key, value in vaccine_mapping.items():
            if key in vaccine_name:
                matched_vaccine = value
                break
        
        if matched_vaccine and matched_vaccine in vaccines:
            vaccine_info = vaccines[matched_vaccine]
            response = format_single_vaccine_response(matched_vaccine, vaccine_info, language)
        else:
            response = get_vaccine_not_found_response(language)
    
    # Add disclaimer
    response += "\n\n" + phrases['disclaimers']['medical_advice'][language]
    
    return response

def format_single_vaccine_response(vaccine_name, vaccine_info, language):
    """Format response for a single vaccine"""
    vaccine_names = {
        'bcg': {'odia': 'BCG', 'english': 'BCG', 'hindi': 'BCG'},
        'opv': {'odia': 'OPV (ପୋଲିଓ)', 'english': 'OPV (Polio)', 'hindi': 'OPV (पोलियो)'},
        'dpt': {'odia': 'DPT', 'english': 'DPT', 'hindi': 'DPT'},
        'measles': {'odia': 'ହମ୍ପ ଟିକା', 'english': 'Measles Vaccine', 'hindi': 'खसरा टीका'},
        'hepatitis_b': {'odia': 'ହେପାଟାଇଟିସ୍ B', 'english': 'Hepatitis B', 'hindi': 'हेपेटाइटिस B'}
    }
    
    templates = {
        'odia': f"💉 {vaccine_names.get(vaccine_name, {}).get('odia', vaccine_name.upper())} ଟିକା:\n📅 ସମୟ: {vaccine_info.get('age_odia', '')}\n🛡️ {vaccine_info.get('description_odia', '')}",
        'english': f"💉 {vaccine_names.get(vaccine_name, {}).get('english', vaccine_name.upper())} Vaccine:\n📅 Age: {vaccine_info.get('age_english', '')}\n🛡️ {vaccine_info.get('description_english', '')}",
        'hindi': f"💉 {vaccine_names.get(vaccine_name, {}).get('hindi', vaccine_name.upper())} टीका:\n📅 उम्र: {vaccine_info.get('age_hindi', '')}\n🛡️ {vaccine_info.get('description_hindi', '')}"
    }
    
    return templates.get(language, templates['english'])

def get_complete_schedule_manual(vaccines, language):
    """Generate complete schedule manually if not in data"""
    schedules = {
        'odia': "ଶିଶୁ ଟିକା କାର୍ଯ୍ୟସୂଚୀ:\n🔸 ଜନ୍ମ ସମୟରେ: BCG + Hepatitis B\n🔸 ୬ ସପ୍ତାହରେ: OPV + DPT + Hepatitis B\n🔸 ୧୦ ସପ୍ତାହରେ: OPV + DPT\n🔸 ୧୪ ସପ୍ତାହରେ: OPV + DPT + Hepatitis B\n🔸 ୯ ମାସରେ: Measles\n\nନିକଟସ୍ଥ ସ୍ୱାସ୍ଥ୍ୟକେନ୍ଦ୍ରରେ ଯୋଗାଯୋଗ କରନ୍ତୁ।",
        'english': "Baby Vaccination Schedule:\n🔸 At Birth: BCG + Hepatitis B\n🔸 6 Weeks: OPV + DPT + Hepatitis B\n🔸 10 Weeks: OPV + DPT\n🔸 14 Weeks: OPV + DPT + Hepatitis B\n🔸 9 Months: Measles\n\nContact your nearest health center.",
        'hindi': "बच्चे की टीकाकरण तालिका:\n🔸 जन्म पर: BCG + Hepatitis B\n🔸 6 सप्ताह: OPV + DPT + Hepatitis B\n🔸 10 सप्ताह: OPV + DPT\n🔸 14 सप्ताह: OPV + DPT + Hepatitis B\n🔸 9 महीने: Measles\n\nअपने नजदीकी स्वास्थ्य केंद्र से संपर्क करें।"
    }
    
    return schedules.get(language, schedules['english'])

def get_vaccine_not_found_response(language):
    """Return response when vaccine is not found"""
    responses = {
        'odia': "ଦୁଃଖିତ, ଏହି ଟିକା ବିଷୟରେ ମୋର ସୂଚନା ନାହିଁ। ମୁଁ BCG, OPV, DPT, Measles, Hepatitis B ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି।",
        'english': "Sorry, I don't have information about this vaccine. I can help with BCG, OPV, DPT, Measles, Hepatitis B vaccines.",
        'hindi': "खुशी, मुझे इस टीके की जानकारी नहीं है। मैं BCG, OPV, DPT, खसरा, हेपेटाइटिस B के बारे में मदद कर सकता हूं।"
    }
    return responses.get(language, responses['english'])

def get_vaccination_reminder(language):
    """Get vaccination reminder message"""
    reminders = {
        'odia': "💡 ମନେରଖନ୍ତୁ: ସମୟରେ ଟିକା ଦେବା ଅତ୍ୟନ୍ତ ଜରୁରୀ। ଟିକା କାର୍ଡ ସାଙ୍ଗରେ ରଖନ୍ତୁ।",
        'english': "💡 Remember: Timely vaccination is very important. Keep vaccination card with you.",
        'hindi': "💡 याद रखें: समय पर टीकाकरण बहुत जरूरी है। टीकाकरण कार्ड अपने साथ रखें।"
    }
    return reminders.get(language, reminders['english'])

def get_available_vaccines():
    """Return list of available vaccines"""
    vaccines, _ = load_vaccine_data()
    return [v for v in vaccines.keys() if v != 'complete_schedule']
