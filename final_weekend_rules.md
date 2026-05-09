# Final Premier League Weekend – Rule Changes

## Overview
One-off rule changes for the final gameweek of the 2025/26 Premier League season.

## Pick Changes
- Number of picks increased from **4 to 8** goalscorers per player.

## Scoring Changes
- Points per goal are weighted by how many **other** participants picked the same scorer.
- Formula: `points_per_goal = max(0.1, 1 - 0.1 × number_of_other_pickers)`
- "Other pickers" excludes the player themselves.

### Examples
| Other pickers | Multiplier |
|---------------|------------|
| 0 (unique pick) | 1.0 |
| 1 | 0.9 |
| 2 | 0.8 |
| 5 | 0.5 |
| 9+ | 0.1 (floor) |

- A player's total score is the sum across all 8 picks.

## Leaderboard
- When the admin logs a goal (e.g. `goal haaland`), the bot should automatically recalculate the **simple leaderboard**, which can then be accessed by the admin
- If no picks have scored yet, just show all participants on 0.
- Two leaderboard views, triggered by different commands:

### Simple view (default, shown automatically after each `goal` command)
Command: `leaderboard` (also auto-posted after `goal`)
```
🏆 LEADERBOARD

1. Pete — 2.6 pts
2. Dave — 1.8 pts
3. Mike — 0.0 pts
```

### Detailed view (on demand)
Command: `leaderboard detail`
```
🏆 LEADERBOARD (DETAILED)

1. Pete — 2.6 pts
   ⚽ Haaland (1g × 0.6) = 0.6
   ⚽ Wissa (2g × 1.0) = 2.0

2. Dave — 1.8 pts
   ⚽ Haaland (1g × 0.6) = 0.6
   ⚽ Salah (1g × 0.4) = 0.4
   ⚽ Palmer (1g × 0.8) = 0.8

3. Mike — 0.0 pts
```

## What Needs to Change
1. **Pick limit**: Update from 4 to 8.
2. **Scoring logic**: Replace flat points-per-goal with the weighted formula above.
3. **Results/leaderboard output**: Show the multiplier per scorer so people can see how popularity affected their score.
4. **Announcement/help text**: Update any bot responses that reference the number of picks or how scoring works.

## What Stays the Same
- Picks are still hidden until lockout.
- Admin commands remain unchanged.
- Pick submission flow is the same (just more picks).