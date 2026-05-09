import re
from .player_names import PLAYER_CORRECTIONS

def correct_player_name(name):
    """Correct common player name misspellings"""
    name_lower = name.strip().lower()
    if name_lower in PLAYER_CORRECTIONS:
        return PLAYER_CORRECTIONS[name_lower]
    return name.strip()

def parse_player_picks(message_body):
    """Parse player names from WhatsApp message with spell correction"""
    lines = message_body.strip().split('\n')
    players = []
    
    for line in lines:
        cleaned = line.strip()
        if cleaned and not re.match(r'^\d+$', cleaned):
            corrected_name = correct_player_name(cleaned)
            players.append(corrected_name)
    
    return players

def send_instructions(current_gameweek, deadline_str):
    """Generate welcome/instructions message"""
    return (
        f"⚽ Welcome to the Final Weekend Picks Bot ⚽\n"
        f"📝 To submit picks for Gameweek {current_gameweek}:\n"
        f"Send 8 player names, one per line:\n\n"
        f"Example:\n"
        f"Haaland\n"
        f"Salah\n"
        f"Saka\n"
        f"Palmer\n"
        f"Watkins\n"
        f"Isak\n"
        f"Son\n"
        f"Wissa\n\n"
        f"⏰ Deadline: {deadline_str}\n"
        f"✅ You can update picks by sending new ones\n"
        f"🏆 Points are weighted by pick popularity!\n"
    )