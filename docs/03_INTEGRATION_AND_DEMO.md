# 03 · Integration, Demo and README (both people, v2)

Start this at **Checkpoint B**: Person 1 has real CSVs in `data/processed/`, and Person 2 has a working v2 animation on mock data.

---

## I-1 · Hand-over

1. Person 1 copies `data/processed/ghost_frames.csv` and `data/processed/play_summary.csv` to Person 2 (USB, shared drive or chat; they are git-ignored on purpose).
2. Person 2 drops them into `data/processed/`.
3. Person 2 restarts Streamlit. The yellow MOCK DATA banner should disappear. If it does not, the filenames or folder are wrong.

---

## I-2 · Integration check (Person 2 runs this)

```text
Task: integration check. data/processed/ now holds real data from Person 1.

1. Write scratch_check_contract.py (throwaway, own code, do not import Person 1's files). It loads both real CSVs and checks they match the v2 contract in CLAUDE.md: column names and order, the four player_type values, exactly 4 rows per (gameId, playId, frameId), and that every summary play has frames. Run it and show the output.
2. Run the app and open these plays: <paste Person 1's three demo picks from P1-7>. Report any exception from the terminal.
3. Confirm load_data is cached and build_play_figure only receives the selected play's rows, so switching plays is fast on the full file.

Fix app.py only. If the CSVs break the contract, stop and tell me exactly what is wrong so Person 1 can fix it.
```

**Check:** all three demo plays animate without errors, and switching between plays takes under about a second.

---

## I-3 · Picking the demo play

A good demo play has:

- wasted_yards between about 2 and 8 (big enough to see, small enough to be believable)
- ghost_reached True, so the gray dot visibly beats the red one to the X
- air time of at least 1.5 s, so the animation has room to breathe
- a visible bend or false step in the red path, which is the "bad angle" the whole tool is about
- ideally a completed pass, so the story is "the right angle could have broken this up"

Watch your three candidates at 0.5x and pick the clearest. Keep one out-of-range play in your back pocket: it shows the tool doesn't blame a defender who never had a chance.

---

## I-4 · Recording and screenshot

**Screen recording (30–60 seconds):**
1. Start your OS screen recorder on the browser window.
2. Sidebar → select the demo play → Playback speed 0.5x (0.25x if the throw is short).
3. Press Play. Let it run to the end.
4. Optional: open the out-of-range play to show the contrast.

**High-resolution screenshot:**
1. Tick "Show final frame (for screenshot)".
2. Click the camera icon at the top right of the chart. The PNG comes out at triple resolution.
3. If the judges need the Wasted Yards header in the image too, take a full-window screenshot as well.

**Talking points for the narration:**
1. The problem: while the ball is in the air, a defender has a second or two to pick his path. A false step or a rounded angle is the difference between a pass breakup and a completion, and it's hard to see on film.
2. What you are looking at: brown is the ball, blue the receiver, red the real defender, gray the Ghost running a straight line to the catch point at the same player's top speed.
3. The number: when the ball arrived, the defender was X yards from the catch point. With the optimal angle he'd have been Y. That's Z wasted yards.
4. The use: rank every defender by wasted yards and pull the worst clips straight into film study.

---

## I-5 · README (either person)

The original README draft says "post-catch" and "tackle", which no longer matches what the tool does. Use this revised draft:

> **Ghost Defender: Pursuit Angle & Wasted Yardage Optimizer**
> This tool measures how well a defender attacks the catch point while the ball is in the air. At the moment of the throw, it launches a simulated "Ghost Defender" from the real defender's position, running a straight line to the spot where the ball arrives at that player's own top speed. Comparing how far each was from the catch point when the ball got there gives Wasted Yards: the ground a defender gave away through his choice of path. Defensive coaches and scouts can use the interactive view to grade reactions and pursuit angles, find the plays where a better path would have contested the catch, and show players the correct geometry in film study.

```text
Task: write README.md. Use the revised draft above as the opening section, word for word.

Then add these sections:
1. Quick start: create the venv, pip install -r requirements.txt, put the competition CSVs in data/raw/, run python data_processing.py, run streamlit run app.py. Mention that the app falls back to mock data (python make_mock_data.py) when data/processed/ is empty.
2. How it works, in three short paragraphs: the play window (throw to ball arrival, and why: the tracking data stops when the pass arrives); choosing the targeted receiver (nearest to the ball on arrival) and the defender (nearest to that receiver at the throw); the ghost and the Wasted Yards formula, real gap minus ghost gap.
3. Assumptions and limitations, as a short list:
   - the catch point is known in hindsight; a real defender has to read it
   - the Ghost reaches top speed instantly at the throw, with no reaction time or acceleration
   - the Ghost's top speed is the defender's own top speed on that play
   - only the defender nearest the targeted receiver at the throw is graded
   - throwaways (no receiver within 3 yards of the ball) are skipped
   - "out of range" plays are shown but not counted against the defender
4. Repository layout (one line per file).
5. Team.

Keep everything after the draft under 600 words, in plain language a coach could follow.
```

**Check:** follow your own Quick start in a fresh terminal. If any command fails, fix the README before submitting.

---

## Final submission checklist

- [ ] `pytest` passes (physics and golden-play tests)
- [ ] `python data_processing.py` runs on the real data and writes both CSVs
- [ ] `streamlit run app.py` shows real data (no MOCK banner)
- [ ] Screen recording of the demo play
- [ ] High-resolution PNG of the final frame with Wasted Yards
- [ ] README with the revised draft, Quick start, How it works, Assumptions
- [ ] Everything committed and pushed (data excluded)
