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
    
    if not vaccine_name or str(vaccine_name).lower() in ['baby', 'schedule', 'complete', 'all']:
        # Return complete vaccination schedule
        if 'complete_schedule' in vaccines:
            response = vaccines['complete_schedule'][language]
        else:
            response = get_complete_schedule_manual(vaccines, language)
    else:
        # Return specific vaccine information
        vaccine_name = str(vaccine_name).lower().replace(' ', '_')
        
        # Handle vaccine name variations
        vaccine_mapping = {
            'bcg': 'bcg',
            'polio': 'opv',
            'opv': 'opv',
            'dpt': 'dpt',
            'diphtheria': 'dpt',
            'pertussis': 'dpt', 
            'tetanus': 'dpt',
            'measles': 'mr_vaccine',
            'mr': 'mr_vaccine',
            'hepatitis': 'hepatitis_b',
            'hepatitis_b': 'hepatitis_b',
            'pentavalent': 'pentavalent',
            'penta': 'pentavalent',
            'rotavirus': 'rotavirus',
            'rota': 'rotavirus',
            'pcv': 'pcv',
            'pneumococcal': 'pcv',
            'ipv': 'ipv',
            'fipv': 'ipv',
            'je': 'je_vaccine',
            'japanese': 'je_vaccine',
            'dpt_booster': 'dpt_booster_1',
            'opv_booster': 'opv_booster',
            'td': 'td_vaccine',
            'booster': 'dpt_booster_1'
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
        'mr_vaccine': {'odia': 'MR Vaccine', 'english': 'MR Vaccine', 'hindi': 'MR टीका'},
        'hepatitis_b': {'odia': 'ହେପାଟାଇଟିସ୍ B', 'english': 'Hepatitis B', 'hindi': 'हेपेटाइटिस B'},
        'pentavalent': {'odia': 'Pentavalent', 'english': 'Pentavalent', 'hindi': 'पेंटावैलेंट'},
        'rotavirus': {'odia': 'Rotavirus', 'english': 'Rotavirus', 'hindi': 'रोटावायरस'},
        'pcv': {'odia': 'PCV', 'english': 'PCV', 'hindi': 'PCV'},
        'ipv': {'odia': 'IPV (fIPV)', 'english': 'IPV (fIPV)', 'hindi': 'IPV (fIPV)'},
        'je_vaccine': {'odia': 'JE Vaccine', 'english': 'JE Vaccine', 'hindi': 'JE टीका'},
        'dpt_booster_1': {'odia': 'DPT Booster-1', 'english': 'DPT Booster-1', 'hindi': 'DPT बूस्टर-1'},
        'dpt_booster_2': {'odia': 'DPT Booster-2', 'english': 'DPT Booster-2', 'hindi': 'DPT बूस्टर-2'},
        'opv_booster': {'odia': 'OPV Booster', 'english': 'OPV Booster', 'hindi': 'OPV बूस्टर'},
        'td_vaccine': {'odia': 'Td Vaccine', 'english': 'Td Vaccine', 'hindi': 'Td टीका'}
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
        'odia': "ଶିଶୁ ଟିକା କାର୍ଯ୍ୟସୂଚୀ (NIS 2025):\n🔸 ଜନ୍ମରେ: BCG + OPV-0 + Hepatitis B\n🔸 ୬ ସପ୍ତାହ: OPV-1 + Pentavalent-1 + Rotavirus-1 + fIPV-1 + PCV-1\n🔸 ୧୦ ସପ୍ତାହ: OPV-2 + Pentavalent-2 + Rotavirus-2\n🔸 ୧୪ ସପ୍ତାହ: OPV-3 + Pentavalent-3 + fIPV-2 + Rotavirus-3 + PCV-2\n🔸 ୯-୧୨ ମାସ: MR-1 + JE-1* + PCV Booster\n🔸 ୧୬-୨୪ ମାସ: MR-2 + DPT Booster-1 + OPV Booster + JE-2*\n🔸 ୫-୬ ବର୍ଷ: DPT Booster-2\n🔸 ୧୦ ବର୍ଷ: Td\n🔸 ୧୬ ବର୍ଷ: Td\n\n*JE କେବଳ ଏଣ୍ଡେମିକ୍ ଜିଲ୍ଲାରେ\nନିକଟସ୍ଥ ସ୍ୱାସ୍ଥ୍ୟକେନ୍ଦ୍ରରେ ଯୋଗାଯୋଗ କରନ୍ତୁ।",
        
        'english': "Baby Vaccination Schedule (NIS 2025):\n🔸 At Birth: BCG + OPV-0 + Hepatitis B\n🔸 6 Weeks: OPV-1 + Pentavalent-1 + Rotavirus-1 + fIPV-1 + PCV-1\n🔸 10 Weeks: OPV-2 + Pentavalent-2 + Rotavirus-2\n🔸 14 Weeks: OPV-3 + Pentavalent-3 + fIPV-2 + Rotavirus-3 + PCV-2\n🔸 9-12 Months: MR-1 + JE-1* + PCV Booster\n🔸 16-24 Months: MR-2 + DPT Booster-1 + OPV Booster + JE-2*\n🔸 5-6 Years: DPT Booster-2\n🔸 10 Years: Td\n🔸 16 Years: Td\n\n*JE in endemic districts only\nContact your nearest health center.",
        
        'hindi': "बच्चे की टीकाकरण तालिका (NIS 2025):\n🔸 जन्म पर: BCG + OPV-0 + Hepatitis B\n🔸 6 सप्ताह: OPV-1 + Pentavalent-1 + Rotavirus-1 + fIPV-1 + PCV-1\n🔸 10 सप्ताह: OPV-2 + Pentavalent-2 + Rotavirus-2\n🔸 14 सप्ताह: OPV-3 + Pentavalent-3 + fIPV-2 + Rotavirus-3 + PCV-2\n🔸 9-12 महीने: MR-1 + JE-1* + PCV Booster\n🔸 16-24 महीने: MR-2 + DPT Booster-1 + OPV Booster + JE-2*\n🔸 5-6 साल: DPT Booster-2\n🔸 10 साल: Td\n🔸 16 साल: Td\n\n*JE केवल स्थानिक जिलों में\nअपने नजदीकी स्वास्थ्य केंद्र से संपर्क करें।"
    }
    
    return schedules.get(language, schedules['english'])

def get_vaccine_not_found_response(language):
    """Return response when vaccine is not found"""
    responses = {
        'odia': "ଦୁଃଖିତ, ଏହି ଟିକା ବିଷୟରେ ମୋର ସୂଚନା ନାହିଁ। ମୁଁ BCG, OPV, IPV, DPT, Pentavalent, Rotavirus, PCV, MR, Hepatitis B, JE, Td ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି।",
        'english': "Sorry, I don't have information about this vaccine. I can help with BCG, OPV, IPV, DPT, Pentavalent, Rotavirus, PCV, MR, Hepatitis B, JE, Td vaccines.",
        'hindi': "खेद है, मुझे इस टीके की जानकारी नहीं है। मैं BCG, OPV, IPV, DPT, Pentavalent, Rotavirus, PCV, MR, Hepatitis B, JE, Td के बारे में मदद कर सकता हूं।"
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
