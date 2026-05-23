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
        if message_lower.startswith('1 ') or message_lower.startswith('0 ') or message_lower.startswith('goal '):
            if message_lower.startswith('1 '):
                # Player scored - preserve original case
                player = message_original[2:].strip()  # Skip "1 "
                scored = True
            elif message_lower.startswith('goal '):
                # Player scored - preserve original case
                player = message_original[5:].strip()  # Skip "goal "
                scored = True
            else:
                # Player didn't score - preserve original case
                player = message_original[2:].strip()  # Skip "0 "
                scored = False
            
            if player:
                success, msg = self.sheets_service.update_player_scored_status(gameweek_num, player, scored)
                if success:
                    # Use title case for display
                    player_display = player.title()
                    goal_msg = f"✅ {player_display}: {'GOAL! ⚽' if scored else 'No goal'}\n\n"
                    
                    # Auto-generate leaderboard after goal updates
                    if scored:
                        leaderboard = self._generate_leaderboard(gameweek_num, detailed=False)
                        return goal_msg + leaderboard
                    else:
                        return goal_msg.strip()
                else:
                    return f"❌ Error updating {player}"
            else:
                return "Please specify a player name"
        
        # Eliminate command
        elif message_lower.startswith('eliminate '):
            user_name = message_original[10:].strip()  # Skip "eliminate "
            if user_name:
                success, msg = self.sheets_service.eliminate_user(user_name, gameweek_num)
                if success:
                    return f"❌ {msg}"
                else:
                    return f"⚠️ {msg}"
            else:
                return "Please specify a user name (e.g., 'eliminate Aubrey')"
        
        # Reinstate command
        elif message_lower.startswith('reinstate '):
            user_name = message_original[10:].strip()  # Skip "reinstate "
            if user_name:
                success, msg = self.sheets_service.reinstate_user(user_name, gameweek_num)
                if success:
                    return f"✅ {msg}"
                else:
                    return f"⚠️ {msg}"
            else:
                return "Please specify a user name (e.g., 'reinstate Peter')"
        
        # Show unique picks command
        elif message_lower in ['show unique', 'unique', 'unique picks', 'show unique picks']:
            return self._show_unique_picks(gameweek_num)
        
        # Help command for admin
        elif message_lower in ['help', 'commands']:
            return ("📋 ADMIN COMMANDS:\n"
                    "• goal [player name] - Mark player as scored\n"
                    "• 0 [player name] - Mark player as didn't score\n" 
                    "• eliminate [user] - Manually eliminate user\n"
                    "• reinstate [user] - Reinstate eliminated user\n"
                    "• leaderboard - Show simple leaderboard\n"
                    "• leaderboard detail - Show detailed leaderboard\n"
                    "• show active - Show win/lose status\n"
                    "• show scorers - List all players who scored\n"
                    "• show unique - Show unique picks (1 picker only)\n"
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
        
        # Leaderboard commands
        elif message_lower in ['leaderboard', 'leaderboard detail']:
            detailed = 'detail' in message_lower
            return self._generate_leaderboard(gameweek_num, detailed)
        
        # Check for status request
        elif message_lower in ['show active', 'active', 'whos in', 'who is in', 'status', 'show status']:
            results = self.sheets_service.get_user_status_from_sheet(gameweek_num)
            
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
    
    def _generate_leaderboard(self, gameweek_num, detailed=False):
        """Generate leaderboard with weighted scoring"""
        try:
            # Get all picks for this gameweek
            all_picks = self.sheets_service.get_all_picks_for_gameweek(gameweek_num)
            if not all_picks:
                return "No picks found for this gameweek."
            
            # Get scoring data
            sheet = self.sheets_service.get_google_sheet()
            if not sheet:
                return "❌ Could not connect to sheet"
            
            try:
                scores_sheet = sheet.spreadsheet.worksheet("Player Scores")
                scores_records = scores_sheet.get_all_records()
            except:
                return "No scoring data recorded yet."
            
            # Build scorer data with goal counts
            scorer_goals = {}
            for record in scores_records:
                if str(record.get('Gameweek')) == str(gameweek_num):
                    player = record.get('Player', '').strip().title()
                    scored = record.get('Scored', '').strip().lower() == 'yes'
                    if scored:
                        # For now, assume 1 goal per scored player (can be extended later)
                        scorer_goals[player] = 1
            
            # Calculate scores for each user
            user_scores = []
            for phone, pick_data in all_picks.items():
                user_name = pick_data['user_name']
                players = pick_data['players']
                
                total_score = 0
                player_breakdown = []
                
                for player in players:
                    player_normalized = player.strip().title()
                    goals = scorer_goals.get(player_normalized, 0)
                    
                    if goals > 0:
                        # Calculate how many other users picked this player
                        other_pickers = sum(1 for other_phone, other_pick in all_picks.items() 
                                          if other_phone != phone and 
                                          any(p.strip().title() == player_normalized for p in other_pick['players']))
                        
                        # Apply weighted scoring formula
                        multiplier = max(0.1, 1 - 0.1 * other_pickers)
                        points = goals * multiplier
                        total_score += points
                        
                        player_breakdown.append({
                            'player': player_normalized,
                            'goals': goals,
                            'multiplier': multiplier,
                            'points': points
                        })
                
                user_scores.append({
                    'name': user_name,
                    'total_score': total_score,
                    'breakdown': player_breakdown
                })
            
            # Sort by total score (descending)
            user_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Generate leaderboard message
            if detailed:
                return self._format_detailed_leaderboard(gameweek_num, user_scores)
            else:
                return self._format_simple_leaderboard(gameweek_num, user_scores)
                
        except Exception as e:
            return f"❌ Error generating leaderboard: {str(e)}"
    
    def _format_simple_leaderboard(self, gameweek_num, user_scores):
        """Format simple leaderboard view"""
        message = f"🏆 LEADERBOARD\n\n"
        
        for i, user_score in enumerate(user_scores, 1):
            score_str = f"{user_score['total_score']:.1f}" if user_score['total_score'] > 0 else "0.0"
            message += f"{i}. {user_score['name']} — {score_str} pts\n"
        
        return message
    
    def _format_detailed_leaderboard(self, gameweek_num, user_scores):
        """Format detailed leaderboard view"""
        message = f"🏆 LEADERBOARD (DETAILED)\n\n"
        
        for i, user_score in enumerate(user_scores, 1):
            score_str = f"{user_score['total_score']:.1f}" if user_score['total_score'] > 0 else "0.0"
            message += f"{i}. {user_score['name']} — {score_str} pts\n"
            
            for breakdown in user_score['breakdown']:
                message += f"   ⚽ {breakdown['player']} ({breakdown['goals']}g × {breakdown['multiplier']:.1f}) = {breakdown['points']:.1f}\n"
            
            if not user_score['breakdown']:
                message += "   No scorers yet\n"
            
            message += "\n"
        
        return message
    
    def get_player_weightings(self, gameweek_num):
        """Show weightings for all picked players, sorted by weight (ascending)"""
        try:
            # Get all picks for this gameweek
            all_picks = self.sheets_service.get_all_picks_for_gameweek(gameweek_num)
            if not all_picks:
                return "No picks found for this gameweek."
            
            # Count how many times each player was picked and track who picked them
            player_pick_data = {}
            total_pickers = len(all_picks)
            
            for phone, pick_data in all_picks.items():
                user_name = pick_data['user_name']
                players = pick_data['players']
                for player in players:
                    player_normalized = player.strip().title()
                    if player_normalized:
                        if player_normalized not in player_pick_data:
                            player_pick_data[player_normalized] = {
                                'count': 0,
                                'pickers': []
                            }
                        player_pick_data[player_normalized]['count'] += 1
                        player_pick_data[player_normalized]['pickers'].append(user_name)
            
            if not player_pick_data:
                return "No players have been picked yet."
            
            # Calculate weightings for each player
            player_weightings = []
            for player, data in player_pick_data.items():
                pick_count = data['count']
                pickers = data['pickers']
                
                # Skip players with only 1 pick
                if pick_count == 1:
                    continue
                    
                # For weighting calculation, we use other_pickers (exclude the current picker)
                # Since we want to show the weight any individual picker would get
                other_pickers = pick_count - 1  # Subtract 1 for the picker themselves
                weight = max(0.1, 1 - 0.1 * other_pickers)
                player_weightings.append({
                    'player': player,
                    'pick_count': pick_count,
                    'weight': weight,
                    'pickers': pickers
                })
            
            # Sort by weight (ascending - least popular first)
            player_weightings.sort(key=lambda x: x['weight'])
            
            # Build the message
            message = f"📊 PLAYER WEIGHTINGS (GW{gameweek_num})\n"
            message += "=" * 30 + "\n\n"
            
            for item in player_weightings:
                weight = item['weight']
                player = item['player']
                pickers = ', '.join(item['pickers'])
                
                message += f"{weight:.1f} — *{player}* ({pickers})\n"
            
            return message
                
        except Exception as e:
            return f"❌ Error getting player weightings: {str(e)}"
    
    def _show_unique_picks(self, gameweek_num):
        """Show players that were picked by only one person"""
        try:
            # Get all picks for this gameweek
            all_picks = self.sheets_service.get_all_picks_for_gameweek(gameweek_num)
            if not all_picks:
                return "No picks found for this gameweek."
            
            # Count how many times each player was picked and track who picked them
            player_pick_data = {}
            
            for phone, pick_data in all_picks.items():
                user_name = pick_data['user_name']
                players = pick_data['players']
                for player in players:
                    player_normalized = player.strip().title()
                    if player_normalized:
                        if player_normalized not in player_pick_data:
                            player_pick_data[player_normalized] = {
                                'count': 0,
                                'pickers': []
                            }
                        player_pick_data[player_normalized]['count'] += 1
                        player_pick_data[player_normalized]['pickers'].append(user_name)
            
            if not player_pick_data:
                return "No players have been picked yet."
            
            # Filter for unique picks (count == 1)
            unique_picks = []
            for player, data in player_pick_data.items():
                if data['count'] == 1:
                    unique_picks.append({
                        'player': player,
                        'picker': data['pickers'][0]  # Only one picker
                    })
            
            if not unique_picks:
                return f"🔍 No unique picks found for Gameweek {gameweek_num}.\nAll players were picked by multiple people."
            
            # Sort by player name
            unique_picks.sort(key=lambda x: x['player'])
            
            # Build the message
            message = f"🎯 UNIQUE PICKS (GW{gameweek_num})\n"
            message += "=" * 25 + "\n\n"
            
            for item in unique_picks:
                player = item['player']
                picker = item['picker']
                message += f"*{player}* — {picker}\n"
            
            return message
            
        except Exception as e:
            return f"❌ Error getting unique picks: {str(e)}"