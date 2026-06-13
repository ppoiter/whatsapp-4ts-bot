import re
from config.settings import FIFA_RANK

class WCScoringService:
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service
    
    def strip_rank(self, team_name):
        """Strip ranking suffix from team names, e.g. 'England (#4)' -> 'England'"""
        return re.sub(r' \(#\d+\)', '', team_name.strip())
    
    def calculate_leaderboard(self):
        """Calculate current leaderboard based on available results"""
        try:
            # Get all data
            all_picks = self.sheets_service.get_all_picks()
            all_results = self.sheets_service.get_all_results()
            all_bonus = self.sheets_service.get_all_bonus_awards()
            
            if not all_picks:
                return "No picks found yet."
            
            # Calculate scores for each player
            player_scores = {}
            total_results = len(all_results)
            
            for normalized_name, player_data in all_picks.items():
                display_name = player_data['display_name']
                total_score = 0
                
                # Score group stage matches from Forms 2, 3, 4
                for form_num in [2, 3, 4]:
                    if form_num in player_data['forms']:
                        form_picks = player_data['forms'][form_num]['picks']
                        total_score += self._score_group_stage_picks(form_picks, all_results, form_num)
                
                # Add bonus points
                for bonus_award in all_bonus:
                    if self.sheets_service.normalize_name(bonus_award.get('player', '')) == normalized_name:
                        total_score += bonus_award.get('points', 0)
                
                player_scores[display_name] = total_score
            
            # Sort by score (descending)
            sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Format leaderboard
            return self._format_leaderboard(sorted_players, total_results)
            
        except Exception as e:
            print(f"Error calculating leaderboard: {e}")
            return f"❌ Error calculating leaderboard: {str(e)}"
    
    def _score_group_stage_picks(self, form_picks, all_results, form_num):
        """Score group stage match predictions"""
        total_points = 0
        
        # Get matchday for this form
        if form_num == 2:
            target_matchday = 1
        elif form_num == 3:
            target_matchday = 2
        elif form_num == 4:
            target_matchday = 3
        else:
            return 0
        
        # Check each match prediction
        for column_name, pick in form_picks.items():
            if ' vs ' not in column_name or column_name in ['Timestamp', 'Your name']:
                continue
                
            # Extract teams from column name (remove rankings)
            match_key = self.strip_rank(column_name)
            
            # Find corresponding result
            for result in all_results:
                if result.get('match_key') == match_key and result.get('matchday') == target_matchday:
                    # Determine actual result
                    home_score = result.get('home_score', 0)
                    away_score = result.get('away_score', 0)
                    
                    if home_score > away_score:
                        actual_result = 'Home'
                    elif away_score > home_score:
                        actual_result = 'Away'
                    else:
                        actual_result = 'Draw'
                    
                    # Award points for correct prediction
                    if pick == actual_result:
                        total_points += 1
                    
                    break
        
        return total_points
    
    def _score_knockout_picks(self, form_picks, all_results, stage):
        """Score knockout stage predictions (future implementation)"""
        # Placeholder for knockout scoring
        return 0
    
    def _format_leaderboard(self, sorted_players, total_results):
        """Format leaderboard for WhatsApp display"""
        if not sorted_players:
            return "No players found."
        
        # Determine how many group stage matches have been played
        group_matches_total = 72  # 24 matches × 3 matchdays
        progress_text = f"({total_results}/{group_matches_total} group results)"
        
        message = f"🏆 WC 2026 LEADERBOARD {progress_text}\n"
        message += "=" * 30 + "\n\n"
        
        for i, (player_name, score) in enumerate(sorted_players, 1):
            score_str = f"{score:.1f}" if isinstance(score, float) else str(score)
            message += f"{i}. {player_name}  —  {score_str} pts\n"
        
        return message
    
    def get_detailed_scores(self, player_name=None):
        """Get detailed score breakdown for a player or all players"""
        try:
            all_picks = self.sheets_service.get_all_picks()
            all_results = self.sheets_service.get_all_results()
            all_bonus = self.sheets_service.get_all_bonus_awards()
            
            if player_name:
                # Find specific player
                normalized_target = self.sheets_service.normalize_name(player_name)
                if normalized_target not in all_picks:
                    return f"Player '{player_name}' not found."
                
                return self._get_player_breakdown(
                    all_picks[normalized_target], all_results, all_bonus, normalized_target
                )
            else:
                # Return summary for all players
                return self.calculate_leaderboard()
                
        except Exception as e:
            print(f"Error getting detailed scores: {e}")
            return f"❌ Error getting scores: {str(e)}"
    
    def _get_player_breakdown(self, player_data, all_results, all_bonus, normalized_name):
        """Get detailed score breakdown for a specific player"""
        display_name = player_data['display_name']
        message = f"📊 DETAILED SCORES - {display_name.upper()}\n"
        message += "=" * 30 + "\n\n"
        
        total_score = 0
        
        # Group stage scoring
        for form_num in [2, 3, 4]:
            if form_num in player_data['forms']:
                form_picks = player_data['forms'][form_num]['picks']
                form_score = self._score_group_stage_picks(form_picks, all_results, form_num)
                total_score += form_score
                message += f"📋 Form {form_num} (MD{form_num-1}): {form_score} pts\n"
        
        # Bonus points
        bonus_total = 0
        bonus_details = []
        for bonus_award in all_bonus:
            if self.sheets_service.normalize_name(bonus_award.get('player', '')) == normalized_name:
                points = bonus_award.get('points', 0)
                form = bonus_award.get('form', '')
                bonus_total += points
                bonus_details.append(f"Form {form}")
        
        if bonus_total > 0:
            message += f"🎯 Bonus Points: {bonus_total} pts ({', '.join(bonus_details)})\n"
        
        total_score += bonus_total
        message += f"\n🏆 TOTAL: {total_score} pts"
        
        return message