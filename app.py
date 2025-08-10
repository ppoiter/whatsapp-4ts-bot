from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
import re

app = Flask(__name__)

# Twilio setup
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_client = Client(account_sid, auth_token)

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID', 'your-google-sheet-id')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# User mapping (could be stored in a database)
user_map = {
    '+1234567890': 'john_doe',
    '+9876543210': 'jane_smith',
    # Add more mappings as needed
}

def get_google_sheet():
    """Initialize Google Sheets connection"""
    try:
        # Load credentials from environment variable
        creds = Credentials.from_service_account_info({
            "type": "service_account",
            "project_id": os.environ['GOOGLE_PROJECT_ID'],
            "private_key_id": os.environ['GOOGLE_PRIVATE_KEY_ID'],
            "private_key": os.environ['GOOGLE_PRIVATE_KEY'].replace('\\n', '\n'),
            "client_email": os.environ['GOOGLE_CLIENT_EMAIL'],
            "client_id": os.environ['GOOGLE_CLIENT_ID'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }, scopes=SCOPES)
        
        gc = gspread.authorize(creds)
        return gc.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def parse_player_picks(message_body):
    """Parse player names from WhatsApp message"""
    lines = message_body.strip().split('\n')
    players = []
    
    for line in lines:
        # Clean up the line
        cleaned = line.strip()
        # Skip empty lines and lines that are just numbers
        if cleaned and not re.match(r'^\d+$', cleaned):
            players.append(cleaned)
    
    return players

def add_to_google_sheet(phone_number, players):
    """Add player picks to Google Sheets"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            raise Exception("Could not connect to Google Sheets")
        
        # Get user identity
        user_id = user_map.get(phone_number, phone_number)
        
        # Prepare row data
        row_data = [
            datetime.now().isoformat(),  # Timestamp
            phone_number,                # Phone Number
            user_id,                     # User ID
            players[0] if len(players) > 0 else '',  # Player 1
            players[1] if len(players) > 1 else '',  # Player 2
            players[2] if len(players) > 2 else '',  # Player 3
            players[3] if len(players) > 3 else '',  # Player 4
        ]
        
        # Add row to sheet
        sheet.append_row(row_data)
        print(f"Added picks for {user_id}: {', '.join(players)}")
        return True
        
    except Exception as e:
        print(f"Error adding to sheet: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        # Get message details
        from_number = request.form.get('From', '').replace('whatsapp:', '')
        to_number = request.form.get('To', '')
        message_body = request.form.get('Body', '')
        
        print(f"Received message from {from_number}: {message_body}")
        
        # Parse player picks
        players = parse_player_picks(message_body)
        
        # Create response
        resp = MessagingResponse()
        
        if len(players) == 4:
            # Valid picks - add to sheet
            success = add_to_google_sheet(from_number, players)
            
            if success:
                response_text = f"✅ Got your picks: {', '.join(players)}"
            else:
                response_text = "❌ Sorry, there was an error saving your picks. Please try again."
        else:
            # Invalid format
            response_text = (
                "❌ Please send exactly 4 player names, one per line.\n\n"
                "Example:\n"
                "Gyokeres\n"
                "Salah\n"
                "Sesko\n"
                "Haaland"
            )
        
        resp.message(response_text)
        return str(resp)
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        resp = MessagingResponse()
        resp.message("❌ Sorry, something went wrong. Please try again.")
        return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'OK', 'message': 'WhatsApp bot is running'}, 200

def setup_google_sheet_headers():
    """Set up the headers in Google Sheets (run once)"""
    try:
        sheet = get_google_sheet()
        if sheet:
            headers = ['Timestamp', 'Phone Number', 'User ID', 'Player 1', 'Player 2', 'Player 3', 'Player 4']
            
            # Check if headers already exist
            if not sheet.row_values(1):
                sheet.insert_row(headers, 1)
                print("Headers added to Google Sheet")
            else:
                print("Headers already exist in Google Sheet")
        
    except Exception as e:
        print(f"Error setting up headers: {e}")

if __name__ == '__main__':
    # Set up Google Sheet headers on startup
    setup_google_sheet_headers()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')
