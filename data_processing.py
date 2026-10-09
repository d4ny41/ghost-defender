"""Raw competition CSVs -> data/processed/.

Step 1: loading and play-window extraction only.
"""

from __future__ import annotations

import glob
import os
from typing import Iterable

import pandas as pd

RAW_DIR = os.path.join("data", "raw")
TRACKING_GLOB = os.path.join(RAW_DIR, "tracking", "tracking_*.csv")
PLAYS_PATH = os.path.join(RAW_DIR, "plays.csv")

# Window start: first frame carrying either of these (CLAUDE.md "Play window").
CATCH_EVENTS = {"pass_arrived", "pass_outcome_caught"}
# Window end: first frame at or after the start carrying one of these.
END_EVENTS = {"first_contact", "tackle", "out_of_bounds"}
LAST_FRAME_EVENT = "last_frame"

# Requested tracking columns. displayName is optional: the 2021 tracking files
# do not have it (names come from players.csv), so it is kept only if present.
TRACKING_REQUIRED = ["gameId", "playId", "nflId", "frameId", "team",
                     "x", "y", "s", "dir", "event"]
TRACKING_OPTIONAL = ["displayName"]
TRACKING_DTYPES = {
    "nflId": "Int64",          # nullable: the football has no nflId
    "x": "float32",
    "y": "float32",
    "s": "float32",
    "dir": "float32",
    "team": "category",
    "event": "category",
    "displayName": "category",
}

PLAYS_REQUIRED = ["gameId", "playId", "possessionTeam", "defensiveTeam"]
PLAYS_OPTIONAL = ["playDescription", "ballCarrierId"]


def load_tracking(paths: str | Iterable[str] | None = None) -> pd.DataFrame:
    """Read one or more tracking CSVs, keeping only the columns we need."""
    if paths is None:
        paths = sorted(glob.glob(TRACKING_GLOB))
    elif isinstance(paths, str):
        paths = [paths]
    paths = list(paths)
    if not paths:
        raise FileNotFoundError(f"No tracking files found matching {TRACKING_GLOB}")

    wanted = set(TRACKING_REQUIRED) | set(TRACKING_OPTIONAL)
    frames = []
    for path in paths:
        df = pd.read_csv(path, usecols=lambda c: c in wanted,
                         dtype={k: v for k, v in TRACKING_DTYPES.items()
                                if k not in ("team", "event", "displayName")})
        missing = [c for c in TRACKING_REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{path} is missing tracking columns: {missing}")
        frames.append(df)

    tracking = pd.concat(frames, ignore_index=True)
    # Cast categories after concat so all files share one category set.
    for col in ("team", "event", "displayName"):
        if col in tracking.columns:
            tracking[col] = tracking[col].astype("category")

    order = [c for c in TRACKING_REQUIRED[:3] + TRACKING_OPTIONAL + TRACKING_REQUIRED[3:]
             if c in tracking.columns]
    return tracking[order]


def load_plays(path: str = PLAYS_PATH) -> pd.DataFrame:
    """Read plays.csv: keys, teams, and playDescription / ballCarrierId if present."""
    wanted = set(PLAYS_REQUIRED) | set(PLAYS_OPTIONAL)
    plays = pd.read_csv(path, usecols=lambda c: c in wanted)
    missing = [c for c in PLAYS_REQUIRED if c not in plays.columns]
    if missing:
        raise ValueError(f"{path} is missing plays columns: {missing}")
    order = [c for c in PLAYS_REQUIRED + PLAYS_OPTIONAL if c in plays.columns]
    return plays[order]


def caught_play_keys(tracking: pd.DataFrame) -> set[tuple[int, int]]:
    """(gameId, playId) pairs whose tracking contains a catch event."""
    hits = tracking.loc[tracking["event"].isin(CATCH_EVENTS), ["gameId", "playId"]]
    return {(int(g), int(p)) for g, p in hits.drop_duplicates().itertuples(index=False)}


def extract_window(play_rows: pd.DataFrame) -> tuple[pd.DataFrame, int, int, str]:
    """Cut one play's tracking rows down to the play window.

    Returns (window_rows, catch_frame, end_frame, end_event).
    """
    if play_rows.empty:
        raise ValueError("extract_window: play_rows is empty")
    keys = play_rows[["gameId", "playId"]].drop_duplicates()
    if len(keys) != 1:
        raise ValueError(f"extract_window: expected rows for one play, got {len(keys)}")
    game_id, play_id = (int(v) for v in keys.iloc[0])

    # Events repeat on every player's row, so reduce to one row per (frame, event).
    events = (play_rows.loc[play_rows["event"].notna(), ["frameId", "event"]]
              .drop_duplicates())

    catch_frames = events.loc[events["event"].isin(CATCH_EVENTS), "frameId"]
    if catch_frames.empty:
        raise ValueError(f"Play {game_id}/{play_id}: no catch event "
                         f"({sorted(CATCH_EVENTS)})")
    catch_frame = int(catch_frames.min())

    end_rows = events[(events["frameId"] >= catch_frame)
                      & events["event"].isin(END_EVENTS)]
    if end_rows.empty:
        end_frame = int(play_rows["frameId"].max())
        end_event = LAST_FRAME_EVENT
    else:
        end_frame = int(end_rows["frameId"].min())
        # If several end events share that frame, pick deterministically.
        end_event = str(sorted(end_rows.loc[end_rows["frameId"] == end_frame,
                                            "event"].astype(str))[0])

    in_window = play_rows["frameId"].between(catch_frame, end_frame)
    window = play_rows[in_window]
    n_frames = window["frameId"].nunique()
    if n_frames < 2:
        raise ValueError(f"Play {game_id}/{play_id}: window {catch_frame}-{end_frame} "
                         f"has {n_frames} frame(s), need at least 2")

    window = window.sort_values(["frameId", "nflId"], na_position="last")
    return window.reset_index(drop=True), catch_frame, end_frame, end_event


if __name__ == "__main__":
    # Temporary smoke test: one tracking file, first caught play.
    first_file = sorted(glob.glob(TRACKING_GLOB))[0]
    tracking = load_tracking(first_file)
    keys = caught_play_keys(tracking)
    if not keys:
        raise SystemExit(f"No caught plays in {first_file}")
    game_id, play_id = min(keys)
    rows = tracking[(tracking["gameId"] == game_id) & (tracking["playId"] == play_id)]
    window, catch_frame, end_frame, end_event = extract_window(rows)

    print(f"file:            {first_file}")
    print(f"gameId:          {game_id}")
    print(f"playId:          {play_id}")
    print(f"catch_frame:     {catch_frame}")
    print(f"end_frame:       {end_frame}")
    print(f"end_event:       {end_event}")
    print(f"window frames:   {window['frameId'].nunique()}")
    print(f"distinct players:{window['nflId'].nunique(): d}  (football excluded; "
          f"{len(window) // window['frameId'].nunique()} rows per frame)")
