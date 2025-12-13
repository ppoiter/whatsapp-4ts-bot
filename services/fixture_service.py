from services.sheets_service import SheetsService
from datetime import datetime

class FixtureService:
    def __init__(self):
        self.sheets_service = SheetsService()
    
    def get_fixtures_for_gameweek(self, gameweek_num):
        """Get all fixtures for a specific gameweek"""
        try:
            sheet = self.sheets_service.get_google_sheet()
            if not sheet:
                return []
            
            # Get or create Fixtures worksheet
            try:
                fixtures_sheet = sheet.spreadsheet.worksheet("Fixtures")
            except:
                return []
            
            all_records = fixtures_sheet.get_all_records()
            gameweek_fixtures = []
            
            for record in all_records:
                if str(record.get('Gameweek')) == str(gameweek_num):
                    fixture = {
                        'gameweek': record.get('Gameweek'),
                        'date': record.get('Date'),
                        'time': record.get('Time'),
                        'home_team': record.get('Home Team'),
                        'away_team': record.get('Away Team'),
                        'status': record.get('Status', 'Scheduled')
                    }
                    gameweek_fixtures.append(fixture)
            
            # Sort by date and time
            gameweek_fixtures.sort(key=lambda x: f"{x['date']} {x['time']}")
            return gameweek_fixtures
            
        except Exception as e:
            print(f"Error getting fixtures: {e}")
            return []
    
    def format_fixtures_message(self, gameweek_num):
        """Format fixtures for WhatsApp message"""
        fixtures = self.get_fixtures_for_gameweek(gameweek_num)
        
        if not fixtures:
            return f"📅 No fixtures found for Gameweek {gameweek_num}"
        
        message = f"📅 GAMEWEEK {gameweek_num} FIXTURES\n"
        message += "=" * 25 + "\n\n"
        
        current_date = ""
        for fixture in fixtures:
            # Group by date
            fixture_date = fixture['date']
            if fixture_date != current_date:
                current_date = fixture_date
                # Format date nicely
                try:
                    date_obj = datetime.strptime(fixture_date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %d %B')
                    message += f"🗓️ {formatted_date}\n"
                except:
                    message += f"🗓️ {fixture_date}\n"
            
            # Add fixture
            time = fixture['time']
            home = fixture['home_team']
            away = fixture['away_team']
            status = fixture['status']
            
            status_emoji = {
                'Scheduled': '⏰',
                'Live': '🔴',
                'Completed': '✅'
            }.get(status, '⏰')
            
            message += f"{status_emoji} {time} - {home} vs {away}\n"
        
        return message
    
    def setup_fixtures_sheet(self):
        """Set up the Fixtures sheet with headers (run once)"""
        try:
            sheet = self.sheets_service.get_google_sheet()
            if not sheet:
                return False, "Could not connect to Google Sheets"
            
            # Create Fixtures worksheet if it doesn't exist
            try:
                fixtures_sheet = sheet.spreadsheet.worksheet("Fixtures")
                print("Fixtures sheet already exists")
                return True, "Fixtures sheet already exists"
            except:
                # Create the sheet
                fixtures_sheet = sheet.spreadsheet.add_worksheet(title="Fixtures", rows=500, cols=10)
                headers = ['Gameweek', 'Date', 'Time', 'Home Team', 'Away Team', 'Status']
                fixtures_sheet.insert_row(headers, 1)
                print("Created Fixtures sheet with headers")
                return True, "Created Fixtures sheet with headers"
                
        except Exception as e:
            print(f"Error setting up fixtures sheet: {e}")
            return False, str(e)
    
    def add_fixture(self, gameweek_num, date, time, home_team, away_team, status='Scheduled'):
        """Add a single fixture to the sheet"""
        try:
            sheet = self.sheets_service.get_google_sheet()
            if not sheet:
                return False, "Could not connect to Google Sheets"
            
            # Get Fixtures worksheet
            try:
                fixtures_sheet = sheet.spreadsheet.worksheet("Fixtures")
            except:
                # Create sheet if it doesn't exist
                setup_success, setup_msg = self.setup_fixtures_sheet()
                if not setup_success:
                    return False, setup_msg
                fixtures_sheet = sheet.spreadsheet.worksheet("Fixtures")
            
            # Add fixture
            fixture_data = [gameweek_num, date, time, home_team, away_team, status]
            fixtures_sheet.append_row(fixture_data)
            
            return True, f"Added fixture: {home_team} vs {away_team}"
            
        except Exception as e:
            print(f"Error adding fixture: {e}")
            return False, str(e)