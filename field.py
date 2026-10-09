"""Draw an NFL field in tracking-data coordinates (yards) with Plotly.

x runs 0-120 along the field (end zones 0-10 and 110-120), y runs 0-53.3.
Only layout shapes, one scatter trace (hash marks) and annotations are used.
"""

from pathlib import Path

import plotly.graph_objects as go

FIELD_LENGTH = 120.0
FIELD_WIDTH = 53.3

GRASS_COLOR = "#3a7d2c"
END_ZONE_COLOR = "#245a1b"
LINE_COLOR = "white"
PAPER_COLOR = "#111111"

HASH_LENGTH = 0.7
INNER_HASH_Y = (23.58, 29.75)
SIDELINE_HASH_Y = (1.0, 52.3)
YARD_NUMBER_Y = (12.0, 41.3)


def _hash_trace() -> go.Scatter:
    """All hash marks as one line trace, segments separated by None."""
    xs, ys = [], []
    half = HASH_LENGTH / 2
    for x in range(11, 110):
        for yc in INNER_HASH_Y + SIDELINE_HASH_Y:
            xs += [x, x, None]
            ys += [yc - half, yc + half, None]
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(color=LINE_COLOR, width=1),
        name="field",
        hoverinfo="skip",
        showlegend=False,
    )


def draw_field() -> go.Figure:
    """Return a Plotly figure of the field, ready for player traces on top."""
    fig = go.Figure(data=[_hash_trace()])

    shapes = [
        # Grass between the goal lines.
        dict(type="rect", x0=10, x1=110, y0=0, y1=FIELD_WIDTH,
             fillcolor=GRASS_COLOR, line=dict(width=0), layer="below"),
        # End zones.
        dict(type="rect", x0=0, x1=10, y0=0, y1=FIELD_WIDTH,
             fillcolor=END_ZONE_COLOR, line=dict(width=0), layer="below"),
        dict(type="rect", x0=110, x1=FIELD_LENGTH, y0=0, y1=FIELD_WIDTH,
             fillcolor=END_ZONE_COLOR, line=dict(width=0), layer="below"),
    ]

    # Yard lines every 5 yards; goal lines and the 50 slightly thicker.
    for x in range(10, 111, 5):
        width = 3 if x in (10, 60, 110) else 1.5
        shapes.append(dict(type="line", x0=x, x1=x, y0=0, y1=FIELD_WIDTH,
                           line=dict(color=LINE_COLOR, width=width),
                           layer="below"))

    # Border around the whole field.
    shapes.append(dict(type="rect", x0=0, x1=FIELD_LENGTH, y0=0, y1=FIELD_WIDTH,
                       line=dict(color=LINE_COLOR, width=2),
                       fillcolor="rgba(0,0,0,0)", layer="below"))

    # Yard numbers 10..50..10 at x = 20..100.
    annotations = []
    for x in range(20, 101, 10):
        number = x - 10 if x <= 60 else 110 - x
        for y in YARD_NUMBER_Y:
            annotations.append(dict(
                x=x, y=y, text=f"<b>{number}</b>", showarrow=False,
                font=dict(color=LINE_COLOR, size=18),
                xref="x", yref="y",
            ))

    axis_common = dict(
        visible=False, showgrid=False, zeroline=False,
        showticklabels=False, ticks="", autorange=False, fixedrange=True,
    )
    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(range=[0, FIELD_LENGTH], **axis_common),
        yaxis=dict(range=[0, FIELD_WIDTH], scaleanchor="x", scaleratio=1,
                   **axis_common),
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PAPER_COLOR,
        margin=dict(l=10, r=10, t=10, b=10),
        height=600,
        showlegend=False,
    )
    return fig


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "field_preview.html"
    draw_field().write_html(out)
    print(out)
