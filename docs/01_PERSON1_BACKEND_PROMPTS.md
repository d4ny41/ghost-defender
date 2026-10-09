# 01 · Person 1 — Data Pipeline and Physics

**Goal:** turn the raw tracking CSVs into `data/processed/ghost_frames.csv` and `data/processed/play_summary.csv`, exactly matching the contract in `CLAUDE.md`.

**Files you own:** `physics.py`, `data_processing.py`, `tests/`, and the "Raw data schema notes" section of `CLAUDE.md`.

**Order:** P1-0 → P1-7. Commit after each one passes its check.

---

## P1-0 · Inspect the raw data

The real column names decide everything downstream, so the agent looks before it builds.

```text
Task: inspect the raw data. Do not write any project code yet.

1. List every file in data/raw/ with its size in MB.
2. For plays.csv and for ONE tracking file, read only the first 200,000 rows and print the column names with dtypes, and 3 sample rows.
3. In the tracking sample, print value_counts of the event column.
4. Work out how the football is identified. Check displayName, whether nflId is null, and the team column.
5. Tell me:
   - which column holds the team (e.g. club or team) and what values it takes
   - whether plays.csv has possessionTeam and defensiveTeam
   - whether plays.csv has ballCarrierId
   - whether plays.csv has playDescription
   - the exact event names for: catch, tackle, out of bounds, touchdown, fumble
6. Fill in the "Raw data schema notes" section of CLAUDE.md with these findings, and make the identical edit in .kiro/steering/ghost-defender.md. Change nothing else in either file.

Stop and show me the summary.
```

**Check:** the schema notes no longer say TODO. Read them. If the catch event is not `pass_outcome_caught`, tell Person 2 straight away.

---

## P1-1 · Physics functions and unit tests

```text
Task: create physics.py (numpy only, no pandas) and tests/test_physics.py. Touch no other file.

At the top of physics.py define the constants DT, CONTACT_RADIUS and LEAGUE_MAX_SPEED with the values in CLAUDE.md.

Functions:
1. velocity_from_s_dir(s, dir_deg) -> numpy array (vx, vy), using the dir convention in CLAUDE.md.
2. solve_intercept(carrier_pos, carrier_vel, defender_pos, speed) -> (t, numpy array I) or None.
   Implement the quadratic and the four edge cases exactly in the order given in CLAUDE.md "Intercept point".
3. ghost_positions(defender_pos, intercept_pos, t_intercept, taus) -> numpy array of shape (len(taus), 2).
   taus are seconds since the catch. Use the formula in CLAUDE.md "Ghost path". If t_intercept is 0, every row is the intercept point.
4. path_length(points) -> float. Sum of distances between consecutive rows of an (n, 2) array. Return 0.0 for fewer than 2 rows.

Tests in tests/test_physics.py:
- One test per worked example 1–7 in CLAUDE.md, using pytest.approx(abs=1e-3).
- speed = 0 with a moving carrier returns None and does not crash.

Run pytest and show the full output. Fix the code until every test passes.
```

**Check:** `pytest` shows 8 passed. Open `physics.py` and confirm `vx` uses `sin` and `vy` uses `cos`. That swap is the single most likely bug.

→ **Checkpoint A** with Person 2.

---

## P1-2 · Loading and the play window

```text
Task: start data_processing.py. Write loading and window functions only.

1. load_tracking(paths) -> DataFrame. Read the tracking CSV(s) (glob data/raw/tracking*.csv, or the names in the schema notes), keeping only: gameId, playId, nflId, displayName, frameId, <team column>, x, y, s, dir, event. Use float32 for x, y, s, dir and category dtype for repeated strings.
2. load_plays() -> DataFrame. Read plays.csv, keeping gameId, playId, possessionTeam, defensiveTeam, plus playDescription and ballCarrierId if they exist.
3. caught_play_keys(tracking) -> set of (gameId, playId) pairs that contain the catch event.
4. extract_window(play_rows) -> (window_rows, catch_frame, end_frame, end_event).
   play_rows is every tracking row for ONE play. Follow CLAUDE.md "Play window" exactly.
   Define END_EVENTS at the top of the file using the exact names in the schema notes.
   Raise ValueError with a clear message if there is no catch event or the window has fewer than 2 frames.

Add a temporary __main__ block that loads ONE tracking file, picks the first caught play, and prints: gameId, playId, catch_frame, end_frame, end_event, number of frames in the window, and number of distinct players.

Run it and show the output.
```

**Check:** the window is a plausible length. A catch-and-run is usually 10–60 frames (1–6 seconds). `end_event` should usually be a tackle or out of bounds.

---

## P1-3 · Identify the ball carrier and the nearest defender

```text
Task: in data_processing.py add identify_actors(window_rows, play_row, catch_frame).

1. Split the rows into football, offense (team == possessionTeam) and defense (team == defensiveTeam), using the labelling in the schema notes.
2. Carrier: if play_row has a non-null ballCarrierId, use it. Otherwise, the offensive player whose (x, y) at catch_frame is closest to the football's (x, y) at catch_frame.
3. Defender: the defensive player with the smallest Euclidean distance to the carrier at catch_frame.
4. Return:
   - a dict with carrier_nflId, carrier_name, defender_nflId, defender_name, carrier_to_ball_dist, defender_to_carrier_dist
   - a DataFrame with only the carrier's and the defender's rows across the window, sorted by frameId
5. Raise ValueError with a clear message if the football, the carrier or any defender is missing at catch_frame.

Update the __main__ block to print the dict for the same play, and both players' x, y, s and dir at the catch frame.

Run it. Then answer in two sentences: is the carrier within about 2 yards of the ball, and is the defender's distance plausible for coverage?
```

**Check:** `carrier_to_ball_dist` is under about 2 yards. If plays.csv has `ballCarrierId`, ask the agent to report how often the nearest-to-ball rule agrees with it on 20 random plays. Agreement above 90% means the fallback logic is sound.

---

## P1-4 · Ghost and Wasted Yards for one play

This is the biggest prompt. Put `Plan first: list the functions you will write and their signatures, then wait for my OK.` at the front.

```text
Task: in data_processing.py add process_play(play_rows, play_row) -> (frames_df, summary_dict). Both must match the contract in CLAUDE.md exactly: ghost_frames.csv columns for frames_df, play_summary.csv columns for summary_dict.

Steps:
1. extract_window, then identify_actors.
2. At catch_frame: C0 = carrier (x, y). Vc = physics.velocity_from_s_dir(carrier s, carrier dir). D0 = defender (x, y).
3. Ghost speed: follow CLAUDE.md "Ghost speed V" exactly (play_max, then league fallback, then no_intercept).
4. For every window frame, tau = (frameId - catch_frame) * DT. Ghost positions from physics.ghost_positions. For no_intercept, the ghost sits at D0 on every frame.
5. Contact frame, real_dist, ghost_dist and wasted_yards: follow CLAUDE.md "Wasted Yards" exactly. Use physics.path_length on the defender's positions from the catch frame to the contact frame inclusive.
6. frames_df in long format: 3 rows per frame, player_type exactly "Carrier", "Real Defender", "Ghost Defender". The ghost row uses the defender's nflId and displayName "Ghost". Sort as the contract says.
7. summary_dict: every contract column, in contract order. Round distances to 2 dp. Use NaN for the empty fields.

Update the __main__ block to run process_play on the same play and print the summary dict, plus the first 6 and last 6 rows of frames_df.

Run it. Then say in three sentences whether the numbers are physically sensible: ghost_speed in yd/s (expect 5–10), t_intercept in seconds (expect 0.5–4), distances in yards.
```

**Check:** compare `t_intercept` to the play length. If the ghost needs 3 seconds but the play ends after 1.5, that is fine (the carrier was tackled by someone else), but `reached_carrier` should then be False.

---

## P1-5 · Golden-play pipeline test

This test proves the whole pipeline: windowing, carrier detection, nearest defender, physics and metric.

```text
Task: create tests/test_pipeline.py. It builds the "Golden play" from CLAUDE.md as synthetic raw tracking rows, runs process_play on it, and checks the expected numbers. Touch no other file unless the test exposes a bug.

Write a helper make_golden_play() -> (tracking_df, play_row) inside the test file:
- Use exactly the same column names, team labelling and football labelling as the real data (see the schema notes).
- gameId = 1, playId = 1. possessionTeam "OFF", defensiveTeam "DEF".
- frameIds 1–48:
  - Frames 1–5: everyone stands still at their catch-frame positions with s = 0. Event "ball_snap" on frame 1, "pass_forward" on frame 3 (use the real names from the schema notes if they differ). All other events empty.
  - Frame 6: the catch event. Frames 6–45 are the golden-play motion (40 frames: frame 6 is the catch position, then 39 steps).
  - Frame 45: the tackle event.
  - Frames 46–48: everyone frozen. The window must exclude these.
- Players:
  - carrier: nflId 101, OFF, s = 7.0 on every frame from 6 onwards, dir = 90 on frames 6–30 and 45 afterwards.
  - QB: nflId 102, OFF, standing at (45, 25).
  - nearest defender: nflId 201, DEF, s = 8.0 from frame 6 until contact, 7.0 afterwards. dir = its heading that frame (not used, any value is fine).
  - second defender: nflId 202, DEF, standing at (30, 45).
  - football: at the carrier's position + (0.2, 0.1) on frames 1–6, then moving with the carrier.
- play_row: ballCarrierId missing or null (so the nearest-to-ball logic is tested). description "Golden test play".

Assertions:
- carrier_nflId == 101, defender_nflId == 201
- catch_frameId == 6, end_frameId == 45, end_event is the tackle event
- ghost_speed == 8.0, speed_source == "play_max"
- t_intercept ≈ 1.925, intercept ≈ (73.47, 20.00)
- contact_frameId == 39, reached_carrier is True
- real_dist ≈ 26.40, ghost_dist ≈ 15.40, wasted_yards ≈ 11.00 (abs = 0.05 for all of these)
- frames_df has 120 rows (40 frames × 3)
- the ghost is at the intercept point on every frame from frameId 26 onwards

Run pytest on the whole tests folder and show the output. If an assertion fails, find and fix the bug in data_processing.py or physics.py. Do not change the expected values; they were computed independently.
```

**Check:** all tests pass. If the agent wants to change an expected number, refuse.

---

## P1-6 · Batch processing CLI

```text
Task: turn data_processing.py into a command-line script that processes every caught play and writes the two contract files.

1. CLI with argparse:
   python data_processing.py [--weeks 1 2 ...] [--max-plays N] [--out data/processed]
   Default: all tracking files, all caught plays. --weeks selects tracking files by week number if the file names contain one; ignore it if there is a single tracking file.
2. Process one tracking file at a time to keep memory low. In each file, keep only the rows of caught plays before grouping.
3. Loop over plays with groupby(["gameId", "playId"]). Wrap each call to process_play in try/except. On error, skip the play and count it by error message. One bad play must never crash the run.
4. Concatenate the results. Write <out>/ghost_frames.csv and <out>/play_summary.csv with exactly the contract columns, in contract order, without the index.
5. Add validate_outputs(frames_df, summary_df) and run it before writing. It asserts:
   - columns and their order match the contract
   - player_type contains only the three allowed strings
   - every summary play has frames and every framed play has a summary row
   - each (gameId, playId, frameId) has exactly 3 rows
   - no NaN in x or y
   - status contains only "ok" and "no_intercept"
6. Print at the end: plays processed, plays skipped with the top 5 reasons, no_intercept count, wasted_yards.describe() for status "ok", and total runtime.
7. Delete the temporary __main__ demo code. Keep only the CLI.

First run with --max-plays 50 and show the output. Then run on one full tracking file and show the output. Do not run the full dataset until I ask.
```

**Check:** skipped plays are under about 10%. If one error message dominates, paste it back to the agent and ask for a fix. Then run the full dataset yourself.

→ **Checkpoint B:** give Person 2 the two CSVs from `data/processed/`.

---

## P1-7 · Sanity audit and demo picks

```text
Task: create scratch_audit.py. This is a throwaway helper, not part of the deliverable. It reads data/processed/play_summary.csv and prints:

1. The 10 plays with the largest wasted_yards where status == "ok" and reached_carrier is True.
2. Suspicious rows, grouped by type:
   - wasted_yards < -3
   - wasted_yards > 40
   - t_intercept > 6
   - ghost_speed < 3 or ghost_speed > 11
   - real_dist == 0
   For each group, print the count, 3 examples, and a one-line hypothesis for the cause.
3. Three recommended demo plays: wasted_yards between 8 and 25, reached_carrier True, window between 20 and 60 frames, ideally a description that reads like a catch-and-run. Print gameId, playId, description and wasted_yards for each.

Run it and show the output.
```

**Check:** send the three demo picks to Person 2. If one suspicious group is large (more than about 5% of plays), investigate it before the demo, since a judge may click on exactly that kind of play.
