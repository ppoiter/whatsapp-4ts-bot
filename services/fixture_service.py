import requests
import time
from datetime import datetime

from utils.date_utils import get_uk_timezone

FPL_BASE = "https://fantasy.premierleague.com/api"
FIXTURES_TTL = 3600      # cache fixtures per gameweek for 1 hour
BOOTSTRAP_TTL = 86400    # cache the team id -> name map for 1 day


class FixtureService:
    """Reads Premier League fixtures from the free, key-less Fantasy Premier
    League API. Fixtures are grouped by gameweek ("event"), which maps
    directly onto this bot's gameweek numbering.
    """

    def __init__(self):
        self._teams = None            # {team_id: team_name}
        self._teams_fetched_at = 0.0
        self._fixtures_cache = {}     # {gameweek: (fetched_at, [fixtures])}

    def _get_team_map(self):
        """Fetch and cache the team id -> name map from bootstrap-static."""
        now = time.monotonic()
        if self._teams is not None and (now - self._teams_fetched_at) < BOOTSTRAP_TTL:
            return self._teams

        resp = requests.get(f"{FPL_BASE}/bootstrap-static/", timeout=10)
        resp.raise_for_status()
        teams = resp.json().get('teams', [])
        self._teams = {t['id']: t['name'] for t in teams}
        self._teams_fetched_at = now
        return self._teams

    def get_fixtures_for_gameweek(self, gameweek_num):
        """Return a list of fixture dicts for the given gameweek.

        Results are cached for FIXTURES_TTL seconds. On any API error this
        returns an empty list.
        """
        now = time.monotonic()
        cached = self._fixtures_cache.get(gameweek_num)
        if cached and (now - cached[0]) < FIXTURES_TTL:
            return cached[1]

        try:
            teams = self._get_team_map()
            resp = requests.get(
                f"{FPL_BASE}/fixtures/",
                params={'event': gameweek_num},
                timeout=10,
            )
            resp.raise_for_status()
            raw_fixtures = resp.json()
        except Exception as e:
            print(f"Error fetching fixtures from FPL API: {e}")
            return []

        uk_tz = get_uk_timezone()
        fixtures = []
        for f in raw_fixtures:
            kickoff = f.get('kickoff_time')
            if kickoff:
                # kickoff_time is UTC ISO8601, e.g. "2026-08-21T19:00:00Z"
                dt_uk = datetime.fromisoformat(kickoff.replace('Z', '+00:00')).astimezone(uk_tz)
                date_str = dt_uk.strftime('%Y-%m-%d')
                time_str = dt_uk.strftime('%H:%M')
            else:
                # Fixture scheduled but kickoff not yet confirmed
                date_str = ''
                time_str = 'TBC'

            fixtures.append({
                'gameweek': f.get('event'),
                'date': date_str,
                'time': time_str,
                'home_team': teams.get(f.get('team_h'), '?'),
                'away_team': teams.get(f.get('team_a'), '?'),
                'status': 'Finished' if f.get('finished') else 'Scheduled',
            })

        fixtures.sort(key=lambda x: f"{x['date']} {x['time']}")
        self._fixtures_cache[gameweek_num] = (now, fixtures)
        return fixtures

    def format_fixtures_message(self, gameweek_num):
        """Format fixtures for WhatsApp message"""
        fixtures = self.get_fixtures_for_gameweek(gameweek_num)

        if not fixtures:
            return f"No fixtures found for Gameweek {gameweek_num}"

        message = ""

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
                    message += f"{formatted_date}\n"
                except ValueError:
                    message += f"{fixture_date}\n"

            # Add fixture
            time_str = fixture['time']
            home = fixture['home_team']
            away = fixture['away_team']

            message += f"{time_str} - {home} vs {away}\n"

        return message
