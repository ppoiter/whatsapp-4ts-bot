import pytz
from datetime import datetime, timedelta
from config.settings import GAMEWEEK_SCHEDULE

def get_uk_timezone():
    """Get UK timezone (handles BST/GMT automatically)"""
    return pytz.timezone('Europe/London')

def get_current_gameweek():
    """Determine which gameweek we're currently in based on current time"""
    uk_tz = get_uk_timezone()
    now = datetime.now(uk_tz).replace(tzinfo=None)  # Remove timezone for comparison
    
    for gw_num, start_date, deadline, end_time in GAMEWEEK_SCHEDULE:
        # Convert dates to UK timezone
        uk_start = uk_tz.localize(start_date).replace(tzinfo=None)
        uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
        uk_end = uk_tz.localize(end_time).replace(tzinfo=None)
        
        # Check if we're in the gameweek window
        # Window opens after previous gameweek ends, closes at end_time (6 hours after last game)
        if gw_num == 1:
            # First gameweek - allow submissions from start of season
            window_start = uk_start - timedelta(days=7)
        else:
            # Subsequent gameweeks - window opens after previous gameweek ends
            prev_end = uk_tz.localize(GAMEWEEK_SCHEDULE[gw_num-2][3]).replace(tzinfo=None)
            window_start = prev_end
        
        if window_start <= now <= uk_end:
            return gw_num, uk_deadline
    
    # If no active gameweek found, return the next upcoming one
    for gw_num, start_date, deadline, end_time in GAMEWEEK_SCHEDULE:
        uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
        if now < uk_deadline:
            return gw_num, uk_deadline
    
    return None, None

def is_deadline_passed(gameweek_num):
    """Check if the deadline for a specific gameweek has passed"""
    uk_tz = get_uk_timezone()
    now = datetime.now(uk_tz).replace(tzinfo=None)
    
    for gw_num, start_date, deadline, end_time in GAMEWEEK_SCHEDULE:
        if gw_num == gameweek_num:
            uk_deadline = uk_tz.localize(deadline).replace(tzinfo=None)
            return now > uk_deadline
    
    return True  # If gameweek not found, assume deadline passed

def format_deadline(deadline_dt):
    """Format deadline time for display"""
    uk_tz = get_uk_timezone()
    uk_deadline = uk_tz.localize(deadline_dt)
    return uk_deadline.strftime("%A %d %B at %H:%M")