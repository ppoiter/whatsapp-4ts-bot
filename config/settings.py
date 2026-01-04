from datetime import datetime
import os

# Premier League 2025-26 Gameweek Schedule
# Format: (gameweek_number, start_date, deadline, end_time)
# Deadline is typically Friday 6:30 PM UK time before games start
# End time is 6 hours after the last game starts (for goal tracking window)
GAMEWEEK_SCHEDULE = [
    (1, datetime(2025, 8, 15), datetime(2025, 8, 15, 18, 30), datetime(2025, 8, 17, 23, 00)),
    (2, datetime(2025, 8, 22), datetime(2025, 8, 22, 18, 30), datetime(2025, 8, 25, 23, 00)),
    (3, datetime(2025, 8, 30), datetime(2025, 8, 30, 11, 00), datetime(2025, 8, 31, 7, 00)), 
    (4, datetime(2025, 9, 13), datetime(2025, 9, 13, 11, 00), datetime(2025, 9, 14, 16, 30)),
    (5, datetime(2025, 9, 20), datetime(2025, 9, 20, 11, 00), datetime(2025, 9, 21, 16, 30)),
    (6, datetime(2025, 9, 27), datetime(2025, 9, 27, 11, 00), datetime(2025, 9, 29, 20, 00)),
    (7, datetime(2025, 10, 3), datetime(2025, 10, 3, 18, 30), datetime(2025, 10, 5, 16, 30)),
    (8, datetime(2025, 10, 18), datetime(2025, 10, 18, 11, 00), datetime(2025, 10, 20, 20, 00)),
    (9, datetime(2025, 10, 24), datetime(2025, 10, 24, 18, 30), datetime(2025, 10, 26, 16, 30)),
    (10, datetime(2025, 11, 1), datetime(2025, 11, 1, 13, 30), datetime(2025, 11, 4, 2, 30)),
    (11, datetime(2025, 11, 8), datetime(2025, 11, 8, 11, 0), datetime(2025, 11, 10, 0, 30)),
    (12, datetime(2025, 11, 22), datetime(2025, 11, 22, 11, 0), datetime(2025, 11, 25, 2, 30)),
    (13, datetime(2025, 11, 29), datetime(2025, 11, 29, 13, 30), datetime(2025, 12, 1, 2, 30)),
    (14, datetime(2025, 12, 2), datetime(2025, 12, 2, 18, 00), datetime(2025, 12, 4, 20, 00)),
    (15, datetime(2025, 12, 6), datetime(2025, 12, 6, 11, 00), datetime(2025, 12, 9, 2, 30)),
    (16, datetime(2025, 12, 13), datetime(2025, 12, 13, 13, 30), datetime(2025, 12, 14, 22, 30)),
    (17, datetime(2025, 12, 20), datetime(2025, 12, 20, 11, 00), datetime(2025, 12, 22, 12, 30)),
    (18, datetime(2025, 12, 26), datetime(2025, 12, 26, 18, 30), datetime(2025, 12, 27, 20, 30)),
    (19, datetime(2025, 12, 30), datetime(2025, 12, 30, 18, 00), datetime(2026, 1, 1, 2, 30)),
    (20, datetime(2026, 1, 3), datetime(2026, 1, 3, 11, 0), datetime(2026, 1, 3, 16, 00)),
    (21, datetime(2026, 1, 6), datetime(2026, 1, 6, 18, 30), datetime(2026, 1, 8, 20, 00)),
    (22, datetime(2026, 1, 17), datetime(2026, 1, 17, 11, 00), datetime(2026, 1, 19, 20, 00)),
    (23, datetime(2026, 1, 24), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    (24, datetime(2026, 1, 31), datetime(2026, 1, 31, 13, 30), datetime(2026, 2, 3, 2, 00)),
    (25, datetime(2026, 2, 6), datetime(2026, 2, 6, 18, 30), datetime(2026, 2, 8, 18, 30)),
    (26, datetime(2026, 2, 10), datetime(2026, 2, 10, 18, 00), datetime(2026, 2, 11, 22, 00)),
    (27, datetime(2026, 2, 21), datetime(2026, 2, 21, 11, 00), datetime(2026, 2, 23, 22, 00)),
    (28, datetime(2026, 2, 27), datetime(2026, 2, 27, 18, 00), datetime(2026, 3, 1, 20, 00)),
    # (29, datetime(2026, 3, 04), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (30, datetime(2026, 3, 14), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (31, datetime(2026, 3, 21), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (32, datetime(2026, 4, 11), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (33, datetime(2026, 4, 18), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (34, datetime(2026, 4, 25), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (35, datetime(2026, 5, 2), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (36, datetime(2026, 5, 9), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (37, datetime(2026, 5, 17), datetime(2026, 1, 24, 11, 00), datetime(2026, 1, 26, 20, 00)),
    # (38, datetime(2026, 5, 24), datetime(2026, 5, 24, 15, 30), datetime(2026, 5, 25, 20, 00)),
]

# User mapping
USER_MAP = {
    "+447387303123": "Aaron",
    "+16043175991": "Adam",
    "+64272806500": "Aubrey",
    "+31618271215": "Ben",
    "+447950139194": "Calum",
    "+447950904385": "Dave",
    "+447845948768": "David",
    "+64211206201": "Dom",
    "+447871617112": "Fraser",
    "+447587626672": "Jerome",
    "+6421581535": "John",
    "+447517587086": "Joss",
    "+447375356774": "Peter",
    "+447526186549": "Rohan",
    "+447438895095": "Sam",
}

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID', 'your-google-sheet-id')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

ADMIN_PHONE = "+447375356774"

# Twilio setup
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = 'whatsapp:+14155238886'
