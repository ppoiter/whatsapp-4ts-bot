from google.oauth2.service_account import Credentials
import gspread
import os
from datetime import datetime
from config.settings import SPREADSHEET_ID, SCOPES, USER_MAP

class SheetsService:
    def __init__(self):
        self.user_map = USER_MAP
    
    def get_google_sheet(self):
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

    def setup_google_sheet_headers(self):
        """Set up the headers in Google Sheets (run once)"""
        try:
            sheet = self.get_google_sheet()
            if sheet:
                headers = ['Timestamp', 'Phone Number', 'User ID', 'Gameweek', 'Deadline', 'Player 1', 'Player 2', 'Player 3', 'Player 4']
                
                if not sheet.row_values(1):
                    sheet.insert_row(headers, 1)
                    print("Headers added to Google Sheet")
                else:
                    print("Headers already exist in Google Sheet")
            
        except Exception as e:
            print(f"Error setting up headers: {e}")

    def add_to_google_sheet(self, phone_number, players, gameweek_num, deadline):
        """Add player picks to Google Sheets with gameweek info"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                raise Exception("Could not connect to Google Sheets")
            
            user_id = self.user_map.get(phone_number, phone_number)
            
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

    def get_all_picks_for_gameweek(self, gameweek_num):
        """Get all picks submitted for a gameweek, taking latest submission per user"""
        try:
            sheet = self.get_google_sheet()
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
                                'user_name': self.user_map.get(phone, phone)
                            }
            
            return user_picks
            
        except Exception as e:
            print(f"Error getting picks: {e}")
            return {}

    def get_users_without_picks(self, gameweek_num):
        """Get list of users who haven't submitted picks for current gameweek"""
        try:
            sheet = self.get_google_sheet()
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

    def update_player_scored_status(self, gameweek_num, player_name, scored):
        """Update whether a player scored in a gameweek"""
        try:
            sheet = self.get_google_sheet()
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

    def get_elimination_status(self, gameweek_num):
        """Get elimination status for all users in a gameweek"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return None
            
            # Get all picks for the gameweek
            picks = self.get_all_picks_for_gameweek(gameweek_num)
            
            # Try to get scoring data
            try:
                scores_sheet = sheet.spreadsheet.worksheet("Player Scores")
                scores_records = scores_sheet.get_all_records()
                
                print(f"DEBUG: Found {len(scores_records)} records in Player Scores sheet")
                print(f"DEBUG: Looking for gameweek {gameweek_num}")
                
                # Build a dict of players who scored
                scorers = {}
                for record in scores_records:
                    record_gw = str(record.get('Gameweek'))
                    if record_gw == str(gameweek_num):
                        player = record.get('Player', '').strip().lower()
                        scored_value = record.get('Scored', '').strip().lower()
                        scored = scored_value == 'yes'
                        scorers[player] = scored
                        print(f"DEBUG: Player '{player}' -> scored: {scored} (raw value: '{scored_value}')")
                
                print(f"DEBUG: Final scorers dict: {scorers}")
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
                    player_lower = player.strip().lower()
                    print(f"DEBUG: Checking player '{player_lower}' for {user_name}")
                    if player_lower in scorers:
                        if scorers[player_lower]:
                            has_scorer = True
                            player_status.append(f"✅ {player}")
                            print(f"DEBUG: Player '{player_lower}' scored!")
                        else:
                            player_status.append(f"❌ {player}")
                            print(f"DEBUG: Player '{player_lower}' did not score")
                    else:
                        all_checked = False
                        player_status.append(f"⏳ {player}")
                        print(f"DEBUG: Player '{player_lower}' not found in scorers dict")
                
                status_text = f"{user_name}: {', '.join(player_status)}"
                
                if all_checked:
                    if has_scorer:
                        results['active'].append(status_text)
                    else:
                        results['eliminated'].append(status_text)
                else:
                    results['pending'].append(status_text)
            
            # Add users who didn't submit
            for phone, name in self.user_map.items():
                if phone not in picks:
                    results['eliminated'].append(f"{name}: ❌ No picks submitted")
            
            return results
            
        except Exception as e:
            print(f"Error getting elimination status: {e}")
            return None