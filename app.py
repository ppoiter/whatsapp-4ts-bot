from constants import USER_MAP, ADMIN_PHONE
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os

from utils import get_current_gameweek, is_deadline_passed, parse_player_picks, add_to_google_sheet, format_deadline, get_google_sheet, schedule_gameweek_reminders, schedule_deadline_summaries, send_reminders_for_gameweek, send_deadline_summary

app = Flask(__name__)

# Twilio setup
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_client = Client(account_sid, auth_token)

user_map = USER_MAP

@app.route('/send-reminders', methods=['POST'])
def manual_reminder_trigger():
    """Manually trigger reminders for testing"""
    try:
        send_reminders_for_gameweek(twilio_client)
        return {'status': 'success', 'message': 'Reminders sent'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/send-summary/<int:gameweek>', methods=['POST'])
def manual_summary_trigger(gameweek):
    """Manually trigger summary for testing"""
    try:
        send_deadline_summary(gameweek, twilio_client)
        return {'status': 'success', 'message': f'Summary sent for GW{gameweek}'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        from_number = request.form.get('From', '').replace('whatsapp:', '')
        message_body = request.form.get('Body', '')
        
        print(f"Received message from {from_number}: {message_body}")
        
        # Check current gameweek
        current_gameweek, deadline = get_current_gameweek()
        
        if not current_gameweek:
            resp = MessagingResponse()
            resp.message("🚫 No active gameweek found. Please check back when the new season starts!")
            return str(resp)
        
        # Check if deadline has passed
        if is_deadline_passed(current_gameweek):
            resp = MessagingResponse()
            resp.message(f"⏰ Sorry! The deadline for Gameweek {current_gameweek} has passed.")
            return str(resp)

        # ADD THIS NEW SECTION - Check for summary request
        if message_body.lower().strip() == 'show picks':
            # Check if this is the admin
            if from_number == ADMIN_PHONE:  # Remove + for comparison
                send_deadline_summary(current_gameweek, twilio_client)
                resp = MessagingResponse()
                resp.message(f"📊 Sending Gameweek {current_gameweek} summary...")
                return str(resp)
            else:
                resp = MessagingResponse()
                resp.message("⛔ Only the admin can request summaries.")
                return str(resp)
        
        # Parse player picks
        players = parse_player_picks(message_body)
        resp = MessagingResponse()
        
        if len(players) == 4:
            # Valid picks - add to sheet
            success, result = add_to_google_sheet(from_number, players, current_gameweek, deadline)
            
            if success:
                deadline_str = format_deadline(deadline)
                user_name = user_map.get(from_number, from_number)
                response_text = (
                    f"✅ GW{current_gameweek} picks saved for {user_name}!\n"
                    f"🎯 {', '.join(players)}\n"
                    f"⏰ Deadline: {deadline_str}"
                )
            else:
                response_text = "❌ Sorry, there was an error saving your picks. Please try again."
        else:
            deadline_str = format_deadline(deadline)
            response_text = (
                f"❌ Please send exactly 4 player names for Gameweek {current_gameweek}\n\n"
                f"Example:\n"
                f"Haaland\n"
                f"Salah\n"
                f"Saka\n"
                f"Palmer\n\n"
                f"⏰ Deadline: {deadline_str}"
            )
        
        resp.message(response_text)
        return str(resp)
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        resp = MessagingResponse()
        resp.message("❌ Sorry, something went wrong. Please try again.")
        return str(resp)

@app.route('/summary', methods=['GET'])
def get_summary():
    """Simple GET endpoint for browser access"""
    try:
        # Import ADMIN_PHONE if not already imported
        from constants import ADMIN_PHONE
        
        # Get current gameweek
        current_gw, _ = get_current_gameweek()
        
        if current_gw:
            send_deadline_summary(current_gw, twilio_client)
            return f"✅ Summary sent for Gameweek {current_gw} to {ADMIN_PHONE}", 200
        else:
            return "No active gameweek", 400
            
    except Exception as e:
        print(f"Error in get_summary: {e}")
        return f"Error: {str(e)}", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    current_gw, deadline = get_current_gameweek()
    return {
        'status': 'OK', 
        'message': 'WhatsApp bot is running',
        'current_gameweek': current_gw,
        'deadline': deadline.isoformat() if deadline else None
    }, 200

@app.route('/gameweek-info', methods=['GET'])
def gameweek_info():
    """API endpoint to check current gameweek status"""
    current_gw, deadline = get_current_gameweek()
    
    if current_gw:
        deadline_passed = is_deadline_passed(current_gw)
        return {
            'gameweek': current_gw,
            'deadline': deadline.isoformat(),
            'deadline_formatted': format_deadline(deadline),
            'deadline_passed': deadline_passed,
            'status': 'closed' if deadline_passed else 'open'
        }
    else:
        return {'status': 'no_active_gameweek'}

def setup_google_sheet_headers():
    """Set up the headers in Google Sheets (run once)"""
    try:
        sheet = get_google_sheet()
        if sheet:
            headers = ['Timestamp', 'Phone Number', 'User ID', 'Gameweek', 'Deadline', 'Player 1', 'Player 2', 'Player 3', 'Player 4']
            
            if not sheet.row_values(1):
                sheet.insert_row(headers, 1)
                print("Headers added to Google Sheet")
            else:
                print("Headers already exist in Google Sheet")
        
    except Exception as e:
        print(f"Error setting up headers: {e}")

# UPDATE your main section to include both schedulers
if __name__ == '__main__':
    setup_google_sheet_headers()
    
    # # Start the reminder scheduler
    # reminder_scheduler = schedule_gameweek_reminders(twilio_client)
    # reminder_scheduler.start()
    # print("Reminder scheduler started")
    
    # Start the deadline summary scheduler
    summary_scheduler = schedule_deadline_summaries(twilio_client)
    summary_scheduler.start()
    print("Summary scheduler started")
    
    # Keep schedulers running with the app
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')
    except (KeyboardInterrupt, SystemExit):
        # reminder_scheduler.shutdown()
        summary_scheduler.shutdown()