from twilio.rest import Client
from datetime import datetime, timedelta
from config.settings import USER_MAP, ADMIN_PHONE, TWILIO_FROM_NUMBER
from services.sheets_service import SheetsService
from utils.date_utils import get_uk_timezone, get_current_gameweek
from config.settings import GAMEWEEK_SCHEDULE

class MessageService:
    def __init__(self, twilio_client):
        self.twilio_client = twilio_client
        self.sheets_service = SheetsService()
        self.user_map = USER_MAP

    def send_deadline_summary(self, gameweek_num=None):
        """Send summary of all picks to admin after deadline"""
        try:
            # If no gameweek specified, determine which one to show
            if gameweek_num is None:
                uk_tz = get_uk_timezone()
                now = datetime.now(uk_tz).replace(tzinfo=None)
                
                # Check recent gameweeks (within 24 hours of deadline)
                for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
                    uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
                    time_since_deadline = now - uk_deadline
                    
                    # If we're within 24 hours after the deadline, use this gameweek
                    if timedelta(0) <= time_since_deadline <= timedelta(hours=24):
                        gameweek_num = gw_num
                        break
                
                # If no recent deadline, use current gameweek
                if gameweek_num is None:
                    gameweek_num, _ = get_current_gameweek()
                    if not gameweek_num:
                        print("No active or recent gameweek found")
                        return
            
            # Get all submitted picks
            submitted_picks = self.sheets_service.get_all_picks_for_gameweek(gameweek_num)
            
            # Build the summary message
            message = f"📊 GAMEWEEK {gameweek_num} FINAL PICKS\n"
            message += "=" * 25 + "\n\n"
            
            # Track who hasn't submitted
            users_without_picks = []
            
            # Check all users in USER_MAP
            for phone, name in self.user_map.items():
                if phone in submitted_picks:
                    # User submitted picks
                    picks = submitted_picks[phone]['players']
                    message += f"✅ {name}: {', '.join(picks)}\n"
                else:
                    # User didn't submit
                    users_without_picks.append(name)
            
            # Add section for users who didn't submit
            if users_without_picks:
                message += "\n❌ NO PICKS SUBMITTED:\n"
                for name in users_without_picks:
                    message += f"  • {name}\n"
                message += "\n"
            
            # Send to admin
            self.twilio_client.messages.create(
                body=message,
                from_=TWILIO_FROM_NUMBER,
                to=f'whatsapp:{ADMIN_PHONE}'
            )
            
        except Exception as e:
            print(f"Error sending deadline summary: {e}")