import re

def parse_player_picks(message_body):
    """Parse player names from WhatsApp message"""
    lines = message_body.strip().split('\n')
    players = []
    
    for line in lines:
        cleaned = line.strip()
        if cleaned and not re.match(r'^\d+$', cleaned):
            players.append(cleaned)
    
    return players

def send_instructions(current_gameweek, deadline_str):
    """Generate welcome/instructions message"""
    return (
        f"⚽ Welcome to the 4 To Score Picks Bot ⚽\n"
        f"📝 To submit picks for Gameweek {current_gameweek}:\n"
        f"Send 4 player names, one per line:\n\n"
        f"Example:\n"
        f"Haaland\n"
        f"Salah\n"
        f"Saka\n"
        f"Palmer\n\n"
        f"⏰ Deadline: {deadline_str}\n"
        f"✅ You can update picks by sending new ones\n"
    )