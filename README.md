# WhatsApp Player Picks Bot

A WhatsApp bot that receives player picks and saves them to Google Sheets.

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `python app.py`

## Deployment

### Railway
```bash
railway login
railway init
railway up
```

## Gameweek schedule

`GAMEWEEK_SCHEDULE` in `config/settings.py` is generated from the free Fantasy
Premier League API rather than typed by hand. Each row is
`(gameweek, start_date, deadline, end_time)` as naive UK wall-clock times:

- `start_date` — date of the gameweek's first kickoff
- `deadline` — FPL's own `deadline_time`
- `end_time` — the last kickoff plus a buffer (default 3 hours)

Rebuild the list with:

```bash
python -m scripts.gen_schedule            # rewrite config/settings.py
python -m scripts.gen_schedule --dry-run  # preview only, writes nothing
python -m scripts.gen_schedule --buffer-hours 6
```

Re-running overwrites the whole list, so hand-edit rows only *after* generating.
Gameweeks far in the future may be provisional (the API often lists a single
placeholder kickoff until TV picks are confirmed) — just re-run closer to the
time to fill them in.
