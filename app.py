from flask import Flask, request, jsonify
import json
import os
import requests
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

# ADD THESE NEW IMPORTS
from google.cloud import dialogflow
from google.oauth2 import service_account

app = Flask(__name__)

# ADD THESE NEW GLOBAL VARIABLES
PROJECT_ID = "arovi-nahi"  # Your Google Cloud Project ID
CREDENTIALS_PATH = "credentials.json"  # Path to your JSON credentials file
SESSION_ID = "default-session"  # Can be any unique identifier

def get_dialogflow_client():
    """Initialize Dialogflow client with credentials"""
    try:
        # Try environment variable first (for Render deployment)
        credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if credentials_json:
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
        else:
            # Fallback to file (for local development)
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        
        client = dialogflow.SessionsClient(credentials=credentials)
        return client
    except Exception as e:
        print(f"Error initializing Dialogflow client: {str(e)}")
        return None

def call_dialogflow_detect_intent(message_text, session_id=SESSION_ID):
    """Call Dialogflow's detectIntent API"""
    try:
        client = get_dialogflow_client()
        if not client:
            return None
            
        session_path = client.session_path(PROJECT_ID, session_id)
        text_input = dialogflow.TextInput(text=message_text, language_code="en-US")
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )
        
        return response
    except Exception as e:
        print(f"Error calling Dialogflow: {str(e)}")
        return None

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

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio - NOW ROUTES THROUGH DIALOGFLOW"""
    try:
        # Get message data from Twilio
        from_number = request.form.get('From', '').replace('whatsapp:', '')
        message_body = request.form.get('Body', '')
        
        if not message_body:
            return '', 200
        
        # STEP 1: Send message to Dialogflow for intent detection
        dialogflow_response = call_dialogflow_detect_intent(message_body, from_number)
        
        if dialogflow_response:
            # STEP 2: Dialogflow processed successfully - extract the response
            response_text = dialogflow_response.query_result.fulfillment_text
            
            # If Dialogflow has no fulfillment text, it means it should call our webhook
            # In that case, we simulate the webhook call
            if not response_text:
                # Simulate webhook request structure
                mock_request = {
                    'queryResult': {
                        'intent': {
                            'displayName': dialogflow_response.query_result.intent.display_name
                        },
                        'parameters': {k: (v[0] if isinstance(v, list) and len(v) == 1 else str(v)) for k, v in dialogflow_response.query_result.parameters.items()},
                        'queryText': message_body
                    }
                }
                
                # Call our existing webhook logic
                response_text = process_webhook_request(mock_request)
        else:
            # FALLBACK: If Dialogflow fails, use old direct processing
            language = detect_language(message_body)
            response_text = handle_whatsapp_message_fallback(message_body, language)
        
        # STEP 3: Send response back to WhatsApp
        send_whatsapp_message(from_number, response_text)
        return '', 200
        
    except Exception as e:
        print(f"WhatsApp error: {str(e)}")
        return '', 500

def process_webhook_request(mock_request):
    """Process the webhook request (used for both real webhook and WhatsApp simulation)"""
    try:
        # Extract key information
        intent_name = mock_request.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = mock_request.get('queryResult', {}).get('parameters', {})
        query_text = mock_request.get('queryResult', {}).get('queryText', '')
        
        # Detect language
        language = detect_language(query_text)
        dialogflow_lang = get_language_from_dialogflow(parameters)
        if dialogflow_lang != 'english':
            language = dialogflow_lang
        
        # Process based on intent
        response_text = process_intent(intent_name, parameters, query_text, language)
        return response_text
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        return "Sorry, something went wrong. Please try again."

def handle_whatsapp_message_fallback(message, language):
    """FALLBACK: Process WhatsApp message directly (if Dialogflow fails)"""
    disease = extract_disease_from_query(message)
    if disease:
        return get_disease_info(disease, language, message)
    
    vaccine_keywords = ['vaccine', 'टीका', 'ଟିକା', 'baby', 'बच्चा', 'ବାଚ୍ଚା']
    if any(keyword in message.lower() for keyword in vaccine_keywords):
        return get_vaccine_info('complete', language)
    
    return get_greeting_response(language)

def send_whatsapp_message(to_number, message):
    """Send WhatsApp message via Twilio"""
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = {
        'From': 'whatsapp:+14155238886',
        'To': f'whatsapp:{to_number}',
        'Body': message
    }
    
    requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for Dialogflow"""
    try:
        # Get request data from Dialogflow
        req = request.get_json()
        
        if not req:
            return jsonify({'fulfillmentText': 'Invalid request'})
        
        # Use the shared processing function
        response_text = process_webhook_request(req)
        
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
        
        # FIX: Handle both string and list parameters from Dialogflow
        if isinstance(disease_name, list) and disease_name:
            disease_name = disease_name[0]
        elif isinstance(disease_name, list):
            disease_name = ''
        
        if not disease_name:
            # Try to extract disease from query text
            disease_name = extract_disease_from_query(query_text)
        
        normalized_disease = normalize_disease_name(disease_name)
        return get_disease_info(normalized_disease, language, query_text)
    
    # Vaccination Intent
    elif intent_name in ['vaccine_info', 'vaccination', 'get_vaccine_info']:
        vaccine_name = parameters.get('vaccine', '')
        
        # FIX: Handle both string and list parameters from Dialogflow
        if isinstance(vaccine_name, list) and vaccine_name:
            vaccine_name = vaccine_name[0]
        elif isinstance(vaccine_name, list):
            vaccine_name = ''

        # Convert to string to handle any remaining objects
        vaccine_name = str(vaccine_name) if vaccine_name else ''

        if not vaccine_name:
            # Check for baby/schedule keywords
            if any(word in query_text.lower() for word in ['baby', 'बच्चा', 'ବାଚ୍ଚା', 'schedule', 'शेड्यूल', 'କାର୍ଯ୍ଯସୂଚୀ']):
                vaccine_name = 'complete'

        if not vaccine_name:
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
        'odia': '🚨 ଜରୁରୀକାଳୀନ ପରିସ୍ଥିତିରେ ତୁରନ୍ତ 108 ନମ୍ବରରେ ଡାକନ୍ତୁ କିମ୍ବା ନିକଟସ୍ଥ ଚିକିତ୍ସାଳୟକୁ ଯାଅନ୍ତୁ।',
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
    
    # Test with Dialogflow
    dialogflow_response = call_dialogflow_detect_intent(query, "test-session")
    
    if dialogflow_response:
        response = dialogflow_response.query_result.fulfillment_text
        intent = dialogflow_response.query_result.intent.display_name
        if not response:
            # Simulate webhook if no fulfillment text
            mock_request = {
                'queryResult': {
                    'intent': {'displayName': intent},
                    'parameters': dict(dialogflow_response.query_result.parameters),
                    'queryText': query
                }
            }
            response = process_webhook_request(mock_request)
    else:
        response = "Dialogflow connection failed - using fallback"
        intent = "fallback"
    
    return f'''
    <html>
    <body>
        <h2>Test Result</h2>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Language:</strong> {language}</p>
        <p><strong>Detected Intent:</strong> {intent}</p>
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