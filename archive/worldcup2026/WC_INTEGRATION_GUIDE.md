# World Cup 2026 Integration - Setup Guide

## 🎉 Integration Complete!

Your existing 4ts WhatsApp bot now supports World Cup 2026 commands! Both systems run simultaneously.

## What Was Added

### Files Added:
- `services/wc_command_service.py` - WC command handling
- `services/wc_sheets_service.py` - WC Google Sheets integration  
- `services/wc_scoring_service.py` - WC scoring and leaderboard logic
- `WorldCup2026_Forms.gs` - Google Apps Script for forms
- `WC_INTEGRATION_GUIDE.md` - This guide

### Files Modified:
- `app.py` - Added WC command routing (prioritizes `wc` commands)
- `config/settings.py` - Added WC configuration and team data
- `requirements.txt` - Added fuzzy matching dependencies

## How It Works

### Command Routing:
1. **WC Commands** (start with `wc`): Routed to World Cup system
2. **Other Commands**: Routed to existing 4ts system
3. **No Conflict**: Both systems work independently

### Example Commands:
```
wc leaderboard          → World Cup leaderboard
wc result ENG 2-1 FRA   → Enter WC match result (admin only)
wc bonus 2 Peter Dave   → Award WC bonus points (admin only)

leaderboard             → 4ts leaderboard
goal Mohamed Salah      → 4ts goal entry
show picks             → 4ts picks summary
```

## Setup Steps

### 1. Create Google Forms (One-time setup)

1. Go to [script.google.com](https://script.google.com)
2. Create new project, paste `WorldCup2026_Forms.gs` content
3. Run `createAllForms()` - creates all 4 WC forms
4. Link each form to response spreadsheets
5. Run `createMasterSheet()` - note the spreadsheet ID
6. Update script with master sheet ID, run `installTriggers()`

### 2. Add Environment Variable

Add to Railway (or your hosting platform):
```bash
WC_MASTER_SHEET_ID=your_master_spreadsheet_id
```

### 3. Grant Sheet Access

Share the WC master spreadsheet with your existing service account email.

### 4. Deploy

Push the updated code to Railway:
```bash
git add .
git commit -m "Add World Cup 2026 support"
git push
```

## Testing

Send these messages to test both systems:

**World Cup Testing:**
```
wc help
wc leaderboard
wc result ENG 2-1 FRA  (admin only)
```

**4ts Testing (should still work):**
```
leaderboard
goal Haaland
show picks
```

## Admin Commands

Only you (admin phone) can:
- Enter match results: `wc result ENG 2-1 CRO`
- Award bonus points: `wc bonus 2 Peter Dave Aaron`
- View detailed scores: `wc scores Peter`

## Data Architecture

### Existing 4ts Data:
- Unchanged, continues to work normally
- Uses existing Google Sheet

### World Cup Data:
- Separate master spreadsheet
- 6 tabs: form responses + results + bonus
- Independent scoring system

## Form Sharing

Once forms are created, share with your group:
- **Form 1**: Pre-tournament picks (deadline before June 11)
- **Form 2**: Matchday 1 predictions (deadline before June 11)
- **Form 3**: Matchday 2 predictions (deadline before June 18)  
- **Form 4**: Matchday 3 predictions (deadline before June 24)

## Troubleshooting

**WC commands not working?**
- Check WC_MASTER_SHEET_ID environment variable
- Verify service account has access to WC spreadsheet
- Check Railway logs for errors

**4ts stopped working?**
- Should be impossible - code is isolated
- Check existing environment variables unchanged
- Test with non-WC commands

**Forms not copying to master sheet?**
- Verify Apps Script triggers installed
- Check MASTER_SHEET_ID in script
- Test trigger functions manually

## Support

Your bot now supports both:
- ✅ Premier League 4ts game (existing functionality)
- ✅ World Cup 2026 tipping competition (new)

Both systems are completely independent and won't interfere with each other!

---

🏆⚽ Ready for World Cup 2026! 🏆⚽