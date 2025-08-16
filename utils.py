from google.oauth2.service_account import Credentials
import pytz
from datetime import datetime, timedelta
from constants import GAMEWEEK_SCHEDULE, SPREADSHEET_ID, SCOPES, USER_MAP, ADMIN_PHONE
import gspread
import os
import re

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

user_map = USER_MAP

def get_uk_timezone():
    """Get UK timezone (handles BST/GMT automatically)"""
    return pytz.timezone('Europe/London')

def get_current_gameweek():
    """Determine which gameweek we're currently in based on current time"""
    uk_tz = get_uk_timezone()
    now = datetime.now(uk_tz).replace(tzinfo=None)  # Remove timezone for comparison
    
    for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
        # Convert dates to UK timezone
        uk_start = uk_tz.localize(start_date).replace(tzinfo=None)
        uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
        
        # Check if we're in the submission window for this gameweek
        # Window opens after previous gameweek ends, closes at deadline
        if gw_num == 1:
            # First gameweek - allow submissions from start of season
            window_start = uk_start - timedelta(days=7)
        else:
            # Subsequent gameweeks - window opens after previous gameweek starts
            prev_start = uk_tz.localize(GAMEWEEK_SCHEDULE[gw_num-2][1]).replace(tzinfo=None)
            window_start = prev_start
        
        if window_start <= now <= uk_deadline:
            return gw_num, uk_deadline
    
    # If no active gameweek found, return the next upcoming one
    for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
        uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
        if now < uk_deadline:
            return gw_num, uk_deadline
    
    return None, None

def is_deadline_passed(gameweek_num):
    """Check if the deadline for a specific gameweek has passed"""
    uk_tz = get_uk_timezone()
    now = datetime.now(uk_tz).replace(tzinfo=None)
    
    for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
        if gw_num == gameweek_num:
            uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
            return now > uk_deadline
    
    return True  # If gameweek not found, assume deadline passed

def format_deadline(deadline_dt):
    """Format deadline time for display"""
    uk_tz = get_uk_timezone()
    uk_deadline = uk_tz.localize(deadline_dt)
    return uk_deadline.strftime("%A %d %B at %H:%M")

def get_google_sheet():
    """Initialize Google Sheets connection"""
    try:
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
        cleaned = line.strip()
        if cleaned and not re.match(r'^\d+$', cleaned):
            players.append(cleaned)
    
    return players

def add_to_google_sheet(phone_number, players, gameweek_num, deadline):
    """Add player picks to Google Sheets with gameweek info"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            raise Exception("Could not connect to Google Sheets")
        
        user_id = user_map.get(phone_number, phone_number)
        
        # Always add as new row (duplicates allowed)
        # Prepare row data
        row_data = [
            datetime.now().isoformat(),  # Timestamp
            phone_number,                # Phone Number
            user_id,                     # User ID
            gameweek_num,               # Gameweek
            deadline.strftime("%Y-%m-%d %H:%M"),  # Deadline
            players[0] if len(players) > 0 else '',  # Player 1
            players[1] if len(players) > 1 else '',  # Player 2
            players[2] if len(players) > 2 else '',  # Player 3
            players[3] if len(players) > 3 else '',  # Player 4
        ]
        
        sheet.append_row(row_data)
        print(f"Added GW{gameweek_num} picks for {user_id}: {', '.join(players)}")
        return True, "success"
        
    except Exception as e:
        print(f"Error adding to sheet: {e}")
        return False, "error"


def send_instructions(current_gameweek, deadline):
    """Generate welcome/instructions message"""
    deadline_str = format_deadline(deadline)

    return (
        f"⚽ Welcome to the 4 To Score Picks Bot ⚽\n"
        f"📝 To submit picks for Gameweek {current_gameweek}:\n"
        f"Send 4 player names, one per line:\n\n"
        f"Example:\n"
        f"Haaland\n"
        f"Salah\n"
        f"Saka\n"
        f"Palmer\n\n"
        f"⏰ Deadline: {deadline_str}\n"
        f"✅ You can update picks by sending new ones\n"
    )

def get_users_without_picks(gameweek_num):
    """Get list of users who haven't submitted picks for current gameweek"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            return []
        
        # Get all records
        all_records = sheet.get_all_records()
        
        # Find users who submitted for this gameweek
        users_submitted = set()
        for record in all_records:
            if record.get('Gameweek') == gameweek_num:
                phone = record.get('Phone Number')
                if phone:
                    users_submitted.add(phone)
        
        # Find users who haven't submitted
        users_without_picks = []
        for phone in USER_MAP:
            if phone not in users_submitted:
                users_without_picks.append(phone)
        
        return users_without_picks
        
    except Exception as e:
        print(f"Error checking submissions: {e}")
        return []

def send_reminder(phone_number, gameweek_num, deadline, twilio_client):
    """Send reminder message to a single user"""
    try:
        user_name = user_map.get(phone_number, "Player")
        deadline_str = deadline.strftime("%H:%M")
        
        message = (
            f"⏰ Reminder: {user_name}, you haven't submitted your picks for Gameweek {gameweek_num}!\n\n"
            f"🚨 Deadline is in 12 hours: {deadline_str}\n\n"
        )
        
        twilio_client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',  # Your Twilio sandbox number
            to=f'whatsapp:{phone_number}'
        )
        print(f"Reminder sent to {user_name} ({phone_number})")
        
    except Exception as e:
        print(f"Error sending reminder to {phone_number}: {e}")

def send_reminders_for_gameweek(twilio_client):
    """Send reminders to all users without picks (called by scheduler)"""
    current_gw, deadline = get_current_gameweek()
    
    if not current_gw:
        print("No active gameweek for reminders")
        return
    
    users_without_picks = get_users_without_picks(current_gw)
    
    if users_without_picks:
        print(f"Sending reminders to {len(users_without_picks)} users for GW{current_gw}")
        for phone in users_without_picks:
            send_reminder(phone, current_gw, deadline, twilio_client)
    else:
        print(f"All users have submitted picks for GW{current_gw}")

def schedule_gameweek_reminders(twilio_client):
    """Schedule reminders for all gameweeks (4 hours before deadline)"""
    scheduler = BackgroundScheduler(timezone=get_uk_timezone())
    
    for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
        # Schedule reminder 12 hours before deadline
        reminder_time = deadline - timedelta(hours=12)
        
        # Only schedule if reminder time is in the future
        uk_tz = get_uk_timezone()
        now = datetime.now(uk_tz).replace(tzinfo=None)
        uk_reminder = uk_tz.localize(reminder_time).replace(tzinfo=None)
        
        if uk_reminder > now:
            trigger = DateTrigger(run_date=reminder_time, timezone=uk_tz)
            scheduler.add_job(
                send_reminders_for_gameweek(twilio_client),
                trigger=trigger,
                id=f'gw_{gw_num}_reminder',
                name=f'Gameweek {gw_num} Reminder'
            )
            print(f"Scheduled reminder for GW{gw_num} at {reminder_time}")
    
    return scheduler


def get_all_picks_for_gameweek(gameweek_num):
    """Get all picks submitted for a gameweek, taking latest submission per user"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            return {}
        
        all_records = sheet.get_all_records()
        
        # Dictionary to store latest picks per user
        user_picks = {}
        
        for record in all_records:
            if str(record.get('Gameweek')) == str(gameweek_num):
                # Phone number comes as integer, need to add + back
                phone_int = record.get('Phone Number')
                phone = f'+{phone_int}' if phone_int else None
                timestamp = record.get('Timestamp')
                
                # Get the 4 players
                players = []
                for i in range(1, 5):
                    player = record.get(f'Player {i}', '').strip()
                    if player:
                        players.append(player)
                
                if phone and players:
                    # Check if we already have picks for this user
                    if phone not in user_picks or timestamp > user_picks[phone]['timestamp']:
                        user_picks[phone] = {
                            'players': players,
                            'timestamp': timestamp,
                            'user_name': user_map.get(phone, phone)
                        }
        
        return user_picks
        
    except Exception as e:
        print(f"Error getting picks: {e}")
        return {}
        
    except Exception as e:
        print(f"Error getting picks: {e}")
        return {}

def send_deadline_summary(gameweek_num=None, twilio_client=None):
    """Send summary of all picks to admin after deadline"""
    try:
        from constants import ADMIN_PHONE
        
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
        submitted_picks = get_all_picks_for_gameweek(gameweek_num)
        
        # Build the summary message
        message = f"📊 GAMEWEEK {gameweek_num} FINAL PICKS\n"
        message += "=" * 25 + "\n\n"
        
        # Track who hasn't submitted
        users_without_picks = []
        
        # Check all users in USER_MAP
        for phone, name in user_map.items():
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
        twilio_client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',
            to=f'whatsapp:{ADMIN_PHONE}'
        )
        
    except Exception as e:
        print(f"Error sending deadline summary: {e}")

def schedule_deadline_summaries(twilio_client):
    """Schedule summary messages for all gameweek deadlines"""
    scheduler = BackgroundScheduler(timezone=get_uk_timezone())
    
    for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
        # Schedule summary 1 minute after deadline
        summary_time = deadline + timedelta(minutes=1)
        
        # Only schedule if time is in the future
        uk_tz = get_uk_timezone()
        now = datetime.now(uk_tz).replace(tzinfo=None)
        uk_summary = uk_tz.localize(summary_time).replace(tzinfo=None)
        
        if uk_summary > now:
            trigger = DateTrigger(run_date=summary_time, timezone=uk_tz)
            scheduler.add_job(
                lambda gw=gw_num: send_deadline_summary(gw, twilio_client),
                trigger=trigger,
                id=f'gw_{gw_num}_summary',
                name=f'Gameweek {gw_num} Summary'
            )
            print(f"Scheduled summary for GW{gw_num} at {summary_time}")
    
    return scheduler
