"""World Cup 2026 configuration.

Kept separate from the live Premier League bot settings. Only the archived
World Cup services (see archive/worldcup2026/) import from this module.
"""
import os

# World Cup 2026 Google Sheets setup
WC_MASTER_SHEET_ID = os.environ.get('WC_MASTER_SHEET_ID')

# FIFA Rankings (April 1, 2026) for World Cup
FIFA_RANK = {
    "France": 1, "Spain": 2, "Argentina": 3, "England": 4, "Portugal": 5,
    "Brazil": 6, "Netherlands": 7, "Morocco": 8, "Belgium": 9, "Germany": 10,
    "Croatia": 11, "Colombia": 13, "Senegal": 14, "Mexico": 15,
    "USA": 16, "Uruguay": 17, "Japan": 18, "Switzerland": 19,
    "Iran": 21, "Turkey": 22, "Ecuador": 23, "Austria": 24,
    "South Korea": 25, "Australia": 27, "Algeria": 28, "Egypt": 29,
    "Canada": 30, "Norway": 31, "Panama": 33, "Ivory Coast": 34,
    "Sweden": 38, "Paraguay": 40, "Czechia": 41, "Scotland": 43,
    "Tunisia": 44, "DR Congo": 46, "Uzbekistan": 50, "Qatar": 55,
    "Iraq": 57, "South Africa": 60, "Saudi Arabia": 61, "Jordan": 63,
    "Bosnia & Herzegovina": 65, "Cape Verde": 69, "Ghana": 74,
    "Curacao": 82, "Haiti": 83, "New Zealand": 85
}

# Top-seeded team per group (highest FIFA-ranked) — 1pt for correct pick, 3pt for upset
GROUP_TOP_SEEDS = {
    'A': 'Mexico', 'B': 'Switzerland', 'C': 'Brazil', 'D': 'USA',
    'E': 'Germany', 'F': 'Netherlands', 'G': 'Belgium', 'H': 'Spain',
    'I': 'France', 'J': 'Argentina', 'K': 'Portugal', 'L': 'England',
}

# Team abbreviations for parsing WC commands
TEAM_ABBREVIATIONS = {
    # Common abbreviations
    'ENG': 'England', 'CRO': 'Croatia', 'FRA': 'France', 'ARG': 'Argentina',
    'BRA': 'Brazil', 'GER': 'Germany', 'ESP': 'Spain', 'POR': 'Portugal',
    'USA': 'USA', 'MEX': 'Mexico', 'CAN': 'Canada', 'NED': 'Netherlands',
    'BEL': 'Belgium', 'SWI': 'Switzerland', 'ITA': 'Italy', 'JPN': 'Japan',
    'AUS': 'Australia', 'KOR': 'South Korea', 'URU': 'Uruguay', 'COL': 'Colombia',
    'MAR': 'Morocco', 'SEN': 'Senegal', 'TUN': 'Tunisia', 'EGY': 'Egypt',
    'IRN': 'Iran', 'TUR': 'Turkey', 'ECU': 'Ecuador', 'AUT': 'Austria',
    'ALG': 'Algeria', 'NOR': 'Norway', 'PAN': 'Panama', 'CIV': 'Ivory Coast',
    'SWE': 'Sweden', 'PAR': 'Paraguay', 'CZE': 'Czechia', 'SCO': 'Scotland',
    'DRC': 'DR Congo', 'UZB': 'Uzbekistan', 'QAT': 'Qatar', 'IRQ': 'Iraq',
    'RSA': 'South Africa', 'KSA': 'Saudi Arabia', 'JOR': 'Jordan',
    'BIH': 'Bosnia & Herzegovina', 'CPV': 'Cape Verde', 'GHA': 'Ghana',
    'CUR': 'Curacao', 'HAI': 'Haiti', 'NZL': 'New Zealand'
}
