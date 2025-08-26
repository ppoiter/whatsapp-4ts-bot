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
                success, msg = self.sheets_service.update_player_scored_status(gameweek_num, player, scored)
                if success:
                    return f"✅ {player}: {'GOAL! ⚽' if scored else 'No goal'}"
                else:
                    return f"❌ Error updating {player}"
            else:
                return "Please specify a player name"
        
        # Check for active status request
        elif message_lower in ['show active', 'active', 'whos in', 'who is in']:
            results = self.sheets_service.get_elimination_status(gameweek_num)
            
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
                
                return message
            else:
                return "Error getting elimination status"
        
        return None