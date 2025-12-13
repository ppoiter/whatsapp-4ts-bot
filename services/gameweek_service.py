from config.settings import USER_MAP
from services.sheets_service import SheetsService
from utils.date_utils import format_deadline

class GameweekService:
    def __init__(self):
        self.sheets_service = SheetsService()
        self.user_map = USER_MAP

    def process_admin_command(self, message_body, gameweek_num):
        """Process admin commands for scoring updates"""
        message_lower = message_body.lower().strip()
        message_original = message_body.strip()
        
        # Check for scoring commands
        if message_lower.startswith('goal ') or message_lower.startswith('no goal '):
            if message_lower.startswith('goal '):
                # Player scored - preserve original case
                player = message_original[5:].strip()  # Skip "goal "
                scored = True
            else:
                # Player didn't score - preserve original case
                player = message_original[8:].strip()  # Skip "no goal "
                scored = False
            
            if player:
                success, msg = self.sheets_service.update_player_scored_status(gameweek_num, player, scored)
                if success:
                    # Use title case for display
                    player_display = player.title()
                    return f"✅ {player_display}: {'GOAL! ⚽' if scored else 'No goal'}"
                else:
                    return f"❌ Error updating {player}"
            else:
                return "Please specify a player name"
        
        # Help command for admin
        elif message_lower in ['help', 'commands']:
            return ("📋 ADMIN COMMANDS:\n"
                    "• goal [player name] - Mark player as scored\n"
                    "• no goal [player name] - Mark player as didn't score\n" 
                    "• show active - Show win/lose status\n"
                    "• show scorers - List all players who scored\n"
                    "• summary/picks - Show all picks\n"
                    "• fixtures - Show fixtures\n\n"
                    "Example: goal Mohamed Salah")
        
        # Show all scorers for the gameweek
        elif message_lower in ['show scorers', 'scorers', 'goals']:
            try:
                sheet = self.sheets_service.get_google_sheet()
                if not sheet:
                    return "❌ Could not connect to sheet"
                
                try:
                    scores_sheet = sheet.spreadsheet.worksheet("Player Scores")
                    scores_records = scores_sheet.get_all_records()
                    
                    scorers = []
                    non_scorers = []
                    
                    for record in scores_records:
                        if str(record.get('Gameweek')) == str(gameweek_num):
                            player = record.get('Player', '').strip()
                            scored = record.get('Scored', '').strip().lower() == 'yes'
                            if scored:
                                scorers.append(player)
                            else:
                                non_scorers.append(player)
                    
                    message = f"⚽ GAMEWEEK {gameweek_num} SCORERS\n"
                    message += "=" * 25 + "\n\n"
                    
                    if scorers:
                        message += "✅ SCORED:\n"
                        for player in sorted(scorers):
                            message += f"  • {player}\n"
                    else:
                        message += "No scorers recorded yet\n"
                    
                    if non_scorers:
                        message += "\n❌ DID NOT SCORE:\n"
                        for player in sorted(non_scorers):
                            message += f"  • {player}\n"
                    
                    return message
                    
                except:
                    return "No scoring data recorded yet. Use 'goal [player]' to add."
                    
            except Exception as e:
                return f"❌ Error getting scorers: {str(e)}"
        
        # Check for status request
        elif message_lower in ['show active', 'active', 'whos in', 'who is in', 'status', 'show status']:
            results = self.sheets_service.get_elimination_status(gameweek_num)
            
            if results:
                message = f"🎯 GAMEWEEK {gameweek_num} STATUS\n"
                message += "=" * 25 + "\n\n"
                
                # Combine all users and sort by name
                all_users = []
                
                # Add winners
                for user_status in results.get('won', []):
                    # Extract just the name and players
                    parts = user_status.split(': ', 1)
                    if len(parts) == 2:
                        name = parts[0]
                        # Remove the emoji indicators from players
                        players = parts[1].replace('✅ ', '').replace('❌ ', '').replace('⏳ ', '')
                        all_users.append((name, players, 'won'))
                
                # Add losers
                for user_status in results.get('lost', []):
                    parts = user_status.split(': ', 1)
                    if len(parts) == 2:
                        name = parts[0]
                        players = parts[1].replace('✅ ', '').replace('❌ ', '').replace('⏳ ', '')
                        if 'No picks submitted' in players:
                            players = 'No picks submitted'
                        all_users.append((name, players, 'lost'))
                
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
                    if status == 'lost':
                        # Using tilde for strikethrough (WhatsApp formatting)
                        message += f"👎 ~{name}: {players}~\n"
                    elif status == 'won':
                        message += f"🏆 {name}: {players}\n"
                    elif status == 'pending':
                        message += f"⏳ {name}: {players}\n"
                    else:
                        message += f"✅ {name}: {players}\n"
                
                return message
            else:
                return "Error getting elimination status"
        
        return None