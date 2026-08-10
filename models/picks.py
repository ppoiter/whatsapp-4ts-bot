from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class PlayerPick:
    """Represents a player pick submission"""
    phone_number: str
    user_name: str
    gameweek: int
    players: List[str]
    timestamp: datetime
    deadline: datetime

    def is_valid(self) -> bool:
        """Check if the pick has exactly 4 players"""
        return len(self.players) == 4

    def to_sheet_row(self) -> List[str]:
        """Convert to Google Sheets row format"""
        return [
            self.timestamp.isoformat(),
            self.phone_number,
            self.user_name,
            self.gameweek,
            self.deadline.strftime("%Y-%m-%d %H:%M"),
            self.players[0] if len(self.players) > 0 else '',
            self.players[1] if len(self.players) > 1 else '',
            self.players[2] if len(self.players) > 2 else '',
            self.players[3] if len(self.players) > 3 else '',
        ]

@dataclass
class PlayerScore:
    """Represents a player's scoring status for a gameweek"""
    gameweek: int
    player_name: str
    scored: bool
    updated: datetime