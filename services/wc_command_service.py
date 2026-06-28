import re
from fuzzywuzzy import fuzz
from config.settings import ADMIN_PHONE, TEAM_ABBREVIATIONS, FIFA_RANK
from services.wc_scoring_service import WCScoringService

class WCCommandService:
    def __init__(self, sheets_service, twilio_client):
        self.sheets_service = sheets_service
        self.twilio_client = twilio_client
        self.scoring_service = WCScoringService(sheets_service)
    
    def handle_command(self, message_body, from_number):
        """Handle WC commands from WhatsApp"""
        try:
            # Remove 'wc ' prefix and normalize
            command = message_body[3:].strip().lower()
            original_command = message_body[3:].strip()
            
            # Leaderboard command
            if command in ['leaderboard', 'standings', 'scores', 'table']:
                return self.scoring_service.calculate_leaderboard()

            # Detailed scores command (open to all)
            if command.startswith('scores '):
                player_name = original_command[7:].strip()
                return self.scoring_service.get_detailed_scores(player_name)

            # Help command
            if command in ['help', 'commands']:
                return self._get_help_text()

            # Admin-only commands
            if from_number != ADMIN_PHONE:
                return "⛔ Only the admin can enter results and award bonus points."

            # Result entry command
            if command.startswith('result '):
                return self._handle_result_command(original_command[7:])

            # Group winner command
            if command.startswith('winner '):
                return self._handle_group_winner_command(original_command[7:])

            # Bonus points command
            if command.startswith('bonus '):
                return self._handle_bonus_command(original_command[6:])
            
            return "❌ Unknown command. Type 'wc help' for available commands."
            
        except Exception as e:
            print(f"Error handling command: {e}")
            return f"❌ Error processing command: {str(e)}"
    
    def _handle_result_command(self, result_text):
        """Handle result entry: wc result ENG 2-1 CRO"""
        try:
            # Parse result text
            # Expected format: TEAM1 SCORE TEAM2 or TEAM1 SCORE-SCORE TEAM2
            parts = result_text.strip().split()
            
            if len(parts) < 3:
                return "❌ Invalid format. Use: wc result TEAM1 2-1 TEAM2"
            
            # Try different parsing patterns
            if '-' in parts[1]:
                # Format: ENG 2-1 CRO
                team1_input = parts[0]
                score_part = parts[1]
                team2_input = ' '.join(parts[2:])
                
                scores = score_part.split('-')
                if len(scores) != 2:
                    return "❌ Invalid score format. Use format like 2-1"
                
                try:
                    home_score = int(scores[0])
                    away_score = int(scores[1])
                except ValueError:
                    return "❌ Scores must be numbers"
                    
            else:
                return "❌ Invalid format. Use: wc result TEAM1 2-1 TEAM2"
            
            # Parse team names
            home_team = self._parse_team_name(team1_input)
            away_team = self._parse_team_name(team2_input)
            
            if not home_team:
                return f"❌ Could not recognize team: {team1_input}"
            if not away_team:
                return f"❌ Could not recognize team: {team2_input}"
            
            # Create match key
            match_key = f"{home_team} vs {away_team}"
            
            # Determine stage and matchday
            stage, matchday = self.sheets_service.determine_match_stage_and_matchday(match_key)
            
            # Log result
            success, message = self.sheets_service.log_result(
                match_key, home_score, away_score, stage, matchday
            )
            
            if success:
                self.scoring_service.invalidate_cache()

                if stage == 'group' and matchday:
                    stage_text = f"Group Stage, MD{matchday}"
                else:
                    stage_text = stage.title()

                return f"✅ {home_team} {home_score}-{away_score} {away_team} logged ({stage_text})"
            else:
                return f"❌ Error logging result: {message}"
                
        except Exception as e:
            print(f"Error handling result command: {e}")
            return f"❌ Error processing result: {str(e)}"
    
    def _handle_bonus_command(self, bonus_text):
        """Handle bonus points: wc bonus 2 Peter Dave"""
        try:
            parts = bonus_text.strip().split()
            
            if len(parts) < 2:
                return "❌ Invalid format. Use: wc bonus [FORM_NUM] [PLAYER_NAMES]"
            
            try:
                form_num = int(parts[0])
            except ValueError:
                return "❌ Form number must be a number (1-4)"
            
            if form_num not in [1, 2, 3, 4]:
                return "❌ Form number must be 1, 2, 3, or 4"
            
            player_names = parts[1:]
            if not player_names:
                return "❌ Please specify at least one player name"
            
            # Award bonus points
            success, message = self.sheets_service.award_bonus_points(form_num, player_names)
            
            if success:
                self.scoring_service.invalidate_cache()
                return f"✅ Bonus (Form {form_num}): 2pts awarded to {message.split(': ')[1]}"
            else:
                return f"❌ Error awarding bonus: {message}"
                
        except Exception as e:
            print(f"Error handling bonus command: {e}")
            return f"❌ Error processing bonus: {str(e)}"
    
    def _handle_group_winner_command(self, text):
        """Handle group winner entry: wc winner A England"""
        parts = text.strip().split(None, 1)
        if len(parts) < 2:
            return "❌ Format: wc winner A England"

        group = parts[0].upper()
        if len(group) != 1 or group not in 'ABCDEFGHIJKL':
            return "❌ Group must be A–L"

        team = self._parse_team_name(parts[1].strip())
        if not team:
            return f"❌ Could not recognise team: {parts[1]}"

        success, message = self.sheets_service.log_group_winner(group, team)
        if success:
            self.scoring_service.invalidate_cache()
            return f"✅ Group {group} winner: {team}"
        return f"❌ Error: {message}"

    def _parse_team_name(self, team_input):
        """Parse team name from input (abbreviation or full name)"""
        team_input = team_input.strip()
        
        # Check exact abbreviation match
        if team_input.upper() in TEAM_ABBREVIATIONS:
            return TEAM_ABBREVIATIONS[team_input.upper()]
        
        # Check exact full name match
        for team_name in FIFA_RANK.keys():
            if team_input.lower() == team_name.lower():
                return team_name
        
        # Fuzzy matching for full names
        best_match = None
        best_score = 0
        
        for team_name in FIFA_RANK.keys():
            score = fuzz.ratio(team_input.lower(), team_name.lower())
            if score > best_score and score >= 70:  # 70% similarity threshold
                best_score = score
                best_match = team_name
        
        return best_match
    
    def _get_help_text(self):
        """Return help text for commands"""
        return (
            "🏆 WORLD CUP 2026 BOT COMMANDS\n\n"
            "📊 FOR EVERYONE:\n"
            "• wc leaderboard - Show current standings\n\n"
            "⚙️ ADMIN ONLY:\n"
            "• wc result [TEAM1] [SCORE] [TEAM2]\n"
            "  Example: wc result ENG 2-1 CRO\n\n"
            "• wc bonus [FORM] [PLAYERS]\n"
            "  Example: wc bonus 2 Peter Dave\n\n"
            "• wc scores [PLAYER] - Detailed breakdown\n"
            "• wc help - Show this help\n\n"
            "Team abbreviations: ENG, FRA, GER, ESP, etc."
        )