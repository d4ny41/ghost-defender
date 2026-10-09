# 01 · Person 1 — Data Pipeline and Physics (v2)

**Goal:** turn the raw tracking CSVs into `data/processed/ghost_frames.csv` and `data/processed/play_summary.csv`, exactly matching the v2 contract in `CLAUDE.md`.

**What changed in v2:** the data ends when the pass arrives, so the window is now throw → arrival, the "carrier" is now the targeted receiver, and the ghost runs to the catch point. P1-0 and P1-1 are done and stay as they are. Everything from P1-1b onwards replaces the v1 prompts.

**Before you start:** replace `CLAUDE.md` and `.kiro/steering/ghost-defender.md` in the repo with the v2 file, commit, and tell Person 2. Then open a **fresh chat** so the agent isn't carrying v1 assumptions.

**Order:** P1-1b → P1-7. Commit after each one passes its check.

---

## P1-1b · New physics functions

```text
Task: add the v2 functions to physics.py and tests to tests/test_physics.py. Keep every existing function and test. Touch no other file.

1. Add MAX_TARGET_DIST = 3.0 to the constants at the top.
2. ghost_to_target(defender_pos, target_pos, speed, taus) -> numpy array of shape (len(taus), 2).
   Use the formula in CLAUDE.md "Ghost path". If the distance is about 0, every row is the target.
3. reach_time(defender_pos, target_pos, speed) -> float, or None if speed <= 0.
4. arrival_gap(defender_pos, target_pos, speed, air_time) -> float, = max(dist0 − speed · air_time, 0).

Tests: one test per worked example 3–7 in CLAUDE.md v2, using pytest.approx(abs=1e-3). Example 7 should use arrival_gap plus a plain distance for real_gap.

Run the whole tests folder and show the output.
```

**Check:** all old and new tests pass.

---

## P1-2b · Rework loading and the play window

```text
Task: update data_processing.py to the v2 play window in CLAUDE.md. Remove the v1 CATCH_EVENTS and END_EVENTS logic.

1. load_players() -> DataFrame with nflId, a name column and a position column from data/raw/players.csv. Print its columns first so we use the right names.
2. load_plays(): also keep passResult and any coverage column (for example pff_passCoverage or pff_passCoverageType) if they exist.
3. Replace caught_play_keys with pass_play_keys(tracking): the (gameId, playId) pairs that contain a pass_forward event.
4. Rewrite extract_window(play_rows) -> (window_rows, throw_frame, arrival_frame, arrival_event), following CLAUDE.md "Play window" exactly. Raise ValueError with a clear message for: no throw, no arrival, or air_time under 0.3 s.
5. Update the "Raw data schema notes" section of CLAUDE.md, and make the identical edit in .kiro/steering/ghost-defender.md: fill every TODO (team values, football label, passResult values, coverage column, players.csv columns, full list of events). Change nothing else in either file.
6. Replace the __main__ block with a scan of ALL tracking files that prints:
   - plays with a pass_forward event
   - valid windows, and rejections grouped by reason
   - a histogram of air_time in 0.5 s buckets
   - arrival_event counts
   - passResult counts among valid windows
   - the first 3 valid windows (gameId, playId, throw_frame, arrival_frame, air_time)

Run it and show the output.
```

**Check:** most plays with a `pass_forward` should now give a valid window, with air times mostly between 0.5 and 3 seconds. If valid windows are under about 150 plays, tell me the numbers before going further.

---

## P1-3 · Identify the receiver and the defender

```text
Task: rewrite identify_actors in data_processing.py for v2:
identify_actors(window_rows, play_row, players, throw_frame, arrival_frame).

1. Split rows into football, offense (team == possessionTeam) and defense (team == defensiveTeam), using the schema notes.
2. Catch point L = the football's (x, y) at arrival_frame.
3. Targeted receiver: the offensive player, excluding the QB (by position from players), whose (x, y) at arrival_frame is closest to L. Raise ValueError "no clear target" if that distance is over MAX_TARGET_DIST.
4. Defender: the defensive player closest to the receiver at throw_frame.
5. Return:
   - a dict with receiver_nflId, receiver_name, defender_nflId, defender_name, defender_position, receiver_to_ball_dist, defender_to_receiver_dist, catch_x, catch_y
   - a DataFrame with only the receiver's, the defender's and the football's rows across the window, sorted by frameId
6. Raise ValueError with a clear message if the football, the receiver or any defender is missing on the frames needed.

Update the __main__ block to run this on the first 20 valid plays and print one line each: receiver name, defender name and position, receiver_to_ball_dist, defender_to_receiver_dist. Also print how many of the 20 were rejected and why.

Run it. Then answer in two sentences: are the defenders mostly cornerbacks, safeties and linebackers, and are their distances to the receiver plausible for coverage (mostly under 10 yards)?
```

**Check:** defender positions are mostly CB, S and LB, not defensive linemen. If several are linemen, the team split is probably wrong.

---

## P1-4 · Ghost and Wasted Yards for one play

Put `Plan first: list the functions you will write and their signatures, then wait for my OK.` at the front.

```text
Task: rewrite process_play in data_processing.py for v2:
process_play(play_rows, play_row, players) -> (frames_df, summary_dict).
Both must match the v2 contract in CLAUDE.md exactly.

Steps:
1. extract_window, then identify_actors.
2. D0 = the defender's (x, y) at the throw frame. L = (catch_x, catch_y).
3. V: follow CLAUDE.md "Ghost speed V" exactly. Use play_rows (the whole play), but only frames up to and including arrival_frame.
4. For each window frame, tau = (frameId − throw_frame) · DT. Ghost positions from physics.ghost_to_target.
5. ghost_reached, ghost_reach_time, real_gap, ghost_gap, wasted_yards and real_dist: follow CLAUDE.md "Ghost path" and "Wasted Yards" exactly. Use physics.arrival_gap, physics.reach_time and physics.path_length.
6. frames_df in long format: 4 rows per frame, player_type exactly "Receiver", "Real Defender", "Ghost Defender", "Football". Ghost rows use the defender's nflId and displayName "Ghost". Football rows have an empty nflId and displayName "football".
7. summary_dict: every contract column, in contract order, with pass_result, coverage and description from play_row (empty string if missing). Round distances to 2 dp.

Update the __main__ block to run process_play on the first valid play and print the summary dict, plus the first 8 and last 8 rows of frames_df.

Run it. Then say in three sentences whether the numbers are physically sensible: ghost_speed in yd/s (expect 5–10), air_time in seconds (expect 0.5–3.5), gaps in yards.
```

**Check:** on the last frame, the football row's (x, y) equals `catch_x`, `catch_y`.

---

## P1-5 · Golden-play pipeline test

```text
Task: replace tests/test_pipeline.py with a v2 version. It builds the "Golden play" from CLAUDE.md v2 as synthetic raw data, runs process_play, and checks the expected numbers. Touch no other file unless the test exposes a bug.

Helper make_golden_play() -> (tracking_df, play_row, players_df):
- Same column names, team labelling and football labelling as the real data (see the schema notes). Same columns in players_df as the real players.csv.
- gameId = 1, playId = 1. possessionTeam "OFF", defensiveTeam "DEF". passResult "C".
- frameIds 1–28:
  - Frames 1–5: everyone stands at their throw-frame position. Event "ball_snap" on frame 1. Defender 201 has s = 0 on these frames.
  - Frame 6: "pass_forward". Frames 6–26 are the golden-play motion (frame 6 is the start, then 20 steps).
  - Frame 26: "pass_arrived".
  - Frames 27–28: everyone frozen, but defender 201 has s = 9.5 on these frames. They must be excluded, so the ghost speed must still come out as 8.0.
- Players:
  - receiver: nflId 101, OFF, position WR. s = 7.0, dir = 90 from frame 6.
  - QB: nflId 102, OFF, position QB, standing at (40, 26).
  - decoy receiver: nflId 103, OFF, position WR, standing at (45, 40).
  - defender: nflId 201, DEF, position CB. s = 8.0 on frames 6–26. dir = 270 for the bite, then his actual heading.
  - decoy defender: nflId 202, DEF, position SS, standing at (75, 30).
  - football: with the QB on frames 1–6, then moving in a straight line to the catch point, arriving on frame 26.

Assertions:
- receiver_nflId == 101, defender_nflId == 201, defender_position == "CB"
- throw_frameId == 6, arrival_frameId == 26, arrival_event == "pass_arrived", air_time ≈ 2.0
- ghost_speed == 8.0
- catch point ≈ (64, 12), ghost start ≈ (58.4, 21.0)
- ghost_reached is True, ghost_reach_time ≈ 1.325
- ghost_gap ≈ 0.0, real_gap ≈ 5.40, wasted_yards ≈ 5.40, real_dist ≈ 16.00 (abs = 0.01)
- frames_df has 84 rows (21 frames × 4)
- ghost at frameId 16 ≈ (62.63, 14.21); ghost at (64, 12) on every frame from frameId 20 onwards
- football at frameId 16 ≈ (52, 19)

Run pytest on the whole tests folder and show the output. If an assertion fails, find and fix the bug in data_processing.py or physics.py. Do not change the expected values; they were computed independently.
```

**Check:** all tests pass.

---

## P1-6 · Batch processing CLI

```text
Task: turn data_processing.py into a command-line script that processes every pass play and writes the two v2 contract files.

1. CLI with argparse: python data_processing.py [--max-files N] [--max-plays N] [--out data/processed]. Default: all tracking files, all plays.
2. Load plays.csv and players.csv once. Process one tracking file at a time to keep memory low; in each file, keep only rows of pass plays before grouping.
3. Loop over plays with groupby(["gameId", "playId"]). Wrap each process_play call in try/except. On error, skip the play and count it by error message. One bad play must never crash the run.
4. Concatenate the results and write <out>/ghost_frames.csv and <out>/play_summary.csv with exactly the contract columns, in contract order, without the index.
5. Add validate_outputs(frames_df, summary_df) and run it before writing. It asserts:
   - columns and their order match the contract
   - player_type contains only the four allowed strings
   - every summary play has frames, and every framed play has a summary row
   - each (gameId, playId, frameId) has exactly 4 rows
   - no NaN in x or y
   - on each play's arrival frame, the Football row equals (catch_x, catch_y)
6. Print at the end: plays processed, plays skipped with the top 5 reasons, the ghost_reached rate, wasted_yards.describe() for ghost_reached plays, and total runtime.
7. Delete the temporary __main__ demo code. Keep only the CLI.

First run with --max-files 5 and show the output. Then run on everything and show the output.
```

**Check:** skipped plays are under about 25% (throwaways and no-clear-target passes are expected skips). Most `wasted_yards` values should sit between 0 and about 6.

→ **Checkpoint B:** give Person 2 the two CSVs from `data/processed/`.

---

## P1-7 · Sanity audit and demo picks

```text
Task: create scratch_audit.py. This is a throwaway helper, not part of the deliverable. It reads data/processed/play_summary.csv and prints:

1. The 10 plays with the largest wasted_yards where ghost_reached is True.
2. Suspicious rows, grouped by type:
   - wasted_yards < -0.5
   - wasted_yards > 15
   - ghost_speed < 3 or ghost_speed > 11
   - air_time > 3.5
   - defender_position not a defensive back or linebacker
   For each group, print the count, 3 examples and a one-line hypothesis for the cause.
3. Three recommended demo plays: wasted_yards between 2 and 8, ghost_reached True, air_time of at least 1.5 s, and ideally pass_result "C" (the better angle could have contested a completed catch). Print gameId, playId, description, defender_name, wasted_yards and air_time for each.

Run it and show the output.
```

**Check:** send the three demo picks to Person 2. If a suspicious group is large (more than about 5% of plays), look at it before the demo.
