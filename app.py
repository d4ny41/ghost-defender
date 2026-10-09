"""Ghost Defender: Streamlit app comparing the real pursuit angle with the optimal one."""

from pathlib import Path

import pandas as pd
import streamlit as st

from field import draw_field

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MOCK_DIR = BASE_DIR / "data" / "mock"
FRAMES_FILE = "ghost_frames.csv"
SUMMARY_FILE = "play_summary.csv"

GREEN = "#2e7d32"
AMBER = "#f9a825"
RED = "#c62828"
GRAY = "#757575"


@st.cache_data
def load_data():
    """Load processed data if both files exist, otherwise the mock data.

    Returns (frames, summary, source) where source is "real" or "mock".
    """
    if (PROCESSED_DIR / FRAMES_FILE).exists() and (PROCESSED_DIR / SUMMARY_FILE).exists():
        data_dir, source = PROCESSED_DIR, "real"
    else:
        data_dir, source = MOCK_DIR, "mock"
    frames = pd.read_csv(data_dir / FRAMES_FILE)
    summary = pd.read_csv(data_dir / SUMMARY_FILE)
    return frames, summary, source


def is_no_intercept(row) -> bool:
    return row["status"] == "no_intercept"


def is_true(value) -> bool:
    """reached_carrier may come back from CSV as bool or as a string."""
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def fmt(value, decimals: int = 2) -> str:
    """Format a number, or an em dash for missing values."""
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}"


def play_label(row) -> str:
    if is_no_intercept(row):
        return f"Play {row['playId']} · no intercept"
    return f"Play {row['playId']} · {row['wasted_yards']:.1f} wasted yd"


def wasted_yards_html(row) -> str:
    """Big header block for the Wasted Yards number."""
    if is_no_intercept(row):
        value_text, colour, note = "No intercept possible", GRAY, ""
        value_size = "40px"
    else:
        wasted = row["wasted_yards"]
        value_text = f"{wasted:.1f}"
        value_size = "64px"
        if wasted < 1.0:
            colour, note = GREEN, "≈ optimal angle"
        elif wasted <= 5.0:
            colour, note = AMBER, ""
        else:
            colour, note = RED, ""

    parts = [
        '<div style="line-height:1.1">',
        '<div style="font-size:16px;opacity:0.8">Wasted Yards</div>',
        f'<div style="font-size:{value_size};font-weight:700;color:{colour}">{value_text}</div>',
    ]
    if note:
        parts.append(f'<div style="font-size:18px;color:{colour}">{note}</div>')
    if not is_true(row["reached_carrier"]):
        parts.append(
            '<div style="font-size:13px;opacity:0.75">(defender never reached the carrier)</div>'
        )
    parts.append("</div>")
    return "".join(parts)


st.set_page_config(layout="wide", page_title="Ghost Defender")

frames, summary, source = load_data()

if source == "mock":
    st.warning("MOCK DATA — run data_processing.py for real plays.")

st.title("Ghost Defender")
st.caption("Optimal pursuit angle vs the real one, after the catch.")

# Sidebar: game and play selection.
with st.sidebar:
    game_ids = sorted(summary["gameId"].unique().tolist())
    game_id = st.selectbox("gameId", game_ids)

    game_plays = summary[summary["gameId"] == game_id].sort_values("playId")
    labels = {int(r["playId"]): play_label(r) for _, r in game_plays.iterrows()}
    play_id = st.selectbox("playId", list(labels), format_func=labels.get)

    play = game_plays[game_plays["playId"] == play_id].iloc[0]
    description = play["description"] if pd.notna(play["description"]) else ""
    st.caption(description)

# Header: Wasted Yards plus metric tiles.
big_col, metrics_col = st.columns([1, 2])
with big_col:
    st.markdown(wasted_yards_html(play), unsafe_allow_html=True)
with metrics_col:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Real defender distance (yd)", fmt(play["real_dist"]))
    m2.metric("Ghost distance (yd)", fmt(play["ghost_dist"]))
    m3.metric("Time to intercept (s)", fmt(play["t_intercept"]))
    m4.metric(
        f"Ghost speed (yd/s) [{play['speed_source']}]",
        fmt(play["ghost_speed"], 1),
    )
    st.markdown(
        f"Defender: {play['defender_name']} · Ball carrier: {play['carrier_name']}"
    )

st.plotly_chart(draw_field(), width="stretch")
