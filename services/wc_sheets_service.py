from google.oauth2.service_account import Credentials
import gspread
import os
from datetime import datetime
from config.settings import WC_MASTER_SHEET_ID, SCOPES, FIFA_RANK, GROUP_TOP_SEEDS
import re

class WCSheetsService:
    def __init__(self):
        self.master_sheet_id = WC_MASTER_SHEET_ID
        self._spreadsheet = None
    
    def get_google_sheet(self):
        """Initialize Google Sheets connection"""
        try:
            if self._spreadsheet:
                return self._spreadsheet
                
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
            self._spreadsheet = gc.open_by_key(self.master_sheet_id)
            return self._spreadsheet
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return None
    
    def setup_master_sheet_connection(self):
        """Test connection to master sheet on startup"""
        try:
            sheet = self.get_google_sheet()
            if sheet:
                print("✅ Connected to WC Master Sheet successfully")
                # List all worksheets for verification
                worksheets = [ws.title for ws in sheet.worksheets()]
                print(f"Available worksheets: {worksheets}")
            else:
                print("❌ Failed to connect to WC Master Sheet")
        except Exception as e:
            print(f"Error setting up master sheet connection: {e}")
    
    def strip_rank(self, team_name):
        """Strip ranking suffix from team names, e.g. 'England (#4)' -> 'England'"""
        return re.sub(r' \(#\d+\)', '', team_name.strip())
    
    def normalize_name(self, name):
        """Normalize participant name for grouping"""
        return name.strip().lower()
    
    def log_result(self, match_key, home_score, away_score, stage='group', matchday=None):
        """Log match result to results tab"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            
            results_sheet = sheet.worksheet('results')
            
            # Add result row
            row_data = [
                match_key,
                home_score,
                away_score,
                stage,
                matchday,
                datetime.now().isoformat()
            ]
            
            results_sheet.append_row(row_data)
            return True, f"Result logged: {match_key}"
            
        except Exception as e:
            print(f"Error logging result: {e}")
            return False, str(e)
    
    def award_bonus_points(self, form_num, player_names, points=2):
        """Award bonus points to specified players"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            
            bonus_sheet = sheet.worksheet('bonus')
            awarded_to = []
            
            for player_name in player_names:
                normalized_player = self.normalize_name(player_name)
                
                # Add bonus row
                row_data = [
                    form_num,
                    normalized_player,
                    points,
                    datetime.now().isoformat()
                ]
                
                bonus_sheet.append_row(row_data)
                awarded_to.append(player_name.title())
            
            return True, f"Bonus points awarded to: {', '.join(awarded_to)}"
            
        except Exception as e:
            print(f"Error awarding bonus points: {e}")
            return False, str(e)
    
    def get_all_picks(self):
        """Get all picks from all form response tabs"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return {}
            
            all_picks = {}
            
            for form_num in [1, 2, 3, 4]:
                tab_name = f'form{form_num}_picks'
                try:
                    form_sheet = sheet.worksheet(tab_name)
                    records = form_sheet.get_all_records()
                    
                    for record in records:
                        if not record.get('Timestamp'):
                            continue

                        name = ''
                        for key in record.keys():
                            if key.lower().startswith(('your name', 'first name', 'full name', 'name')):
                                name = record[key].strip()
                                if name:
                                    break
                        if not name:
                            continue
                            
                        normalized_name = self.normalize_name(name)
                        timestamp = record.get('Timestamp', '')
                        
                        if normalized_name not in all_picks:
                            all_picks[normalized_name] = {
                                'display_name': name.title(),
                                'forms': {}
                            }
                        
                        # Only keep latest submission per form
                        if form_num not in all_picks[normalized_name]['forms'] or \
                           timestamp > all_picks[normalized_name]['forms'][form_num].get('timestamp', ''):
                            all_picks[normalized_name]['forms'][form_num] = {
                                'timestamp': timestamp,
                                'picks': record
                            }
                
                except Exception as e:
                    print(f"Error reading {tab_name}: {e}")
                    continue
            
            return all_picks
            
        except Exception as e:
            print(f"Error getting picks: {e}")
            return {}
    
    def get_all_results(self):
        """Get all logged results"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return []
            
            results_sheet = sheet.worksheet('results')
            return results_sheet.get_all_records()
            
        except Exception as e:
            print(f"Error getting results: {e}")
            return []
    
    def get_all_bonus_awards(self):
        """Get all bonus point awards"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return []
            
            bonus_sheet = sheet.worksheet('bonus')
            return bonus_sheet.get_all_records()
            
        except Exception as e:
            print(f"Error getting bonus awards: {e}")
            return []
    
    def log_group_winner(self, group, team):
        """Log a group stage winner"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return False, "Could not connect to sheet"
            winners_sheet = sheet.worksheet('group_winners')
            winners_sheet.append_row([group.upper(), team, datetime.now().isoformat()])
            return True, f"Group {group.upper()} winner logged: {team}"
        except Exception as e:
            print(f"Error logging group winner: {e}")
            return False, str(e)

    def get_group_winners(self):
        """Get all logged group winners, returning latest entry per group"""
        try:
            sheet = self.get_google_sheet()
            if not sheet:
                return {}
            winners_sheet = sheet.worksheet('group_winners')
            records = winners_sheet.get_all_records()
            winners = {}
            for record in records:
                group = record.get('group', '').upper()
                team = record.get('team', '')
                if group and team:
                    winners[group] = team  # later entries overwrite earlier ones
            return winners
        except Exception as e:
            print(f"Error getting group winners: {e}")
            return {}

    def determine_match_stage_and_matchday(self, match_key):
        """Determine stage and matchday for a given match"""
        # For now, assume all matches are group stage
        # This can be enhanced later for knockout stages
        
        # Group stage fixtures mapping
        md1_fixtures = [
            'Mexico vs South Africa', 'South Korea vs Czechia', 'Canada vs Bosnia & Herzegovina',
            'Qatar vs Switzerland', 'Brazil vs Morocco', 'Haiti vs Scotland', 'USA vs Paraguay',
            'Australia vs Turkey', 'Germany vs Curacao', 'Ivory Coast vs Ecuador',
            'Netherlands vs Japan', 'Sweden vs Tunisia', 'Belgium vs Egypt',
            'Iran vs New Zealand', 'Spain vs Cape Verde', 'Saudi Arabia vs Uruguay',
            'France vs Senegal', 'Iraq vs Norway', 'Argentina vs Algeria',
            'Austria vs Jordan', 'Portugal vs DR Congo', 'Uzbekistan vs Colombia',
            'England vs Croatia', 'Ghana vs Panama'
        ]
        
        md2_fixtures = [
            'Czechia vs South Africa', 'Mexico vs South Korea', 'Switzerland vs Bosnia & Herzegovina',
            'Canada vs Qatar', 'Scotland vs Morocco', 'Brazil vs Haiti', 'USA vs Australia',
            'Turkey vs Paraguay', 'Germany vs Ivory Coast', 'Ecuador vs Curacao',
            'Netherlands vs Sweden', 'Tunisia vs Japan', 'Belgium vs Iran',
            'New Zealand vs Egypt', 'Spain vs Saudi Arabia', 'Uruguay vs Cape Verde',
            'France vs Iraq', 'Norway vs Senegal', 'Argentina vs Austria',
            'Jordan vs Algeria', 'Portugal vs Uzbekistan', 'Colombia vs DR Congo',
            'England vs Ghana', 'Panama vs Croatia'
        ]
        
        md3_fixtures = [
            'Czechia vs Mexico', 'South Africa vs South Korea', 'Switzerland vs Canada',
            'Bosnia & Herzegovina vs Qatar', 'Scotland vs Brazil', 'Morocco vs Haiti',
            'Turkey vs USA', 'Paraguay vs Australia', 'Ecuador vs Germany',
            'Curacao vs Ivory Coast', 'Japan vs Sweden', 'Tunisia vs Netherlands',
            'Egypt vs Iran', 'New Zealand vs Belgium', 'Cape Verde vs Saudi Arabia',
            'Uruguay vs Spain', 'Norway vs France', 'Senegal vs Iraq',
            'Algeria vs Austria', 'Jordan vs Argentina', 'Colombia vs Portugal',
            'DR Congo vs Uzbekistan', 'Panama vs England', 'Croatia vs Ghana'
        ]
        
        if match_key in md1_fixtures:
            return 'group', 1
        elif match_key in md2_fixtures:
            return 'group', 2
        elif match_key in md3_fixtures:
            return 'group', 3
        else:
            # Assume knockout if not found in group stage
            return 'knockout', None