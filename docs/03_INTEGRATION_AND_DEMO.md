# 03 · Integration, Demo and README (both people)

Start this at **Checkpoint B**: Person 1 has real CSVs in `data/processed/`, and Person 2 has a working animation on mock data.

---

## I-1 · Hand-over

1. Person 1 copies `data/processed/ghost_frames.csv` and `data/processed/play_summary.csv` to Person 2 (USB, shared drive or chat; they are git-ignored on purpose).
2. Person 2 drops them into `data/processed/`.
3. Person 2 restarts Streamlit. The yellow MOCK DATA banner should disappear. If it does not, the filenames or folder are wrong.

---

## I-2 · Integration check (Person 2 runs this)

```text
Task: integration check. data/processed/ now holds real data from Person 1.

1. Write scratch_check_contract.py (throwaway, own code, do not import Person 1's files). It loads both real CSVs and checks they match the CLAUDE.md contract: column names and order, player_type values, exactly 3 rows per (gameId, playId, frameId), status values, and that every summary play has frames. Run it and show the output.
2. Run the app and open these plays: <paste Person 1's three demo picks from P1-7>. Report any exception from the terminal.
3. Confirm load_data is cached and build_play_figure only receives the selected play's rows, so switching plays is fast on the full file.

Fix app.py only. If the CSVs break the contract, stop and tell me exactly what is wrong so Person 1 can fix it.
```

**Check:** all three demo plays animate without errors, and switching between plays takes under about a second.

---

## I-3 · Picking the demo play

Choose the one play you will show the judges. A good demo play has:

- wasted_yards between about 8 and 25 (big enough to see, small enough to be believable)
- reached_carrier True, so the red dot visibly catches the blue one
- a visible curve in the red path, which is the "bad angle" the whole tool is about
- a carrier who runs roughly straight after the catch, because the Ghost assumes constant velocity, so the comparison looks fairest

Watch your three candidates at 0.5x speed and pick the clearest.

---

## I-4 · Recording and screenshot

**Screen recording (30–60 seconds):**
1. Start your OS screen recorder on the browser window.
2. Sidebar → select the demo play → set Playback speed to 0.5x.
3. Press Play. Let it run to the end.
4. Optional: switch to a second play to show it works on any play.

**High-resolution screenshot:**
1. Tick "Show final frame (for screenshot)".
2. Click the camera icon at the top right of the chart. Because of the scale-3 setting from P2-4, the PNG comes out at triple resolution.
3. If the judges need the Wasted Yards header in the image too, take a full-window screenshot as well.

**Talking points for the narration:**
1. The problem: after a catch, the defender's first steps decide whether a 5-yard gain becomes 25. Bad pursuit angles are hard to see in real time.
2. What you are looking at: blue carrier, red real defender, gray Ghost running the optimal angle at the same player's top speed.
3. The number: this defender ran X yards to make contact; the optimal route needed Y; that is Z wasted yards.
4. The use: rank every defender by wasted yards across a season and pull the worst clips straight into film study.

---

## I-5 · README (either person)

```text
Task: write README.md. Keep the following draft as the opening section, word for word:

<paste the team's draft paragraph here>

Then add these sections:
1. Quick start: create the venv, pip install -r requirements.txt, put the competition CSVs in data/raw/, run python data_processing.py, run streamlit run app.py. Mention that the app falls back to mock data (python make_mock_data.py) when data/processed/ is empty.
2. How it works, in three short paragraphs: the play window (catch to tackle or out of bounds); choosing the carrier and the nearest defender; the intercept maths, showing the quadratic a·t² + b·t + c = 0 with a, b and c defined as in CLAUDE.md; and the Wasted Yards metric.
3. Assumptions and limitations, as a short list:
   - the carrier is assumed to hold his speed and direction from the moment of the catch
   - the Ghost runs at the defender's top speed in that play from the first frame, with no acceleration phase
   - only the defender nearest the carrier at the catch is graded
   - contact means within 1 yard, so values under 1 yard count as optimal
   - plays with no possible intercept are reported, not scored
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
- [ ] README with the draft, Quick start, How it works, Assumptions
- [ ] Everything committed and pushed (data excluded)
