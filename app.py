from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os

from config.settings import ADMIN_PHONE, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, USER_MAP
from services.sheets_service import SheetsService
from services.message_service import MessageService
from services.gameweek_service import GameweekService
from services.scheduler_service import SchedulerService
from utils.date_utils import get_current_gameweek, is_deadline_passed, format_deadline
from utils.text_utils import parse_player_picks

app = Flask(__name__)

# Initialize services
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
sheets_service = SheetsService()
message_service = MessageService(twilio_client)
gameweek_service = GameweekService()
scheduler_service = SchedulerService(message_service)

@app.route('/send-summary/<int:gameweek>', methods=['POST'])
def manual_summary_trigger(gameweek):
    """Manually trigger summary for testing"""
    try:
        message_service.send_deadline_summary(gameweek)
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

        # Check for admin commands first (for admin user)
        if from_number == ADMIN_PHONE.lstrip('+'):
            admin_response = gameweek_service.process_admin_command(message_body, current_gameweek)
            if admin_response:
                resp = MessagingResponse()
                resp.message(admin_response)
                return str(resp)
            
            # Existing summary command
            if message_body.lower().strip() in ['summary', 'picks', 'show picks', 'show']:
                message_service.send_deadline_summary(current_gameweek)
                resp = MessagingResponse()
                resp.message(f"📊 Sending Gameweek {current_gameweek} summary...")
                return str(resp)
        
        # Handle specific commands for all users before trying to parse as picks
        message_lower = message_body.lower().strip()
        if message_lower in ['show active', 'active', 'whos in', 'who is in']:
            resp = MessagingResponse()
            if from_number == ADMIN_PHONE.lstrip('+'):
                admin_response = gameweek_service.process_admin_command(message_body, current_gameweek)
                resp.message(admin_response if admin_response else "Error processing command")
            else:
                resp.message("⛔ Only the admin can request active player status.")
            return str(resp)
        
        # Check if deadline has passed
        if is_deadline_passed(current_gameweek):
            resp = MessagingResponse()
            resp.message(f"⏰ Sorry! The deadline for Gameweek {current_gameweek} has passed.")
            return str(resp)

        if message_body.lower().strip() == 'show picks':
            # Check if this is the admin
            if from_number == ADMIN_PHONE.lstrip('+'):  # Remove + for comparison
                message_service.send_deadline_summary(current_gameweek)
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
            success, result = sheets_service.add_to_google_sheet(from_number, players, current_gameweek, deadline)
            
            if success:
                deadline_str = format_deadline(deadline)
                user_name = USER_MAP.get(from_number, from_number)
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
        # Get current gameweek
        current_gw, _ = get_current_gameweek()
        
        if current_gw:
            message_service.send_deadline_summary(current_gw)
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

if __name__ == '__main__':
    # Setup Google Sheets headers
    sheets_service.setup_google_sheet_headers()
    
    # Start the deadline summary scheduler
    summary_scheduler = scheduler_service.schedule_deadline_summaries()
    summary_scheduler.start()
    print("Summary scheduler started")
    
    # Keep schedulers running with the app
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')
    except (KeyboardInterrupt, SystemExit):
        summary_scheduler.shutdown()