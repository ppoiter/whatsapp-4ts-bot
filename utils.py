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

def update_player_scored_status(gameweek_num, player_name, scored):
    """Update whether a player scored in a gameweek"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            return False, "Could not connect to sheet"
        
        # Find or create a "Player Scores" worksheet
        try:
            scores_sheet = sheet.spreadsheet.worksheet("Player Scores")
        except:
            # Create the sheet if it doesn't exist
            scores_sheet = sheet.spreadsheet.add_worksheet(title="Player Scores", rows=100, cols=10)
            scores_sheet.append_row(['Gameweek', 'Player', 'Scored', 'Updated'])
        
        # Check if this player already has a record for this gameweek
        all_records = scores_sheet.get_all_records()
        row_to_update = None
        
        for i, record in enumerate(all_records, start=2):  # Start at 2 because row 1 is headers
            if str(record.get('Gameweek')) == str(gameweek_num) and record.get('Player', '').lower() == player_name.lower():
                row_to_update = i
                break
        
        if row_to_update:
            # Update existing row
            scores_sheet.update_cell(row_to_update, 3, 'Yes' if scored else 'No')
            scores_sheet.update_cell(row_to_update, 4, datetime.now().isoformat())
        else:
            # Add new row
            scores_sheet.append_row([
                gameweek_num,
                player_name,
                'Yes' if scored else 'No',
                datetime.now().isoformat()
            ])
        
        return True, f"Updated: {player_name} {'scored' if scored else 'did not score'} in GW{gameweek_num}"
        
    except Exception as e:
        print(f"Error updating player status: {e}")
        return False, str(e)

def get_elimination_status(gameweek_num):
    """Get elimination status for all users in a gameweek"""
    try:
        sheet = get_google_sheet()
        if not sheet:
            return None
        
        # Get all picks for the gameweek
        picks = get_all_picks_for_gameweek(gameweek_num)
        
        # Try to get scoring data
        try:
            scores_sheet = sheet.spreadsheet.worksheet("Player Scores")
            scores_records = scores_sheet.get_all_records()
            
            # Build a dict of players who scored
            scorers = {}
            for record in scores_records:
                if str(record.get('Gameweek')) == str(gameweek_num):
                    player = record.get('Player', '').lower()
                    scored = record.get('Scored', '').lower() == 'yes'
                    scorers[player] = scored
        except:
            # No scores sheet yet
            scorers = {}
        
        # Check each user's status
        results = {
            'active': [],
            'eliminated': [],
            'pending': []
        }
        
        for phone, data in picks.items():
            user_name = data['user_name']
            players = data['players']
            
            # Check if any of their players scored
            has_scorer = False
            all_checked = True
            player_status = []
            
            for player in players:
                player_lower = player.lower()
                if player_lower in scorers:
                    if scorers[player_lower]:
                        has_scorer = True
                        player_status.append(f"✅ {player}")
                    else:
                        player_status.append(f"❌ {player}")
                else:
                    all_checked = False
                    player_status.append(f"⏳ {player}")
            
            status_text = f"{user_name}: {', '.join(player_status)}"
            
            if all_checked:
                if has_scorer:
                    results['active'].append(status_text)
                else:
                    results['eliminated'].append(status_text)
            else:
                results['pending'].append(status_text)
        
        # Add users who didn't submit
        for phone, name in user_map.items():
            if phone not in picks:
                results['eliminated'].append(f"{name}: ❌ No picks submitted")
        
        return results
        
    except Exception as e:
        print(f"Error getting elimination status: {e}")
        return None

# # Add this endpoint for testing eliminations
# @app.route('/elimination-status/<int:gameweek>', methods=['GET'])
# def get_elimination_status_endpoint(gameweek):
#     """Get elimination status via HTTP"""
#     try:
#         results = get_elimination_status(gameweek)
#         if results:
#             return {
#                 'gameweek': gameweek,
#                 'active': results['active'],
#                 'eliminated': results['eliminated'],
#                 'pending': results['pending']
#             }, 200
#         else:
#             return {'error': 'Could not get status'}, 500
#     except Exception as e:
#         return {'error': str(e)}, 500    

def process_admin_command(message_body, gameweek_num):
    """Process admin commands for scoring updates"""
    message_lower = message_body.lower().strip()
    
    # Check for scoring commands
    if message_lower.startswith('goal ') or message_lower.startswith('no goal '):
        if message_lower.startswith('goal '):
            # Player scored
            player = message_lower.replace('goal ', '', 1).strip()
            scored = True
        else:
            # Player didn't score
            player = message_lower.replace('no goal ', '', 1).strip()
            scored = False
        
        if player:
            success, msg = update_player_scored_status(gameweek_num, player, scored)
            if success:
                return f"✅ {player}: {'GOAL! ⚽' if scored else 'No goal'}"
            else:
                return f"❌ Error updating {player}"
        else:
            return "Please specify a player name"
    
    # Check for active status request
    elif message_lower in ['show active', 'active', 'whos in', 'who is in']:
        results = get_elimination_status(gameweek_num)
        
        if results:
            message = f"🎯 GAMEWEEK {gameweek_num} STATUS\n"
            message += "=" * 25 + "\n\n"
            
            # Combine all users and sort by name
            all_users = []
            
            # Add active users
            for user_status in results['active']:
                # Extract just the name and players
                parts = user_status.split(': ', 1)
                if len(parts) == 2:
                    name = parts[0]
                    # Remove the emoji indicators from players
                    players = parts[1].replace('✅ ', '').replace('❌ ', '').replace('⏳ ', '')
                    all_users.append((name, players, 'active'))
            
            # Add eliminated users
            for user_status in results['eliminated']:
                parts = user_status.split(': ', 1)
                if len(parts) == 2:
                    name = parts[0]
                    players = parts[1].replace('✅ ', '').replace('❌ ', '').replace('⏳ ', '')
                    if 'No picks submitted' in players:
                        players = 'No picks submitted'
                    all_users.append((name, players, 'eliminated'))
            
            # Add pending users as active for now
            for user_status in results['pending']:
                parts = user_status.split(': ', 1)
                if len(parts) == 2:
                    name = parts[0]
                    players = parts[1].replace('✅ ', '').replace('❌ ', '').replace('⏳ ', '')
                    all_users.append((name, players, 'pending'))
            
            # Sort by name
            all_users.sort(key=lambda x: x[0])
            
            # Build the message
            for name, players, status in all_users:
                if status == 'eliminated':
                    # Using tilde for strikethrough (WhatsApp formatting)
                    message += f"👎 ~{name}: {players}~\n"
                else:
                    message += f"✅ {name}: {players}\n"
            
            # Add summary
            active_count = len(results['active']) + len(results['pending'])
            total_count = len(all_users)
            
            return message
        else:
            return "Error getting elimination status"
    
    return None
