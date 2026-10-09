"""Write mock data/mock/ghost_frames.csv and data/mock/play_summary.csv.

Follows the data contract in CLAUDE.md. Uses only numpy and pandas and does not
import physics.py or data_processing.py: the intercept maths is re-implemented
locally from CLAUDE.md "Intercept point" and "Ghost path".
"""

from pathlib import Path

import numpy as np
import pandas as pd

DT = 0.1
CONTACT_RADIUS = 1.0
LEAGUE_MAX_SPEED = 8.5

OUT_DIR = Path(__file__).resolve().parent / "data" / "mock"

FRAME_COLUMNS = [
    "gameId", "playId", "frameId", "t", "player_type",
    "nflId", "displayName", "x", "y",
]
SUMMARY_COLUMNS = [
    "gameId", "playId", "description", "carrier_nflId", "carrier_name",
    "defender_nflId", "defender_name", "catch_frameId", "end_frameId",
    "end_event", "ghost_speed", "speed_source", "t_intercept", "intercept_x",
    "intercept_y", "ghost_start_x", "ghost_start_y", "real_dist", "ghost_dist",
    "wasted_yards", "reached_carrier", "contact_frameId", "status",
]

CARRIER_ID, CARRIER_NAME = 101, "Mock Carrier"
DEFENDER_ID, DEFENDER_NAME = 201, "Mock Defender"


# --- local maths (CLAUDE.md "Core maths") ---------------------------------

def velocity(s, dir_deg):
    rad = np.radians(dir_deg)
    return np.array([s * np.sin(rad), s * np.cos(rad)])


def intercept_time(c0, vc, d0, v):
    """Smallest t > 0 at which a defender at d0 with speed v meets the carrier.

    Returns None when there is no solution. Edge cases in CLAUDE.md order.
    """
    if v <= 0:
        return None
    d = np.asarray(c0, float) - np.asarray(d0, float)
    vc = np.asarray(vc, float)
    a = vc @ vc - v ** 2
    b = 2.0 * (d @ vc)
    c = d @ d
    if np.isclose(c, 0.0):
        return 0.0
    if abs(a) < 1e-9:
        return -c / b if b < 0 else None
    disc = b ** 2 - 4 * a * c
    if disc < 0:
        return None
    root = np.sqrt(disc)
    positive = [r for r in ((-b - root) / (2 * a), (-b + root) / (2 * a)) if r > 0]
    return min(positive) if positive else None


def ghost_path(d0, i_pt, t_int, taus):
    d0, i_pt = np.asarray(d0, float), np.asarray(i_pt, float)
    if t_int == 0:
        return np.tile(i_pt, (len(taus), 1))
    frac = np.minimum(np.asarray(taus) / t_int, 1.0)[:, None]
    return d0 + (i_pt - d0) * frac


def path_length(points):
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


# --- simulations ------------------------------------------------------------

def carrier_path(c0, step_len, dirs):
    """Carrier positions: start at c0, then one step of step_len per dir."""
    pts = [np.asarray(c0, float)]
    for d in dirs:
        pts.append(pts[-1] + velocity(step_len, d))
    return np.array(pts)


def pure_pursuit(carrier, d0, step_len):
    """Defender moves min(step_len, remaining) towards the carrier's new position.

    Once within CONTACT_RADIUS it copies the carrier's displacement.
    """
    pts = [np.asarray(d0, float)]
    for k in range(1, len(carrier)):
        prev = pts[-1]
        if np.linalg.norm(carrier[k - 1] - prev) <= CONTACT_RADIUS:
            pts.append(prev + (carrier[k] - carrier[k - 1]))
            continue
        gap = carrier[k] - prev
        dist = np.linalg.norm(gap)
        move = min(step_len, dist)
        pts.append(prev + gap / dist * move if dist > 0 else prev.copy())
    return np.array(pts)


def follow_ghost(carrier, ghost):
    """Defender sits on the ghost path until within CONTACT_RADIUS, then
    copies the carrier's displacement."""
    pts = [ghost[0].copy()]
    locked = False
    for k in range(1, len(carrier)):
        prev = pts[-1]
        if locked or np.linalg.norm(carrier[k - 1] - prev) <= CONTACT_RADIUS:
            locked = True
            pts.append(prev + (carrier[k] - carrier[k - 1]))
        else:
            pts.append(ghost[k].copy())
    return np.array(pts)


# --- assembling a play ------------------------------------------------------

def solve_ghost(c0, vc, d0, play_max):
    """Try play_max, then LEAGUE_MAX_SPEED. Returns (V, source, t or None)."""
    for v, source in ((play_max, "play_max"), (LEAGUE_MAX_SPEED, "league")):
        t_int = intercept_time(c0, vc, d0, v)
        if t_int is not None:
            return v, source, t_int
    return v, source, None


def build_play(game_id, play_id, description, end_event, frame_ids,
               carrier, defender, vc, play_max, ghost_mode="independent"):
    frame_ids = np.asarray(frame_ids)
    taus = (frame_ids - frame_ids[0]) * DT
    c0, d0 = carrier[0], defender[0]

    v, source, t_int = solve_ghost(c0, vc, d0, play_max)
    if t_int is None:
        i_pt = None
        ghost = np.tile(np.asarray(d0, float), (len(frame_ids), 1))
    else:
        i_pt = np.asarray(c0, float) + vc * t_int
        ghost = ghost_path(d0, i_pt, t_int, taus)

    if ghost_mode == "follow":
        defender = follow_ghost(carrier, ghost)

    # Positions as written to the CSV; summary is computed from these.
    carrier = np.round(carrier, 4)
    defender = np.round(defender, 4)
    ghost = np.round(ghost, 4)

    rows = []
    for k, fid in enumerate(frame_ids):
        t = round(float(taus[k]), 1)
        for ptype, nfl_id, name, pos in (
            ("Carrier", CARRIER_ID, CARRIER_NAME, carrier[k]),
            ("Real Defender", DEFENDER_ID, DEFENDER_NAME, defender[k]),
            ("Ghost Defender", DEFENDER_ID, "Ghost", ghost[k]),
        ):
            rows.append([game_id, play_id, int(fid), t, ptype, nfl_id, name,
                         float(pos[0]), float(pos[1])])

    gaps = np.linalg.norm(defender - carrier, axis=1)
    hits = np.flatnonzero(gaps <= CONTACT_RADIUS)
    reached = hits.size > 0
    contact_idx = int(hits[0]) if reached else len(frame_ids) - 1

    summary = {
        "gameId": game_id,
        "playId": play_id,
        "description": description,
        "carrier_nflId": CARRIER_ID,
        "carrier_name": CARRIER_NAME,
        "defender_nflId": DEFENDER_ID,
        "defender_name": DEFENDER_NAME,
        "catch_frameId": int(frame_ids[0]),
        "end_frameId": int(frame_ids[-1]),
        "end_event": end_event,
        "ghost_speed": float(v),
        "speed_source": source,
        "t_intercept": np.nan,
        "intercept_x": np.nan,
        "intercept_y": np.nan,
        "ghost_start_x": float(d0[0]),
        "ghost_start_y": float(d0[1]),
        "real_dist": np.nan,
        "ghost_dist": np.nan,
        "wasted_yards": np.nan,
        "reached_carrier": bool(reached),
        "contact_frameId": int(frame_ids[contact_idx]) if reached else pd.NA,
        "status": "no_intercept" if t_int is None else "ok",
    }
    if t_int is not None:
        real_dist = round(path_length(defender[: contact_idx + 1]), 2)
        ghost_dist = round(v * t_int, 2)
        summary.update({
            "t_intercept": round(float(t_int), 4),
            "intercept_x": round(float(i_pt[0]), 4),
            "intercept_y": round(float(i_pt[1]), 4),
            "real_dist": real_dist,
            "ghost_dist": ghost_dist,
            "wasted_yards": round(path_length(defender[: contact_idx + 1])
                                  - v * t_int, 2),
        })
    return rows, summary


def main():
    frames, summaries = [], []

    # Plays 1 and 2: Golden play start (CLAUDE.md "Golden play").
    golden_ids = np.arange(1, 41)
    golden_carrier = carrier_path((60.0, 20.0), 0.7, [90] * 25 + [45] * 14)
    golden_vc = velocity(7.0, 90)
    golden_d0 = (70.0, 35.0)

    r, s = build_play(
        1, 1, "MOCK – pure pursuit vs optimal angle", "tackle", golden_ids,
        golden_carrier, pure_pursuit(golden_carrier, golden_d0, 0.8),
        golden_vc, play_max=8.0)
    frames += r
    summaries.append(s)

    r, s = build_play(
        1, 2, "MOCK – near-optimal angle", "tackle", golden_ids,
        golden_carrier, np.array([golden_d0]), golden_vc, play_max=8.0,
        ghost_mode="follow")
    frames += r
    summaries.append(s)

    # Play 3: carrier outruns the defender, no intercept at 6.0 or 8.5.
    p3_ids = np.arange(1, 31)
    p3_carrier = carrier_path((50.0, 10.0), 9.5 * DT, [90] * 29)
    r, s = build_play(
        2, 1, "MOCK – carrier outruns defender", "last_frame", p3_ids,
        p3_carrier, pure_pursuit(p3_carrier, (40.0, 40.0), 6.0 * DT),
        velocity(9.5, 90), play_max=6.0)
    frames += r
    summaries.append(s)

    frames_df = pd.DataFrame(frames, columns=FRAME_COLUMNS)
    frames_df = frames_df.sort_values(
        ["gameId", "playId", "frameId", "player_type"]).reset_index(drop=True)

    summary_df = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS)
    summary_df["contact_frameId"] = summary_df["contact_frameId"].astype("Int64")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames_df.to_csv(OUT_DIR / "ghost_frames.csv", index=False, encoding="utf-8")
    summary_df.to_csv(OUT_DIR / "play_summary.csv", index=False, encoding="utf-8")

    with pd.option_context("display.max_columns", None, "display.width", 250):
        print(summary_df.drop(columns=["description", "carrier_name",
                                       "defender_name"]).to_string(index=False))
    print(f"\nWrote {len(frames_df)} frame rows and {len(summary_df)} plays to {OUT_DIR}")


if __name__ == "__main__":
    main()
