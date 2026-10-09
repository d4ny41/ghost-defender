# Ghost Defender — Project Context (v2)

Read this file before every task. It is the single source of truth for both halves of the project.

**Why v2:** the tracking data stops when the pass arrives, so there is no post-catch pursuit to measure. The project now measures pursuit **while the ball is in the air**, from the throw to the moment it arrives. Code written for v1 (post-catch, ball carrier, tackle) must be updated to match this file. `physics.py` still contains `solve_intercept` and `ghost_positions` from v1: keep them and their tests, but the pipeline no longer uses them.

## What we are building

A Streamlit + Plotly tool for NFL coaches. On every pass, at the moment of the throw, it takes the defender nearest the targeted receiver and launches a "Ghost Defender" from the same spot. The ghost runs a straight line to the point where the ball arrives, at that defender's own top speed. The app animates the throw, the real defender and the ghost, and reports **Wasted Yards**: how much farther from the catch point the real defender was than the ghost when the ball arrived.

## Team and file ownership

Never edit a file you do not own. If a task seems to need it, stop and say so.

| Owner | Files |
|---|---|
| Person 1 (backend) | `physics.py`, `data_processing.py`, `tests/`, the "Raw data schema notes" section of this file |
| Person 2 (frontend) | `field.py`, `app.py`, `make_mock_data.py` |
| Shared (change only when both agree) | `CLAUDE.md`, `.kiro/steering/ghost-defender.md`, `requirements.txt`, `README.md`, `.gitignore` |

Person 2's code must never import `physics.py` or `data_processing.py`. The only link between the two halves is the CSV contract below.

## Repository layout

```
CLAUDE.md                         this file
.kiro/steering/ghost-defender.md  identical copy for Kiro
requirements.txt
data/raw/          raw competition CSVs (git-ignored)
data/processed/    Person 1 output: ghost_frames.csv, play_summary.csv
data/mock/         Person 2 mock output, same filenames and columns
physics.py         pure maths, numpy only
data_processing.py CLI: raw CSVs -> data/processed/
tests/             pytest
make_mock_data.py  writes data/mock/
field.py           draw_field() -> plotly Figure
app.py             Streamlit app
```

## Conventions

- Python 3.10+. Backend: pandas, numpy. Frontend: streamlit, plotly. Tests: pytest. Plain `.py` files, no notebooks.
- Coordinates are in yards. `x` runs 0–120 along the field (end zones are 0–10 and 110–120). `y` runs 0–53.3 across it.
- Never flip or standardise play direction. Work in raw coordinates throughout.
- `s` is speed in yards per second. `dir` is the direction of motion in degrees, measured clockwise from the +y axis: 0 = +y, 90 = +x, 180 = −y, 270 = −x.
- Velocity from `s` and `dir`: `vx = s · sin(radians(dir))`, `vy = s · cos(radians(dir))`.
- Tracking runs at 10 frames per second, so consecutive frames are `DT = 0.1` s apart.
- Constants, defined once at the top of `physics.py`: `DT = 0.1`, `CONTACT_RADIUS = 1.0` (yards), `LEAGUE_MAX_SPEED = 8.5` (yd/s), `MAX_TARGET_DIST = 3.0` (yards).

## Core logic

### Play window

- Throw frame: the first frame whose event is `pass_forward`.
- Arrival frame: the first frame after the throw frame whose event is `pass_arrived`. If there is none, the first frame after the throw with an event starting `pass_outcome_`. If there is neither, skip the play.
- The window is every frame from the throw frame to the arrival frame, inclusive. Frames after the arrival frame are never used.
- `air_time = (arrival_frameId − throw_frameId) · DT`. Skip plays with `air_time` under 0.3 s.

### Actors

- Catch point `L` = the football's (x, y) at the arrival frame.
- Targeted receiver: the offensive player, excluding the QB, whose (x, y) at the arrival frame is closest to `L`. Skip the play if that distance is over `MAX_TARGET_DIST` (a throwaway or a pass with no clear target).
- Defender: the defensive player closest to the targeted receiver at the throw frame.
- Names and positions come from `players.csv` (tracking has no displayName).

### Ghost speed V

`V` = the real defender's maximum `s` on the play, from the first tracked frame up to and including the arrival frame. Never use frames after the arrival frame.

### Ghost path

The ghost starts at the defender's throw-frame position `D0` and runs straight at `L` at speed `V`, then stops at `L`.

```
dist0 = |L − D0|
u     = (L − D0) / dist0
ghost(τ) = D0 + u · min(V · τ, dist0)        τ = seconds since the throw
```

If `dist0` ≈ 0, the ghost is at `L` on every frame.

- `ghost_reached = (V · air_time >= dist0)`
- `ghost_reach_time = dist0 / V` if `ghost_reached`, otherwise empty.

### Wasted Yards

- `real_gap` = distance from the real defender to `L` at the arrival frame.
- `ghost_gap = max(dist0 − V · air_time, 0)`, which is the ghost's distance to `L` at arrival.
- `wasted_yards = real_gap − ghost_gap`, rounded to 2 dp.
- `real_dist` = path length of the real defender from the throw frame to the arrival frame (from x, y, not the `dis` column). Informational only.
- Interpretation: `wasted_yards` is non-negative in theory, because the ghost uses the defender's own top speed. Small negatives can appear from tracking noise. Treat anything under 0.5 as an optimal angle. If `ghost_reached` is False, the defender was out of range: even a perfect angle could not get there, so do not blame him for the gap.

### Worked examples (unit tests must reproduce these)

1. Velocity: `s=5, dir=90` → `(5, 0)`. `s=5, dir=180` → `(0, −5)`.
2. Path length of `(0,0) → (3,4) → (3,10)` = `11.0`.
3. Ghost to target: `D0=(0,0)`, `L=(10,0)`, `V=5`, `τ = 0, 1, 2, 3` → `(0,0)`, `(5,0)`, `(10,0)`, `(10,0)`.
4. Arrival gap: `D0=(0,0)`, `L=(10,0)`, `air_time=2`: `V=4` → `2.0`. `V=6` → `0.0`.
5. Reach time: `D0=(0,0)`, `L=(6,8)`, `V=5` → `2.0`.
6. Defender already at the catch point: `D0 = L = (5,5)`, `V=7`, `τ = 0, 1` → both `(5,5)`; gap `0.0`; reach time `0.0`.
7. Wasted Yards: `D0=(0,0)`, `L=(6,8)`, `V=5`, `air_time=2`, real defender at `(3,4)` on arrival → `ghost_gap = 0.0`, `real_gap = 5.0`, `wasted_yards = 5.0`.

### Golden play (shared by the mock data and the pipeline test)

A throw with 2.0 s of air time: 20 steps after the throw, 21 frames in the window.

- QB at `(40, 26)`. The football starts there at the throw and moves in a straight line to the catch point, arriving on the last step.
- Receiver: starts at `(50, 12)`, runs `dir = 90` at 7.0 yd/s (0.7 yd per step) → catch point `L = (64, 12)`.
- Defender: starts at `(58.4, 21.0)`, top speed 8.0 yd/s (0.8 yd per step).
  - Steps 1–8: he bites the wrong way, running `dir = 270` → reaches `(52.0, 21.0)`.
  - Steps 9–20: he runs straight at `L` → ends at `(59.68, 15.24)`.
- Ghost speed 8.0.

Expected results (tolerance ±0.01 unless stated):
- `dist0 = 10.60`, `ghost_reached = True`, `ghost_reach_time = 1.325` s
- ghost at `τ = 1.0` is `(62.63, 14.21)`; at `τ ≥ 1.4` it is at `(64, 12)`
- football at window step 10 (`τ = 1.0`) is `(52, 19)`
- `ghost_gap = 0.00`, `real_gap = 5.40`, `wasted_yards = 5.40`, `real_dist = 16.00`

These numbers were computed independently. If code disagrees with them, the code is wrong.

## Data contract (Person 1 writes, Person 2 reads)

Location: `data/processed/` for real data, `data/mock/` for mock data. Identical filenames and columns in both.

### `ghost_frames.csv` — one row per element per frame

| column | type | meaning |
|---|---|---|
| gameId | int | |
| playId | int | |
| frameId | int | original frameId from tracking |
| t | float | seconds since the throw (0.0 on the throw frame) |
| player_type | str | exactly `Receiver`, `Real Defender`, `Ghost Defender` or `Football` |
| nflId | int | ghost: the real defender's nflId; football: empty |
| displayName | str | ghost: `Ghost`; football: `football` |
| x | float | yards |
| y | float | yards |

Exactly 4 rows per frame, for every frame in the window. Sorted by gameId, playId, frameId, player_type.

### `play_summary.csv` — one row per play

| column | type | meaning |
|---|---|---|
| gameId | int | |
| playId | int | |
| description | str | `playDescription` from plays.csv, or empty |
| pass_result | str | `passResult` from plays.csv (e.g. C, I, IN), or empty |
| coverage | str | coverage column from plays.csv if one exists, or empty |
| receiver_nflId | int | |
| receiver_name | str | |
| defender_nflId | int | |
| defender_name | str | |
| defender_position | str | from players.csv |
| throw_frameId | int | first frame of the window |
| arrival_frameId | int | last frame of the window |
| arrival_event | str | event that closed the window |
| air_time | float | seconds |
| ghost_speed | float | yd/s |
| catch_x | float | L |
| catch_y | float | L |
| ghost_start_x | float | D0 |
| ghost_start_y | float | D0 |
| ghost_reached | bool | |
| ghost_reach_time | float | seconds; empty if not reached |
| real_dist | float | yards, 2 dp |
| real_gap | float | yards, 2 dp |
| ghost_gap | float | yards, 2 dp |
| wasted_yards | float | yards, 2 dp |

Plays that cannot be processed are skipped and logged, never written.

## Raw data schema notes

Person 1 fills this in and keeps it current.

- Tracking files: `data/raw/tracking/tracking_*.csv` (122 files). No displayName column.
- Team column: `team` (values: TODO confirm club abbreviations plus the football label)
- Football: TODO (team label and/or null nflId)
- Tracking ends at or within 2 frames of `pass_arrived`. There is no post-catch data.
- plays.csv: has possessionTeam, defensiveTeam, playDescription. No ballCarrierId. passResult: TODO. Coverage column name: TODO.
- players.csv: TODO (columns for nflId, name, position)
- Events seen: ball_snap, pass_forward, pass_arrived, pass_outcome_caught, first_contact, tackle, out_of_bounds (TODO: full list)

## Working rules for the agent

- Do one task per prompt. Do not start the next step until asked.
- Touch only the files named in the prompt.
- After writing code, run it or its tests and show the output. Never claim success without running.
- If the real data contradicts this file, stop and say so. Do not silently invent a workaround.
- Never change expected values in tests to make them pass. Find the bug instead.
