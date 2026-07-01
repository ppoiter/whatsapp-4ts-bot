import re
from config.settings import FIFA_RANK, GROUP_TOP_SEEDS

class WCScoringService:
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service
        self._leaderboard_cache = None
        self._cached_result_count = -1

    def invalidate_cache(self):
        self._leaderboard_cache = None
        self._cached_result_count = -1

    def strip_rank(self, team_name):
        """Strip ranking suffix from team names, e.g. 'England (#4)' -> 'England'"""
        return re.sub(r' \(#\d+\)', '', team_name.strip())

    def calculate_leaderboard(self):
        """Calculate current leaderboard based on available results"""
        try:
            all_results = self.sheets_service.get_all_results()
            total_results = len(all_results)

            if self._leaderboard_cache is not None and total_results == self._cached_result_count:
                return self._leaderboard_cache

            all_picks = self.sheets_service.get_all_picks()
            all_bonus = self.sheets_service.get_all_bonus_awards()
            group_winners = self.sheets_service.get_group_winners()

            if not all_picks:
                return "No picks found yet."

            # Calculate scores for each player
            player_scores = {}

            for normalized_name, player_data in all_picks.items():
                display_name = player_data['display_name']
                total_score = 0

                # Score group stage matches from Forms 1, 2, 3
                for form_num in [1, 2, 3]:
                    if form_num in player_data['forms']:
                        form_picks = player_data['forms'][form_num]['picks']
                        total_score += self._score_group_stage_picks(form_picks, all_results, form_num)

                # Score group winner picks from Form 4
                if 4 in player_data['forms']:
                    total_score += self._score_group_winner_picks(
                        player_data['forms'][4]['picks'], group_winners
                    )

                # Score R32 picks from Forms 5 & 6
                for form_num in [5, 6]:
                    if form_num in player_data['forms']:
                        total_score += self._score_r32_picks(
                            player_data['forms'][form_num]['picks'], all_results
                        )

                # Add bonus points
                for bonus_award in all_bonus:
                    if self.sheets_service.normalize_name(bonus_award.get('player', '')) == normalized_name:
                        total_score += bonus_award.get('points', 0)

                player_scores[display_name] = total_score

            # Sort by score (descending)
            sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)

            latest_result = all_results[-1] if all_results else None
            result = self._format_leaderboard(sorted_players, total_results, latest_result)

            self._leaderboard_cache = result
            self._cached_result_count = total_results
            return result

        except Exception as e:
            print(f"Error calculating leaderboard: {e}")
            return f"❌ Error calculating leaderboard: {str(e)}"
    
    def _score_group_stage_picks(self, form_picks, all_results, form_num):
        """Score group stage match predictions"""
        total_points = 0
        
        # Get matchday for this form
        if form_num == 1:
            target_matchday = 1
        elif form_num == 2:
            target_matchday = 2
        elif form_num == 3:
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
                    
                    # Get team names from match_key
                    teams = match_key.split(' vs ')
                    home_team = teams[0] if len(teams) == 2 else ''
                    away_team = teams[1] if len(teams) == 2 else ''
                    
                    # Determine correct prediction format
                    if home_score > away_score:
                        correct_pick = home_team
                    elif away_score > home_score:
                        correct_pick = away_team
                    else:
                        correct_pick = 'Draw'
                    
                    # Award points for correct prediction
                    if pick == correct_pick:
                        total_points += 1
                    
                    break
        
        return total_points
    
    def _score_group_winner_picks(self, form_picks, group_winners):
        """Score group winner predictions from Form 4. 1pt for top seed, 3pt for upset."""
        total_points = 0
        for column_name, pick in form_picks.items():
            match = re.match(r'Group ([A-L]) Winner', column_name, re.IGNORECASE)
            if not match or not pick:
                continue
            group = match.group(1).upper()
            actual_winner = group_winners.get(group)
            if not actual_winner:
                continue
            if self.strip_rank(pick) == actual_winner:
                points = 1 if actual_winner == GROUP_TOP_SEEDS.get(group) else 3
                total_points += points
        return total_points

    def _score_r32_picks(self, form_picks, all_results):
        """Score Round of 32 predictions. 1pt per correct pick."""
        total_points = 0
        knockout_results = {
            r['match_key']: r for r in all_results if r.get('stage') == 'knockout'
        }
        for column_name, pick in form_picks.items():
            if ' vs ' not in column_name or not pick:
                continue
            result = knockout_results.get(column_name)
            if not result:
                continue
            home_score = result.get('home_score', 0)
            away_score = result.get('away_score', 0)
            teams = column_name.split(' vs ')
            if home_score > away_score:
                correct_pick = teams[0]
            elif away_score > home_score:
                correct_pick = teams[1]
            else:
                correct_pick = 'Draw'
            if pick == correct_pick:
                total_points += 1
        return total_points
    
    def _format_leaderboard(self, sorted_players, total_results, latest_result=None):
        """Format leaderboard for WhatsApp display"""
        if not sorted_players:
            return "No players found."

        message = f"🏆 WC 2026 LEADERBOARD\n"

        if latest_result:
            match_key = latest_result.get('match_key', '')
            h = latest_result.get('home_score', '')
            a = latest_result.get('away_score', '')
            md = latest_result.get('matchday', '')
            md_text = f" (MD{md})" if md else ""
            message += f"Last: {match_key} {h}-{a}{md_text}\n"

        message += "=" * 25 + "\n\n"

        for i, (player_name, score) in enumerate(sorted_players, 1):
            if isinstance(score, float) and score.is_integer():
                score_str = str(int(score))
            else:
                score_str = f"{score:.1f}" if isinstance(score, float) else str(score)

            first_name = player_name.split()[0] if player_name else player_name

            message += f"{i}. {first_name}  —  {score_str} pts\n"

        return message
    
    def get_detailed_scores(self, player_name=None):
        """Get detailed score breakdown for a player or all players"""
        try:
            all_picks = self.sheets_service.get_all_picks()
            all_results = self.sheets_service.get_all_results()
            all_bonus = self.sheets_service.get_all_bonus_awards()
            group_winners = self.sheets_service.get_group_winners()

            if player_name:
                normalized_target = self.sheets_service.normalize_name(player_name)
                if normalized_target not in all_picks:
                    return f"Player '{player_name}' not found."
                return self._get_player_breakdown(
                    all_picks[normalized_target], all_results, all_bonus, group_winners, normalized_target
                )
            else:
                return self.calculate_leaderboard()

        except Exception as e:
            print(f"Error getting detailed scores: {e}")
            return f"❌ Error getting scores: {str(e)}"

    def _get_player_breakdown(self, player_data, all_results, all_bonus, group_winners, normalized_name):
        """Get detailed score breakdown for a specific player"""
        display_name = player_data['display_name']
        message = f"📊 DETAILED SCORES - {display_name.upper()}\n"
        message += "=" * 25 + "\n\n"

        total_score = 0

        for form_num in [1, 2, 3]:
            if form_num in player_data['forms']:
                form_picks = player_data['forms'][form_num]['picks']
                form_score = self._score_group_stage_picks(form_picks, all_results, form_num)
                total_score += form_score
                message += f"📋 MD{form_num} picks: {form_score} pts\n"

        if 4 in player_data['forms']:
            gw_score = self._score_group_winner_picks(player_data['forms'][4]['picks'], group_winners)
            total_score += gw_score
            message += f"🏅 Group winners: {gw_score} pts\n"

        r32_score = 0
        if 5 in player_data['forms'] or 6 in player_data['forms']:
            for form_num in [5, 6]:
                if form_num in player_data['forms']:
                    r32_score += self._score_r32_picks(player_data['forms'][form_num]['picks'], all_results)
            message += f"⚽ R32 picks: {r32_score} pts\n"
        else:
            message += f"⚽ R32 picks: form not found\n"

        total_score += r32_score
        bonus_total = 0
        bonus_details = []
        for bonus_award in all_bonus:
            if self.sheets_service.normalize_name(bonus_award.get('player', '')) == normalized_name:
                points = bonus_award.get('points', 0)
                form = bonus_award.get('form', '')
                bonus_total += points
                bonus_details.append(f"Form {form}")

        if bonus_total > 0:
            message += f"🎯 Bonus: {bonus_total} pts ({', '.join(bonus_details)})\n"

        total_score += bonus_total
        message += f"\n🏆 TOTAL: {total_score} pts"

        return message