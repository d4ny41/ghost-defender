# Ghost Defender — Project Context

Read this file before every task. It is the single source of truth for both halves of the project.

## What we are building

A Streamlit + Plotly tool for NFL coaches. For every completed pass, it takes the defender nearest the ball carrier at the moment of the catch, simulates a "Ghost Defender" that runs the mathematically optimal straight-line pursuit angle, animates the real defender against the ghost, and reports **Wasted Yards** = distance the real defender ran − distance the ghost needed.

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
- Constants, defined once at the top of `physics.py`: `DT = 0.1`, `CONTACT_RADIUS = 1.0` (yards), `LEAGUE_MAX_SPEED = 8.5` (yd/s).

## Core maths

### Intercept point

Inputs at the catch frame: carrier position `C0`, carrier velocity `Vc` (from `s` and `dir`, assumed constant from then on), defender position `D0`, ghost speed `V`.

```
d = C0 − D0
a = Vc·Vc − V²
b = 2 (d·Vc)
c = d·d
Solve a·t² + b·t + c = 0 for the smallest t > 0.
```

Edge cases, checked in this order:
1. `V <= 0` → no solution.
2. `c` ≈ 0 (defender already on the carrier) → `t = 0`.
3. `|a| < 1e-9` (equal speeds) → `t = −c / b` if `b < 0`, otherwise no solution.
4. Otherwise `disc = b² − 4ac`. If `disc < 0` → no solution. Else take both roots and keep the smallest one greater than 0. If neither is positive → no solution.

Intercept point `I = C0 + Vc · t`. Ghost distance = `V · t` (equal to `|I − D0|`).

### Ghost path

Let `τ` be seconds since the catch, `τ = (frameId − catch_frameId) · DT`.

```
ghost(τ) = D0 + (I − D0) · min(τ / t, 1)
```

After reaching `I` the ghost stays at `I`. If `t = 0`, the ghost is at `I` on every frame.

### Ghost speed V

`V` = the real defender's maximum `s` across the play window, with `speed_source = "play_max"`. If no intercept exists at that speed, retry with `LEAGUE_MAX_SPEED` and `speed_source = "league"`. If there is still no solution, `status = "no_intercept"`, the ghost stays at `D0` on every frame, and `ghost_speed` holds the last speed tried.

### Play window

- Catch frame: the first frame whose event is the catch event (`pass_outcome_caught`).
- End frame: the first frame at or after the catch frame whose event is in `END_EVENTS` (tackle, out of bounds, touchdown, fumble — exact names in the schema notes). If none, the last frame of the play, with `end_event = "last_frame"`.
- The window is every frame from the catch frame to the end frame, inclusive. Skip plays whose window has fewer than 2 frames.

### Wasted Yards

- Contact frame: the first window frame where the real defender is within `CONTACT_RADIUS` of the carrier. If that never happens, use the last window frame and set `reached_carrier = False`.
- `real_dist`: sum of straight-line distances between consecutive real-defender positions from the catch frame to the contact frame, inclusive. Compute it from `x`, `y`, not from the `dis` column.
- `ghost_dist = V · t`.
- `wasted_yards = real_dist − ghost_dist`, rounded to 2 dp. Keep the sign.
- Interpretation: values below 1.0 count as an effectively optimal angle, because contact is declared at 1 yard rather than 0.

### Worked examples (unit tests must reproduce these)

1. Stationary carrier: `C0=(10,0)`, `Vc=(0,0)`, `D0=(0,0)`, `V=5` → `t=2.0`, `I=(10,0)`.
2. Crossing route: `C0=(10,0)`, `Vc=(0,5)`, `D0=(0,0)`, `V=10` → `t=1.1547`, `I=(10, 5.7735)`.
3. Faster carrier running away: `C0=(10,0)`, `Vc=(8,0)`, `D0=(0,0)`, `V=6` → no solution.
4. Equal speeds, carrier running back towards the defender: `C0=(10,0)`, `Vc=(−5,0)`, `D0=(0,0)`, `V=5` → `t=1.0`, `I=(5,0)`.
5. Velocity: `s=5, dir=90` → `(5, 0)`. `s=5, dir=180` → `(0, −5)`.
6. Ghost path: `D0=(0,0)`, `I=(10,0)`, `t=2.0` → `τ=1.0` gives `(5,0)`; `τ=2.0` gives `(10,0)`; `τ=2.4` gives `(10,0)`.
7. Path length of `(0,0) → (3,4) → (3,10)` = `11.0`.

### Golden play (shared by the mock data and the pipeline test)

A 40-frame window. At the catch frame the carrier is at `(60.0, 20.0)` with `s = 7.0`, `dir = 90`, and the nearest defender is at `(70.0, 35.0)`.

On each of the 39 steps after the catch:
- The carrier moves 0.7 yd: at `dir = 90` for steps 1–25, then at `dir = 45` for steps 26–39.
- The defender runs pure pursuit (the classic bad angle): it moves `min(0.8, remaining distance)` yards straight towards the carrier's new position. Once it is within 1.0 yd of the carrier, it copies the carrier's displacement on every later step.

Ghost speed = 8.0 yd/s (the defender's top speed).

Expected results (tolerance ±0.05):
- `t_intercept = 1.925` s, intercept `(73.47, 20.00)`
- contact on step 33 (the 34th frame of the window)
- ghost reaches the intercept on step 20 (the 21st frame)
- `real_dist = 26.40`, `ghost_dist = 15.40`, `wasted_yards = 11.00`

These numbers were computed independently. If code disagrees with them, the code is wrong.

## Data contract (Person 1 writes, Person 2 reads)

Location: `data/processed/` for real data, `data/mock/` for mock data. Identical filenames and columns in both.

### `ghost_frames.csv` — one row per player per frame

| column | type | meaning |
|---|---|---|
| gameId | int | |
| playId | int | |
| frameId | int | original frameId from tracking |
| t | float | seconds since the catch (0.0 on the catch frame) |
| player_type | str | exactly `Carrier`, `Real Defender` or `Ghost Defender` |
| nflId | int | for the ghost, the real defender's nflId |
| displayName | str | for the ghost, `Ghost` |
| x | float | yards |
| y | float | yards |

Exactly 3 rows per frame, for every frame in the window. Sorted by gameId, playId, frameId, player_type.

### `play_summary.csv` — one row per play

| column | type | meaning |
|---|---|---|
| gameId | int | |
| playId | int | |
| description | str | `playDescription` from plays.csv, or empty |
| carrier_nflId | int | |
| carrier_name | str | |
| defender_nflId | int | |
| defender_name | str | |
| catch_frameId | int | first frame of the window |
| end_frameId | int | last frame of the window |
| end_event | str | event that closed the window, or `last_frame` |
| ghost_speed | float | yd/s |
| speed_source | str | `play_max` or `league` |
| t_intercept | float | seconds; empty if no_intercept |
| intercept_x | float | empty if no_intercept |
| intercept_y | float | empty if no_intercept |
| ghost_start_x | float | D0 |
| ghost_start_y | float | D0 |
| real_dist | float | yards, 2 dp; empty if no_intercept |
| ghost_dist | float | yards, 2 dp; empty if no_intercept |
| wasted_yards | float | yards, 2 dp; empty if no_intercept |
| reached_carrier | bool | |
| contact_frameId | int | empty if not reached |
| status | str | `ok` or `no_intercept` |

Plays that cannot be processed at all are skipped and logged, never written.

## Raw data schema notes

Person 1 fills this in after inspecting the files. Until then, inspect the data rather than guessing.

- Raw files are currently in `.kiro/steering/data/raw/`, not `data/raw/` (which is empty). Files: `games.csv`, `players.csv`, `plays.csv`, `pffScoutingData.csv`, and `tracking/tracking_<gameId>.csv` (122 files, one per game, 5-9 MB each). This is the 2021 season, pass plays only (8,557 plays).
- Tracking columns: gameId, playId, nflId, frameId, time, jerseyNumber, team, playDirection, x, y, s, a, dis, o, dir, event. There is NO `displayName` column: player names come from `players.csv` (nflId -> displayName). `nflId` is float because the football's is null.
- Team column name and values: `team`. Values are the club abbreviation (e.g. `TB`, `DAL`) or `football`. There is no home/away label. Offence vs defence must come from `plays.csv` possessionTeam / defensiveTeam.
- How the football is labelled: `team == "football"`, `nflId` null, `jerseyNumber` null. It is the only row type with null nflId.
- plays.csv has possessionTeam / defensiveTeam: yes, both.
- plays.csv has ballCarrierId: NO. There is no ball-carrier column anywhere. The carrier must be derived (e.g. the football's nearest offensive player at the catch frame, or the targeted receiver from `pffScoutingData.csv`, whose `pff_role` is one of Pass, Pass Route, Pass Block, Pass Rush, Coverage; there is no "Targeted Receiver" role).
- plays.csv has playDescription: yes, `playDescription`. Other useful plays.csv columns: passResult (C, I, S, R, IN), playResult, absoluteYardlineNumber.
- Exact event names: catch = `pass_outcome_caught`; tackle = `tackle`; out of bounds = `out_of_bounds`; fumble = `fumble` (also `fumble_offense_recovered`, `qb_strip_sack`); touchdown = NO event exists (404 plays mention TOUCHDOWN in playDescription only). Other events: ball_snap, autoevent_ballsnap, pass_forward, autoevent_passforward, pass_arrived, pass_tipped, autoevent_passinterrupted, pass_outcome_incomplete, dropped_pass, first_contact, handoff, lateral, run, play_action, qb_sack, man_in_motion, shift, line_set, huddle_break_offense, penalty_flag.
- Event coverage is very sparse across all 122 files: `pass_outcome_caught` appears in only 23 plays, `tackle` in 3, `out_of_bounds` in 1, `fumble` in 17. None of the 23 caught plays has a tackle, out_of_bounds or fumble event, so every one would fall back to `end_event = "last_frame"` under the current window rules. `pass_arrived` (367 plays) and `first_contact` (80 plays) are much more common.
- Events are repeated on every player's row for that frame (23 rows per frame), so count plays, not rows.
- Not yet checked: whether `x`/`y` units, `dir` convention and 10 fps match the Conventions section.

## Working rules for the agent

- Do one task per prompt. Do not start the next step until asked.
- Touch only the files named in the prompt.
- After writing code, run it or its tests and show the output. Never claim success without running.
- If the real data contradicts this file, stop and say so. Do not silently invent a workaround.
- Never change expected values in tests to make them pass. Find the bug instead.
