"""Write mock data/mock/ghost_frames.csv and data/mock/play_summary.csv (v2).

Follows the v2 data contract in CLAUDE.md: pass plays from the throw to the
pass arrival, with a receiver, the real defender, the ghost and the football.
Uses only numpy and pandas and does not import physics.py or
data_processing.py: the ghost path and the gaps are re-implemented locally
from CLAUDE.md "Ghost path" and "Wasted Yards".
"""

from pathlib import Path

import numpy as np
import pandas as pd

DT = 0.1

OUT_DIR = Path(__file__).resolve().parent / "data" / "mock"
OUT_FILES = ("ghost_frames.csv", "play_summary.csv")

FRAME_COLUMNS = [
    "gameId", "playId", "frameId", "t", "player_type",
    "nflId", "displayName", "x", "y",
]
SUMMARY_COLUMNS = [
    "gameId", "playId", "description", "pass_result", "coverage",
    "receiver_nflId", "receiver_name", "defender_nflId", "defender_name",
    "defender_position", "throw_frameId", "arrival_frameId", "arrival_event",
    "air_time", "ghost_speed", "catch_x", "catch_y", "ghost_start_x",
    "ghost_start_y", "ghost_reached", "ghost_reach_time", "real_dist",
    "real_gap", "ghost_gap", "wasted_yards",
]

RECEIVER_ID, RECEIVER_NAME = 101, "Mock Receiver"
DEFENDER_ID, DEFENDER_NAME, DEFENDER_POS = 201, "Mock Defender", "CB"


# --- local maths (CLAUDE.md "Ghost path" and "Wasted Yards") ---------------

def velocity(s, dir_deg):
    rad = np.radians(dir_deg)
    return np.array([s * np.sin(rad), s * np.cos(rad)])


def ghost_path(d0, catch, v, taus):
    """ghost(tau) = D0 + u * min(V * tau, dist0); at L every frame if dist0 ~ 0."""
    d0, catch = np.asarray(d0, float), np.asarray(catch, float)
    dist0 = np.linalg.norm(catch - d0)
    if np.isclose(dist0, 0.0):
        return np.tile(catch, (len(taus), 1))
    u = (catch - d0) / dist0
    return d0 + u * np.minimum(v * np.asarray(taus, float), dist0)[:, None]


def ghost_gap(dist0, v, air_time):
    return max(dist0 - v * air_time, 0.0)


def path_length(points):
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


# --- simulations ------------------------------------------------------------

def straight_run(start, step_len, dir_deg, steps):
    """Start at start, then `steps` steps of step_len in direction dir_deg."""
    step = velocity(step_len, dir_deg)
    return np.asarray(start, float) + step * np.arange(steps + 1)[:, None]


def run_at(start, target, step_len, steps):
    """Move step_len per step straight at a fixed target, stopping on it."""
    pts = [np.asarray(start, float)]
    target = np.asarray(target, float)
    for _ in range(steps):
        gap = target - pts[-1]
        dist = np.linalg.norm(gap)
        move = min(step_len, dist)
        pts.append(pts[-1] + gap / dist * move if dist > 0 else pts[-1].copy())
    return np.array(pts)


def football_path(qb, catch, steps):
    """Straight line from the QB to the catch point, arriving on the last step."""
    qb, catch = np.asarray(qb, float), np.asarray(catch, float)
    frac = (np.arange(steps + 1) / steps)[:, None]
    return qb + (catch - qb) * frac


# --- assembling a play ------------------------------------------------------

def build_play(game_id, play_id, description, pass_result, coverage,
               frame_ids, receiver, defender, football, ghost_speed,
               follow_ghost=False):
    frame_ids = np.asarray(frame_ids)
    taus = (frame_ids - frame_ids[0]) * DT
    air_time = round(float(taus[-1]), 1)

    catch = football[-1]                    # L = football at the arrival frame
    d0 = defender[0]                        # D0 = defender at the throw frame
    v = float(ghost_speed)
    ghost = ghost_path(d0, catch, v, taus)
    if follow_ghost:
        defender = ghost.copy()

    # Positions as written to the CSV; the summary is computed from these.
    receiver, defender, ghost, football = (
        np.round(a, 4) for a in (receiver, defender, ghost, football))
    catch, d0 = football[-1], defender[0]

    rows = []
    for k, fid in enumerate(frame_ids):
        t = round(float(taus[k]), 1)
        for ptype, nfl_id, name, pos in (
            ("Receiver", RECEIVER_ID, RECEIVER_NAME, receiver[k]),
            ("Real Defender", DEFENDER_ID, DEFENDER_NAME, defender[k]),
            ("Ghost Defender", DEFENDER_ID, "Ghost", ghost[k]),
            ("Football", pd.NA, "football", football[k]),
        ):
            rows.append([game_id, play_id, int(fid), t, ptype, nfl_id, name,
                         float(pos[0]), float(pos[1])])

    dist0 = float(np.linalg.norm(catch - d0))
    reached = bool(v * air_time >= dist0)
    real_gap = float(np.linalg.norm(defender[-1] - catch))
    g_gap = ghost_gap(dist0, v, air_time)

    summary = {
        "gameId": game_id,
        "playId": play_id,
        "description": description,
        "pass_result": pass_result,
        "coverage": coverage,
        "receiver_nflId": RECEIVER_ID,
        "receiver_name": RECEIVER_NAME,
        "defender_nflId": DEFENDER_ID,
        "defender_name": DEFENDER_NAME,
        "defender_position": DEFENDER_POS,
        "throw_frameId": int(frame_ids[0]),
        "arrival_frameId": int(frame_ids[-1]),
        "arrival_event": "pass_arrived",
        "air_time": air_time,
        "ghost_speed": v,
        "catch_x": float(catch[0]),
        "catch_y": float(catch[1]),
        "ghost_start_x": float(d0[0]),
        "ghost_start_y": float(d0[1]),
        "ghost_reached": reached,
        "ghost_reach_time": round(dist0 / v, 4) if reached else np.nan,
        "real_dist": round(path_length(defender), 2) + 0.0,
        "real_gap": round(real_gap, 2) + 0.0,
        "ghost_gap": round(g_gap, 2) + 0.0,
        "wasted_yards": round(real_gap - g_gap, 2) + 0.0,
    }
    return rows, summary


def main():
    frames, summaries = [], []

    # Plays 1 and 2: CLAUDE.md "Golden play". 2.0 s air time, 20 steps.
    golden_ids = np.arange(1, 22)
    qb = (40.0, 26.0)
    golden_receiver = straight_run((50.0, 12.0), 0.7, 90, 20)
    golden_catch = golden_receiver[-1]
    golden_football = football_path(qb, golden_catch, 20)

    # Defender bites the wrong way for 8 steps, then runs straight at L.
    bite = straight_run((58.4, 21.0), 0.8, 270, 8)
    chase = run_at(bite[-1], golden_catch, 0.8, 12)
    golden_defender = np.vstack([bite, chase[1:]])

    r, s = build_play(
        1, 1, "MOCK – defender bites, then chases", "C", "Cover 3",
        golden_ids, golden_receiver, golden_defender, golden_football, 8.0)
    frames += r
    summaries.append(s)

    r, s = build_play(
        1, 2, "MOCK – optimal angle, pass broken up", "I", "Cover 3",
        golden_ids, golden_receiver, golden_defender, golden_football, 8.0,
        follow_ghost=True)
    frames += r
    summaries.append(s)

    # Play 3: deep ball, 2.5 s air time, defender takes a perfect angle but
    # is too slow.
    p3_ids = np.arange(1, 27)
    p3_receiver = straight_run((50.0, 10.0), 0.9, 90, 25)
    p3_catch = p3_receiver[-1]
    r, s = build_play(
        2, 1, "MOCK – deep ball, defender out of range", "C", "",
        p3_ids, p3_receiver, run_at((60.0, 40.0), p3_catch, 0.7, 25),
        football_path(qb, p3_catch, 25), 7.0)
    frames += r
    summaries.append(s)

    frames_df = pd.DataFrame(frames, columns=FRAME_COLUMNS)
    frames_df["nflId"] = frames_df["nflId"].astype("Int64")
    frames_df = frames_df.sort_values(
        ["gameId", "playId", "frameId", "player_type"]).reset_index(drop=True)

    summary_df = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in OUT_FILES:          # remove old mock files before writing
        (OUT_DIR / name).unlink(missing_ok=True)
    frames_df.to_csv(OUT_DIR / "ghost_frames.csv", index=False, encoding="utf-8")
    summary_df.to_csv(OUT_DIR / "play_summary.csv", index=False, encoding="utf-8")

    with pd.option_context("display.max_columns", None, "display.width", 250):
        print(summary_df.drop(columns=["description", "receiver_name",
                                       "defender_name"]).to_string(index=False))
    print(f"\nWrote {len(frames_df)} frame rows and {len(summary_df)} plays to {OUT_DIR}")


if __name__ == "__main__":
    main()
