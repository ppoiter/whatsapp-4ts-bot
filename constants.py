from datetime import datetime
import os

# Premier League 2025-26 Gameweek Schedule
# Format: (gameweek_number, start_date, deadline)
# Deadline is typically Friday 6:30 PM UK time before games start
GAMEWEEK_SCHEDULE = [
    (1, datetime(2025, 8, 15), datetime(2025, 8, 15, 18, 30)),  # GW1: Deadline Friday 15th Aug 6:30pm
    # Add more gameweeks as you get the fixture dates
    # Example format for subsequent gameweeks:
    (2, datetime(2025, 8, 22), datetime(2025, 8, 22, 18, 30)),
    (3, datetime(2025, 8, 29), datetime(2025, 8, 29, 18, 30)),
    (4, datetime(2025, 9, 13), datetime(2025, 9, 13, 11, 00)),
    (5, datetime(2025, 9, 20), datetime(2025, 9, 20, 11, 00)),
    (6, datetime(2025, 9, 27), datetime(2025, 9, 27, 11, 00)),
    # etc...
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
    "+447399224773": "Larry",
    "+447375356774": "Peter",
    "+447526186549": "Rohan",
    "+447438895095": "Sam"
}

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID', 'your-google-sheet-id')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

ADMIN_PHONE = "+447375356774"