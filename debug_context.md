# Debugging Elimination Status Issue

## Problem
The elimination status check isn't working even though entries are on the Player Scores sheet. Suspected case sensitivity issue.

## Investigation Summary

### Code Location
- Main logic: `services/sheets_service.py:192` - `get_elimination_status()`
- Called from: `services/gameweek_service.py:36`

### Sample Data

#### Picks Data Format
```
2025-08-26T11:10:13.629997    +447526186549    Rohan    3    2025-08-29 18:30    Ekitiké    Wood    Mbeumo    Cunha
2025-08-26T18:14:06.147043    +64272806500    Aubrey    3    2025-08-29 18:30    Pedro    Wood    Richarlison    Cunha
2025-08-26T23:53:42.723589    +447375356774    Peter    3    2025-08-30 11:00    Semenyo    Wood    Salah    Mateta
2025-08-27T08:40:00.707798    +447375356774    Peter    3    2025-08-30 11:00    Semenyo    Wood    Salah    Mateta
2025-08-27T19:42:25.880540    +447845948768    David    3    2025-08-30 11:00    Haaland    Gyokeres    Watkins    Semenyo
2025-08-28T07:44:07.139855    +64272806500    Aubrey    3    2025-08-30 11:00    Pedro    Wood    Richarlison    Thiago
```

#### Player Scores Sheet Format
```
Gameweek    Player    Scored    Updated
3    wood    No    2025-08-28T19:56:01.896847
3    cunha    Yes    2025-08-28T19:56:54.154809
```

### Issue Analysis
- Player Scores sheet uses lowercase names ("wood", "cunha")
- Picks use capitalized names ("Wood", "Cunha") 
- Code converts both to lowercase with `.strip().lower()` so should match
- Logic should work: Wood→wood, Cunha→cunha

### Debug Code Added
Added debug logging to `services/sheets_service.py` lines 207-221 and 243-256:
- Shows records found in Player Scores sheet
- Shows gameweek being searched
- Shows each player and their scored status
- Shows final scorers dictionary
- Shows each pick being checked and match results

### Testing Method
1. Start Flask app: `python app.py`
2. Test with curl: `curl -X POST "http://localhost:5000/webhook" -d "From=whatsapp:+447375356774&Body=show active"`
3. Check console output for debug information

### Recent Commits
- `4024310` - add debug logging for elimination status
- `56f73ad` - fix remaining admin phone number comparisons  
- `c69b601` - fix admin phone number comparison for show picks command

## Next Steps
Run the curl test and analyze the debug output to see exactly what's happening with the player name matching.