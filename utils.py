from google.oauth2.service_account import Credentials
import pytz
from datetime import datetime, timedelta
from constants import GAMEWEEK_SCHEDULE, SPREADSHEET_ID, SCOPES, USER_MAP
import gspread
import os
import re

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