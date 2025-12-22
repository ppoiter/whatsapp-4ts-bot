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
            
            # Also update User Status sheet
            self.update_user_status_picks(phone_number, players, gameweek_num)
            
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
            
            # Normalize player name for consistency (title case)
            normalized_player = player_name.strip().title()
            
            # Check if this player already has a record for this gameweek
            all_records = scores_sheet.get_all_records()
            row_to_update = None
            
            for i, record in enumerate(all_records, start=2):  # Start at 2 because row 1 is headers
                existing_player = record.get('Player', '').strip().title()
                if str(record.get('Gameweek')) == str(gameweek_num) and existing_player == normalized_player:
                    row_to_update = i
                    break
            
            if row_to_update:
                # Update existing row
                scores_sheet.update_cell(row_to_update, 3, 'Yes' if scored else 'No')
                scores_sheet.update_cell(row_to_update, 4, datetime.now().isoformat())
            else:
                # Add new row with normalized name
                scores_sheet.append_row([
                    gameweek_num,
                    normalized_player,
                    'Yes' if scored else 'No',
                    datetime.now().isoformat()
                ])
            
            # Also update User Status sheet
            self.update_player_scores_in_status(normalized_player, scored, gameweek_num)
            
            return True, f"Updated: {normalized_player} {'scored' if scored else 'did not score'} in GW{gameweek_num}"
            
        except Exception as e:
            print(f"Error updating player status: {e}")
            return False, str(e)

    def get_elimination_status(self, gameweek_num):
        """Get win/lose status for all users in a gameweek (Four to Score rules)"""
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
                
                # Build a dict of players who scored (using title case for consistency)
                scorers = {}
                for record in scores_records:
                    record_gw = str(record.get('Gameweek'))
                    if record_gw == str(gameweek_num):
                        player = record.get('Player', '').strip().title()
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
                'won': [],  # All 4 players scored
                'lost': [],  # At least one player didn't score
                'pending': []  # Not all players checked yet
            }
            
            for phone, data in picks.items():
                user_name = data['user_name']
                players = data['players']
                
                # Check if ALL players scored (need all 4 to win)
                all_scored = True
                all_checked = True
                player_status = []
                
                for player in players:
                    player_normalized = player.strip().title()
                    print(f"DEBUG: Checking player '{player_normalized}' for {user_name}")
                    if player_normalized in scorers:
                        if scorers[player_normalized]:
                            player_status.append(f"✅ {player}")
                            print(f"DEBUG: Player '{player_normalized}' scored!")
                        else:
                            all_scored = False
                            player_status.append(f"❌ {player}")
                            print(f"DEBUG: Player '{player_normalized}' did not score")
                    else:
                        all_checked = False
                        all_scored = False  # Can't have won if not all checked
                        player_status.append(f"⏳ {player}")
                        print(f"DEBUG: Player '{player_normalized}' not found in scorers dict")
                
                status_text = f"{user_name}: {', '.join(player_status)}"
                
                if all_checked:
                    if all_scored:
                        results['won'].append(status_text)
                    else:
                        results['lost'].append(status_text)
                else:
                    results['pending'].append(status_text)
            
            # Add users who didn't submit
            for phone, name in self.user_map.items():
                if phone not in picks:
                    results['lost'].append(f"{name}: ❌ No picks submitted")
            
            return results
            
        except Exception as e:
            print(f"Error getting elimination status: {e}")
            return None
    
    def setup_user_status_sheet(self):
        """Set up the User Status sheet with headers (run once)"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to Google Sheets"
            
            # Create User Status worksheet if it doesn't exist
            try:
                status_sheet = sheet.spreadsheet.worksheet("User Status")
                print("User Status sheet already exists")
                return True, "User Status sheet already exists"
            except:
                # Create the sheet
                status_sheet = sheet.spreadsheet.add_worksheet(title="User Status", rows=500, cols=15)
                headers = [
                    'Timestamp', 'Gameweek', 'Phone Number', 'User Name',
                    'Player 1', 'P1 Scored', 'Player 2', 'P2 Scored',
                    'Player 3', 'P3 Scored', 'Player 4', 'P4 Scored',
                    'Status', 'Updated'
                ]
                status_sheet.insert_row(headers, 1)
                print("Created User Status sheet with headers")
                return True, "Created User Status sheet with headers"
                
        except Exception as e:
            print(f"Error setting up User Status sheet: {e}")
            return False, str(e)
    
    def update_user_status_picks(self, phone_number, players, gameweek_num):
        """Add or update user picks in User Status sheet"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            
            # Get or create User Status worksheet
            try:
                status_sheet = sheet.spreadsheet.worksheet("User Status")
            except:
                # Create sheet if it doesn't exist
                self.setup_user_status_sheet()
                status_sheet = sheet.spreadsheet.worksheet("User Status")
            
            user_name = self.user_map.get(phone_number, phone_number)
            
            # Check if user already has entry for this gameweek
            all_records = status_sheet.get_all_records()
            row_to_update = None
            latest_timestamp = ''
            
            # Find the most recent entry for this user in this gameweek
            for i, record in enumerate(all_records, start=2):  # Start at 2 because row 1 is headers
                if str(record.get('Gameweek')) == str(gameweek_num) and record.get('Phone Number') == phone_number:
                    record_timestamp = record.get('Timestamp', '')
                    if not row_to_update or record_timestamp > latest_timestamp:
                        row_to_update = i
                        latest_timestamp = record_timestamp
            
            if row_to_update:
                # Update existing row
                status_sheet.update(f'A{row_to_update}:N{row_to_update}', [[
                    datetime.now().isoformat(),
                    gameweek_num,
                    phone_number,
                    user_name,
                    players[0], '', players[1], '', 
                    players[2], '', players[3], '',
                    'Pending',
                    datetime.now().isoformat()
                ]])
            else:
                # Add new row
                status_sheet.append_row([
                    datetime.now().isoformat(),
                    gameweek_num,
                    phone_number,
                    user_name,
                    players[0], '', players[1], '', 
                    players[2], '', players[3], '',
                    'Pending',
                    datetime.now().isoformat()
                ])
            
            return True, f"Updated User Status for {user_name}"
            
        except Exception as e:
            print(f"Error updating user status picks: {e}")
            return False, str(e)
    
    def update_player_scores_in_status(self, player_name, scored, gameweek_num):
        """Update User Status sheet when a player's score is marked"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            
            # Get User Status worksheet
            try:
                status_sheet = sheet.spreadsheet.worksheet("User Status")
            except:
                return False, "User Status sheet not found"
            
            # Normalize player name
            normalized_player = player_name.strip().title()
            
            # Get all records for this gameweek
            all_records = status_sheet.get_all_records()
            updates_made = 0
            
            for i, record in enumerate(all_records, start=2):
                if str(record.get('Gameweek')) == str(gameweek_num):
                    # Check each player column
                    row_updated = False
                    player_columns = [
                        ('Player 1', 'P1 Scored', 5, 6),
                        ('Player 2', 'P2 Scored', 7, 8),
                        ('Player 3', 'P3 Scored', 9, 10),
                        ('Player 4', 'P4 Scored', 11, 12)
                    ]
                    
                    for player_col, score_col, player_idx, score_idx in player_columns:
                        player_in_sheet = str(record.get(player_col, '')).strip().title()
                        if player_in_sheet == normalized_player:
                            # Update the scored column
                            status_sheet.update_cell(i, score_idx, 'Yes' if scored else 'No')
                            row_updated = True
                    
                    if row_updated:
                        # Recalculate status for this user
                        all_scored = True
                        any_failed = False
                        all_checked = True
                        
                        # Re-fetch the row to get updated values
                        row_values = status_sheet.row_values(i)
                        for score_idx in [6, 8, 10, 12]:  # P1, P2, P3, P4 Scored columns
                            if score_idx <= len(row_values):
                                score_val = row_values[score_idx - 1].strip().lower() if score_idx - 1 < len(row_values) else ''
                                if score_val == 'no':
                                    all_scored = False
                                    any_failed = True
                                elif score_val != 'yes':
                                    all_scored = False
                                    all_checked = False
                        
                        # Update status
                        if any_failed:
                            new_status = 'Lost'
                        elif all_scored and all_checked:
                            new_status = 'Won'
                        else:
                            new_status = 'Pending'
                        
                        status_sheet.update_cell(i, 13, new_status)  # Status column
                        status_sheet.update_cell(i, 14, datetime.now().isoformat())  # Updated column
                        updates_made += 1
            
            return True, f"Updated {updates_made} user statuses for {normalized_player}"
            
        except Exception as e:
            print(f"Error updating player scores in status: {e}")
            return False, str(e)
    
    def eliminate_user(self, user_identifier, gameweek_num):
        """Manually set a user's status to Lost"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            
            # Get User Status worksheet
            try:
                status_sheet = sheet.spreadsheet.worksheet("User Status")
            except:
                return False, "User Status sheet not found"
            
            # Normalize user identifier for matching
            user_lower = user_identifier.strip().lower()
            
            # Find user in sheet
            all_records = status_sheet.get_all_records()
            found = False
            
            for i, record in enumerate(all_records, start=2):
                if str(record.get('Gameweek')) == str(gameweek_num):
                    # Check if identifier matches phone or name
                    user_name_in_sheet = str(record.get('User Name', '')).strip()
                    phone_in_sheet = str(record.get('Phone Number', '')).strip()
                    
                    name_match = user_name_in_sheet.lower() == user_lower
                    phone_match = phone_in_sheet == user_identifier
                    
                    if name_match or phone_match:
                        # Update status to Lost
                        status_sheet.update_cell(i, 13, 'Lost')  # Status column
                        status_sheet.update_cell(i, 14, datetime.now().isoformat())  # Updated column
                        found = True
                        user_name = record.get('User Name', user_identifier)
                        break
            
            if found:
                return True, f"Eliminated {user_name} for GW{gameweek_num}"
            else:
                return False, f"User '{user_identifier}' not found in GW{gameweek_num}"
                
        except Exception as e:
            print(f"Error eliminating user: {e}")
            return False, str(e)
    
    def get_user_status_from_sheet(self, gameweek_num):
        """Get user status from User Status sheet (no calculation needed)"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return None
            
            # Get User Status worksheet
            try:
                status_sheet = sheet.spreadsheet.worksheet("User Status")
                all_records = status_sheet.get_all_records()
            except:
                # Fall back to old calculation method if sheet doesn't exist
                return self.get_elimination_status(gameweek_num)
            
            results = {
                'won': [],
                'lost': [],
                'pending': []
            }
            
            # Dictionary to store latest entry per phone number
            latest_entries = {}
            
            # Process each record for this gameweek and keep only the latest per user
            for record in all_records:
                if str(record.get('Gameweek')) == str(gameweek_num):
                    phone = record.get('Phone Number', '')
                    timestamp = record.get('Timestamp', '')
                    
                    # Keep the record with the latest timestamp for each phone
                    if phone not in latest_entries or timestamp > latest_entries[phone]['Timestamp']:
                        latest_entries[phone] = record
            
            # Process the latest entries
            processed_users = set()  # Track which users we've already processed
            
            for phone, record in latest_entries.items():
                user_name = record.get('User Name', '')
                status = record.get('Status', 'Pending')
                
                # Mark this user as processed
                processed_users.add(user_name)
                
                # Build player list with scoring indicators
                players_display = []
                for i in range(1, 5):
                    player = record.get(f'Player {i}', '')
                    scored = record.get(f'P{i} Scored', '').strip().lower()
                    
                    if player:
                        if scored == 'yes':
                            # Bold for scored players (WhatsApp formatting)
                            players_display.append(f"*{player}*")
                        elif scored == 'no':
                            players_display.append(player)
                        else:
                            # Pending - show with indicator
                            players_display.append(f"{player}")
                
                status_text = f"{user_name}: {', '.join(players_display)}"
                
                if status == 'Won':
                    results['won'].append(status_text)
                elif status == 'Lost':
                    results['lost'].append(status_text)
                else:
                    results['pending'].append(status_text)
            
            # Add users who haven't submitted (check by name to avoid phone format issues)
            for phone, name in self.user_map.items():
                if name not in processed_users:
                    results['lost'].append(f"{name}: No picks submitted")
            
            return results
            
        except Exception as e:
            print(f"Error getting user status from sheet: {e}")
            # Fall back to calculation method
            return self.get_elimination_status(gameweek_num)