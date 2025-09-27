from flask import Flask, request, jsonify
import json
import os
from utils.disease_handler import get_disease_info, detect_language as detect_lang_disease
from utils.vaccine_handler import get_vaccine_info, get_vaccination_reminder
from utils.language_utils import (
    detect_language, 
    get_language_from_dialogflow, 
    normalize_disease_name, 
    normalize_vaccine_name,
    get_greeting_response,
    extract_temperature
)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Healthcare Chatbot API is running',
        'supported_languages': ['odia', 'english', 'hindi'],
        'supported_diseases': ['fever', 'cold', 'malaria', 'dengue'],
        'supported_vaccines': ['bcg', 'opv', 'dpt', 'measles', 'hepatitis_b']
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for Dialogflow"""
    try:
        # Get request data from Dialogflow
        req = request.get_json()
        
        if not req:
            return jsonify({'fulfillmentText': 'Invalid request'})
        
        # Extract key information
        intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        query_text = req.get('queryResult', {}).get('queryText', '')
        
        print(f"Intent: {intent_name}")
        print(f"Parameters: {parameters}")
        print(f"Query: {query_text}")
        
        # Detect language
        language = detect_language(query_text)
        dialogflow_lang = get_language_from_dialogflow(parameters)
        if dialogflow_lang != 'english':
            language = dialogflow_lang
        
        print(f"Detected Language: {language}")
        
        # Process based on intent
        response_text = process_intent(intent_name, parameters, query_text, language)
        
        return jsonify({
            'fulfillmentText': response_text
        })
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        error_responses = {
            'odia': 'ଦୁଃଖିତ, କିଛି ସମସ୍ୟା ହୋଇଛି। ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।',
            'english': 'Sorry, something went wrong. Please try again.',
            'hindi': 'खुशी, कुछ समस्या हुई है। कृपया फिर से कोशिश करें।'
        }
        return jsonify({
            'fulfillmentText': error_responses.get('english')
        })

def process_intent(intent_name, parameters, query_text, language):
    """Process different intents and return appropriate response"""
    
    # Default Welcome Intent
    if intent_name in ['Default Welcome Intent', 'welcome', 'greeting']:
        return get_greeting_response(language)
    
    # Disease Information Intent
    elif intent_name in ['disease_info', 'disease.info', 'get_disease_info']:
        disease_name = parameters.get('disease', '')
        if not disease_name:
            # Try to extract disease from query text
            disease_name = extract_disease_from_query(query_text)
        
        normalized_disease = normalize_disease_name(disease_name)
        return get_disease_info(normalized_disease, language, query_text)
    
    # Vaccination Intent
    elif intent_name in ['vaccine_info', 'vaccination', 'get_vaccine_info']:
        vaccine_name = parameters.get('vaccine', '')
        if not vaccine_name:
            # Check for baby/schedule keywords
            if any(word in query_text.lower() for word in ['baby', 'बच्चा', 'ବାଚ୍ଚା', 'schedule', 'शेड्यूल', 'କାର୍ଯ୍ୟସୂଚୀ']):
                vaccine_name = 'complete'
        
        normalized_vaccine = normalize_vaccine_name(vaccine_name)
        return get_vaccine_info(normalized_vaccine, language)
    
    # Emergency Intent
    elif intent_name in ['emergency', 'urgent_help', 'emergency_help']:
        return handle_emergency(query_text, language)
    
    # General Health Intent
    elif intent_name in ['general_health', 'health_tips']:
        return get_general_health_tips(language)
    
    # Fallback - try to determine what user wants
    else:
        return handle_fallback(query_text, language)

def extract_disease_from_query(query_text):
    """Extract disease name from user query"""
    disease_keywords = {
        'fever': ['fever', 'ଜ୍ୱର', 'jwara', 'बुखार', 'bukhar', 'temperature', 'temp'],
        'cold': ['cold', 'ଶର୍ଦି', 'sardi', 'सर्दी', 'cough', 'କାଶ', 'खांसी'],
        'malaria': ['malaria', 'ମଲେରିଆ', 'मलेरिया'],
        'dengue': ['dengue', 'ଡେଙ୍ଗୁ', 'डेंगू']
    }
    
    query_lower = query_text.lower()
    for disease, keywords in disease_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                return disease
    
    return None

def handle_emergency(query_text, language):
    """Handle emergency situations"""
    from utils.disease_handler import check_emergency_condition, load_data
    
    # Check for temperature in query
    temp = extract_temperature(query_text)
    if temp and temp >= 103:
        _, phrases = load_data()
        return phrases['emergency_responses']['fever_above_103'][language]
    
    # Check other emergency conditions
    emergency = check_emergency_condition(None, query_text)
    if emergency:
        _, phrases = load_data()
        return phrases['emergency_responses'][emergency][language]
    
    # General emergency response
    emergency_responses = {
        'odia': '🚨 ଜରୁରୀକାଳୀନ ପରିସ୍ଥିତିରେ ତୁରନ୍ତ 108 ନମ୍ବରରେ ଡାକନ୍ତୁ କିମ୍ବା ନିକଟସ୍ଥ ଚିକିତ୍ସାଳୟକୁ ଯାଆନ୍ତୁ।',
        'english': '🚨 In emergency, immediately call 108 or visit nearest hospital.',
        'hindi': '🚨 आपातकाल में तुरंत 108 पर कॉल करें या निकटतम अस्पताल जाएं।'
    }
    
    return emergency_responses.get(language, emergency_responses['english'])

def get_general_health_tips(language):
    """Get general health tips"""
    tips = {
        'odia': 'ସୁସ୍ଥ ରହିବା ପାଇଁ:\n• ସଫା ପାଣି ପିଅନ୍ତୁ\n• ହାତ ବାରମ୍ବାର ଧୋଇନ୍ତୁ\n• ସୁସ୍ଥ ଖାଦ୍ୟ ଖାଅନ୍ତୁ\n• ନିୟମିତ ବ୍ୟାୟାମ କରନ୍ତୁ\n• ପର୍ଯ୍ୟାପ୍ତ ଶୋଇନ୍ତୁ',
        'english': 'To stay healthy:\n• Drink clean water\n• Wash hands frequently\n• Eat healthy food\n• Exercise regularly\n• Get adequate sleep',
        'hindi': 'स्वस्थ रहने के लिए:\n• साफ पानी पिएं\n• बार-बार हाथ धोएं\n• स्वस्थ खाना खाएं\n• नियमित व्यायाम करें\n• पर्याप्त नींद लें'
    }
    
    return tips.get(language, tips['english'])

def handle_fallback(query_text, language):
    """Handle fallback cases when intent is not clear"""
    
    # Check if it's about disease
    disease = extract_disease_from_query(query_text)
    if disease:
        return get_disease_info(disease, language, query_text)
    
    # Check if it's about vaccination
    vaccine_keywords = ['vaccine', 'टीका', 'ଟିକା', 'vaccination', 'immunization']
    if any(keyword in query_text.lower() for keyword in vaccine_keywords):
        return get_vaccine_info('complete', language)
    
    # General fallback response
    fallback_responses = {
        'odia': 'ମୁଁ ରୋଗ (ଜ୍ୱର, ଶର୍ଦି, ମଲେରିଆ, ଡେଙ୍ଗୁ) ଏବଂ ଟିକାକରଣ ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି। କେମିତି ସାହାଯ୍ୟ କରିବି?',
        'english': 'I can help with diseases (fever, cold, malaria, dengue) and vaccination information. How can I help you?',
        'hindi': 'मैं बीमारियों (बुखार, सर्दी, मलेरिया, डेंगू) और टीकाकरण के बारे में मदद कर सकता हूं। मैं कैसे मदद कर सकता हूं?'
    }
    
    return fallback_responses.get(language, fallback_responses['english'])

@app.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Test endpoint for manual testing"""
    if request.method == 'GET':
        return '''
        <html>
        <body>
            <h2>Healthcare Chatbot Test</h2>
            <form method="POST">
                <label>Query:</label><br>
                <input type="text" name="query" style="width:300px" placeholder="Ask about fever, vaccines, etc."><br><br>
                <label>Language:</label><br>
                <select name="language">
                    <option value="english">English</option>
                    <option value="odia">Odia</option>
                    <option value="hindi">Hindi</option>
                </select><br><br>
                <input type="submit" value="Test">
            </form>
        </body>
        </html>
        '''
    
    # POST request - process test query
    query = request.form.get('query', '')
    language = request.form.get('language', 'english')
    
    # Simulate Dialogflow request
    mock_intent = 'test'
    mock_parameters = {}
    
    # Determine intent based on query
    if any(word in query.lower() for word in ['fever', 'ଜ୍ୱର', 'बुखार']):
        mock_intent = 'disease_info'
        mock_parameters['disease'] = 'fever'
    elif any(word in query.lower() for word in ['vaccine', 'ଟିକା', 'टीका']):
        mock_intent = 'vaccine_info'
    
    response = process_intent(mock_intent, mock_parameters, query, language)
    
    return f'''
    <html>
    <body>
        <h2>Test Result</h2>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Language:</strong> {language}</p>
        <p><strong>Response:</strong></p>
        <pre>{response}</pre>
        <br>
        <a href="/test">Test Again</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
