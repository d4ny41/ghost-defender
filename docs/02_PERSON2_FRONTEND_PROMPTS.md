# 02 · Person 2 — Visualisation and Interface

**Goal:** a Streamlit app where a coach picks a play and watches the real defender (red) against the optimal Ghost Defender (gray), with Wasted Yards in large text above the field.

**Files you own:** `field.py`, `app.py`, `make_mock_data.py`. Never import Person 1's code. You only read the two CSVs described in `CLAUDE.md`.

**Order:** P2-0 → P2-5. Commit after each one passes its check.

---

## P2-0 · Mock data in the contract format

You build against this until Person 1's real data arrives.

```text
Task: create make_mock_data.py, which writes data/mock/ghost_frames.csv and data/mock/play_summary.csv in exactly the contract format in CLAUDE.md. Use only numpy and pandas. Do not import physics.py or data_processing.py. Touch no other file.

Implement a small local intercept function using the quadratic and edge cases in CLAUDE.md "Intercept point", and the ghost formula in "Ghost path".

Play 1 (gameId 1, playId 1): the "Golden play" from CLAUDE.md.
- 40 frames, frameIds 1–40, catch on frameId 1, end_event "tackle".
- Simulate the carrier and the real defender exactly as described there.
- Ghost speed 8.0 (speed_source "play_max"), carrier velocity from s = 7.0, dir = 90.
- Names "Mock Carrier" (nflId 101) and "Mock Defender" (nflId 201). description "MOCK – pure pursuit vs optimal angle".

Play 2 (gameId 1, playId 2): a near-perfect angle.
- Same start as play 1, same carrier motion.
- The real defender follows the ghost's path exactly until it is within 1.0 yd of the carrier, then copies the carrier's displacement.
- description "MOCK – near-optimal angle".

Play 3 (gameId 2, playId 1): no intercept possible.
- 30 frames. Carrier starts at (50, 10), dir = 90, 9.5 yd/s, straight line.
- Defender starts at (40, 40), pure pursuit at 6.0 yd/s, never reaches the carrier.
- No solution at 6.0 or at 8.5, so: status "no_intercept", ghost_speed 8.5, speed_source "league", ghost frozen at its start, t_intercept, intercept, real_dist, ghost_dist and wasted_yards empty, reached_carrier False.
- description "MOCK – carrier outruns defender".

Compute every summary column from the simulated positions (contact frame, distances, and so on). Do not hard-code results.

Run it and print the summary table. Play 1 must show t_intercept 1.925, intercept (73.47, 20.00), contact_frameId 34, wasted_yards 11.00 (±0.05). Play 2 must show wasted_yards between -1.5 and +1. If not, fix the simulation, not the expected values.
```

**Check:** play 1 shows 11.00 and play 2 shows a value near 0 (about −0.2). → **Checkpoint A** with Person 1.

---

## P2-1 · The football field

```text
Task: create field.py with draw_field() -> plotly.graph_objects.Figure. Use only Plotly shapes, scatter traces and annotations. No images. Touch no other file.

Field spec, in yards, matching the tracking data:
1. Axes: x fixed to [0, 120], y fixed to [0, 53.3]. y axis scaleanchor "x" with scaleratio 1, so a yard is the same length in both directions. Hide axes, ticks, grid lines and zero lines. Turn off autorange.
2. Grass: green rectangle from x = 10 to 110. End zones (0–10 and 110–120) in a darker green.
3. Yard lines: white vertical lines every 5 yards from x = 10 to x = 110. Goal lines (10 and 110) and the 50 (x = 60) slightly thicker.
4. Yard numbers: 10, 20, 30, 40, 50, 40, 30, 20, 10 at x = 20, 30, …, 100. Place them at y ≈ 12 and y ≈ 41.3. White, bold.
5. Hash marks: short white vertical ticks, 0.7 yd long, at every whole yard from x = 11 to x = 109, centred on y = 23.58 and y = 29.75 (NFL hash positions). Also ticks along both sidelines, at y ≈ 1 and y ≈ 52.3.
6. Border: white rectangle around the whole field.
7. Layout: dark paper background, small margins, height 600, no legend yet.

Rules:
- Rectangles and yard lines are layout shapes with layer "below", so they stay fixed during animation.
- Draw all hash marks as ONE scatter trace in mode "lines", using None separators between segments, not hundreds of shapes. Name it "field", hoverinfo "skip", showlegend False. It must be trace index 0.

Add a __main__ block that writes field_preview.html. Run it and tell me where the file is.
```

**Check:** open `field_preview.html` in a browser. The field should be about 2.25 times as wide as it is tall, and the hash marks should sit between the yard numbers, closer to the middle.

---

## P2-2 · App skeleton: data, sidebar, metric

```text
Task: create app.py (Streamlit) with data loading, the sidebar and the metric header. No animation yet. Do not edit field.py.

1. load_data() with @st.cache_data:
   - if data/processed/ghost_frames.csv and data/processed/play_summary.csv both exist, load them and return source "real"
   - otherwise load data/mock/ and return source "mock"
   - returns (frames, summary, source)
2. Page: st.set_page_config(layout="wide", page_title="Ghost Defender"). Title "Ghost Defender", caption "Optimal pursuit angle vs the real one, after the catch."
3. If source is "mock", show st.warning at the top: "MOCK DATA — run data_processing.py for real plays."
4. Sidebar:
   - selectbox gameId (sorted)
   - selectbox playId, filtered to that game. Label each option as "Play 1 · 11.0 wasted yd", or "Play 3 · no intercept".
   - the play description below, in small text
5. Header above the field:
   - Wasted Yards as the biggest element on the page: a custom st.markdown block with the number at about 64 px.
   - Colour: below 1.0 → green, with the text "≈ optimal angle". 1–5 → amber. Above 5 → red.
   - status "no_intercept" → show "No intercept possible" instead of a number.
   - reached_carrier False → add a small line "(defender never reached the carrier)".
   - Next to it, st.metric tiles: Real defender distance (yd), Ghost distance (yd), Time to intercept (s), Ghost speed (yd/s, with speed_source in brackets).
   - Under them: "Defender: <defender_name> · Ball carrier: <carrier_name>".
6. Below the header: st.plotly_chart(draw_field()) at full container width. Use whichever argument your installed Streamlit version accepts without a deprecation warning.

Run `streamlit run app.py`, read the terminal for errors, and tell me exactly what I should see for mock play 1 and mock play 3.
```

**Check:** switching between the three mock plays changes the header correctly: red 11.0, green ≈ −0.2 "≈ optimal angle", and "No intercept possible".

---

## P2-3 · The animation

This is the biggest prompt. Put `Plan first: list the functions you will write and their signatures, then wait for my OK.` at the front.

```text
Task: in app.py add build_play_figure(play_frames, summary_row, frame_ms=100) -> go.Figure and show it instead of the static field. Do not edit field.py.

Start from draw_field() (trace 0 is the field). Add traces in exactly this order, because the animation addresses them by index:
1. Ghost planned path: static dashed gray line from (ghost_start_x, ghost_start_y) to (intercept_x, intercept_y). An empty trace if status is no_intercept.
2. Intercept point: static gray "x" marker at the intercept, hover text "Optimal intercept · t = <t_intercept, 2 dp> s". Empty if no_intercept.
3. Real defender trail: red solid line from the first frame up to the current frame.
4. Carrier trail: thin blue line, same idea.
5. Ghost Defender dot: gray #9e9e9e, opacity 0.5, size 16, white outline.
6. Real Defender dot: red #d62728, size 16.
7. Carrier dot: blue #1f77b4, size 16.
Dots come last so they draw on top.

Animation:
- One go.Frame per frameId, in sorted order, name = str(frameId), containing data for traces 3–7 only, with traces=[3, 4, 5, 6, 7].
- The figure's initial data for traces 3–7 equals the first frame.
- Play and Pause buttons (layout.updatemenus): frame duration frame_ms, transition duration 0, redraw False, mode "immediate".
- A slider under the field, one step per frame, labelled with the t column, e.g. "t = 1.2 s".
- Legend at the top, horizontal, showing only: "Ball carrier", "Real defender", "Ghost defender (optimal)". Hide legend entries for the field, trails, path and intercept.
- Hover on dots: displayName and t.
- Keep the axis ranges fixed during animation. Set them explicitly; never autorange.

Run streamlit and read the terminal for errors. Then tell me exactly what I should see on mock play 1.
```

**Check:** on mock play 1 the red dot curves as it chases, the gray dot runs straight to the X and arrives at about t = 1.9 s, and the red dot reaches the blue at about t = 3.3 s. On mock play 2 the red and gray dots move together.

→ **Checkpoint B:** when Person 1's CSVs arrive, go to `03_INTEGRATION_AND_DEMO.md`.

---

## P2-4 · Coach-facing polish

```text
Task: polish app.py. Do not edit any other file.

1. Sidebar radio "Playback speed": 0.5x, 1x, 2x → frame_ms 200, 100, 50.
2. Sidebar checkbox "Show final frame (for screenshot)". When ticked, render a static figure at the last frame with no animation controls: full real and ghost paths drawn, plus an on-field annotation near the intercept reading "Wasted: 11.0 yd" (the play's value).
3. Plotly config for st.plotly_chart: displaylogo False, and toImageButtonOptions with format "png", scale 3, filename "ghost_defender_<gameId>_<playId>".
4. An expander "How to read this" under the chart, with three short lines:
   - Blue is the ball carrier. Red is the real defender. Gray is the Ghost: the same defender running the optimal straight-line angle at his top speed in this play.
   - The dashed line and X show where the Ghost meets the carrier, assuming the carrier keeps his speed and direction from the catch.
   - Wasted Yards = distance the real defender ran before contact − distance the Ghost needed. Under 1 yard counts as optimal.
5. Make sure switching plays resets the animation to the first frame, with no leftover frames from the previous play.

Run it and check the terminal for errors.
```

**Check:** tick the final-frame box and click the camera icon on the chart. You should get a sharp PNG with the annotation visible.

---

## P2-5 · Leaderboard tab (stretch)

Skip this if time is short. It is the feature a scout would use, and it helps you find demo plays fast.

```text
Task: add tabs to app.py: "Play viewer" (everything built so far) and "Worst angles". Do not edit any other file.

In "Worst angles":
1. A table of the 25 plays with the largest wasted_yards, among status "ok" and reached_carrier True. Columns: game, play, defender, carrier, wasted, real, ghost, description (cut to 80 characters). Numbers to 1 dp.
2. A defender leaderboard: group by defender_name, keep defenders with at least 3 plays. Show plays, mean wasted, total wasted. Top 15 by mean wasted.
3. Above the tables, a selectbox "Open play" listing the top 25. Choosing one sets the sidebar's gameId and playId. Do this with an on_change callback that writes the sidebar widgets' session_state keys, because setting a widget's key after it has been created raises an error. Then show st.info("Switch to the Play viewer tab").

It must still work on mock data, where the tables will be short.
```

**Check:** pick a play in "Open play", switch tabs, and the viewer shows that play.
