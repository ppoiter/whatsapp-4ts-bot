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

            # Debug R32 scoring
            if command.startswith('debugr32 '):
                return self._debug_r32(original_command[9:])

            # Debug QF scoring
            if command.startswith('debugqf '):
                return self._debug_qf(original_command[8:])
            
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
                return "❌ Form number must be a number"
            
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
    
    def _debug_r32(self, player_name):
        """Debug R32 scoring for a player — form 5 breakdown only"""
        try:
            abbr = {v: k for k, v in TEAM_ABBREVIATIONS.items()}

            def shorten(team):
                return abbr.get(team, team[:3].upper())

            all_picks = self.sheets_service.get_all_picks()
            all_results = self.sheets_service.get_all_results()

            normalized = self.sheets_service.normalize_name(player_name.strip())
            if normalized not in all_picks:
                return f"Player '{player_name}' not found."

            player_data = all_picks[normalized]
            knockout_results = {
                r['match_key']: r for r in all_results if r.get('stage') == 'knockout'
            }

            lines = [f"R32 breakdown ({player_name}):"]
            total_pts = 0

            for form_num in [5, 6]:
                if form_num not in player_data['forms']:
                    lines.append(f"Form {form_num}: not found")
                    continue
                picks = {k: v for k, v in player_data['forms'][form_num]['picks'].items() if ' vs ' in k}
                lines.append(f"— Form {form_num} —")
                for col, pick in picks.items():
                    teams = col.split(' vs ')
                    h_abbr = shorten(teams[0])
                    a_abbr = shorten(teams[1])
                    result = knockout_results.get(col)
                    if not result:
                        lines.append(f"  {h_abbr} vs {a_abbr}: {shorten(pick)} [pending]")
                        continue
                    h = result.get('home_score', 0)
                    a = result.get('away_score', 0)
                    if h > a:
                        correct = teams[0]
                    elif a > h:
                        correct = teams[1]
                    else:
                        correct = 'Draw'
                    got_it = pick == correct
                    if got_it:
                        total_pts += 1
                    tick = '✓' if got_it else '✗'
                    lines.append(f"  {tick} {h_abbr} vs {a_abbr} {h}-{a}: {shorten(pick)} (ans:{shorten(correct)})")

            lines.append(f"Total: {total_pts} pts")
            return "\n".join(lines)
        except Exception as e:
            return f"Debug error: {e}"

    def _debug_qf(self, player_name):
        """Debug QF score-based scoring for a player"""
        try:
            all_picks = self.sheets_service.get_all_picks()
            all_results = self.sheets_service.get_all_results()

            normalized = self.sheets_service.normalize_name(player_name.strip())
            if normalized not in all_picks:
                return f"Player '{player_name}' not found."

            player_data = all_picks[normalized]
            if 8 not in player_data['forms']:
                return f"No form 8 picks found for '{player_name}'."

            knockout_results = {
                r['match_key']: r for r in all_results if r.get('stage') == 'knockout'
            }

            picks = player_data['forms'][8]['picks']
            match_scores = {}
            for col, val in picks.items():
                m = re.match(r'^(.+? vs .+?) \[(.+?)\]\s*$', col)
                if not m or val == '' or val is None:
                    continue
                match_key = m.group(1).strip()
                team = m.group(2).strip()
                if match_key not in match_scores:
                    match_scores[match_key] = {}
                try:
                    match_scores[match_key][team] = int(val)
                except (ValueError, TypeError):
                    pass

            lines = [f"QF breakdown ({player_name}):"]
            total_pts = 0

            for match_key, team_scores in match_scores.items():
                teams = match_key.split(' vs ')
                home_team, away_team = teams[0].strip(), teams[1].strip()
                pred_h = team_scores.get(home_team)
                pred_a = team_scores.get(away_team)
                result = knockout_results.get(match_key)

                if pred_h is None or pred_a is None:
                    lines.append(f"  {match_key}: incomplete pick")
                    continue

                if not result:
                    lines.append(f"  {match_key}: {pred_h}-{pred_a} [pending]")
                    continue

                actual_h = int(result.get('home_score', 0))
                actual_a = int(result.get('away_score', 0))

                if pred_h == actual_h and pred_a == actual_a:
                    pts = 2
                    tick = '✓✓'
                elif (pred_h > pred_a and actual_h > actual_a) or \
                     (pred_a > pred_h and actual_a > actual_h) or \
                     (pred_h == pred_a and actual_h == actual_a):
                    pts = 1
                    tick = '✓'
                else:
                    pts = 0
                    tick = '✗'

                total_pts += pts
                lines.append(f"  {tick} {home_team[:3].upper()} vs {away_team[:3].upper()} {actual_h}-{actual_a}: pick {pred_h}-{pred_a} ({pts}pt)")

            lines.append(f"Total: {total_pts} pts")
            return "\n".join(lines)
        except Exception as e:
            return f"Debug error: {e}"

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