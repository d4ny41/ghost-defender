# 00 · Setup and Workflow (both people, read first)

## How this pack is organised

| File | Who | When |
|---|---|---|
| `00_SETUP_AND_WORKFLOW.md` | Both | First 10 minutes |
| `CLAUDE.md` | Both agents | Goes into the repo; agents read it automatically |
| `01_PERSON1_BACKEND_PROMPTS.md` | Person 1 | Prompts P1-0 to P1-7, in order |
| `02_PERSON2_FRONTEND_PROMPTS.md` | Person 2 | Prompts P2-0 to P2-5, in order |
| `03_INTEGRATION_AND_DEMO.md` | Both | After Checkpoint B |

The key idea: `CLAUDE.md` defines the maths, the file ownership and the exact CSV columns. Person 2 builds against mock data in that format from minute one, so neither of you waits for the other.

## Step 1 — One-time repo setup (one person, about 10 minutes)

1. Create an empty folder `ghost-defender`, open it in Kiro, and `git init`.
2. Copy `CLAUDE.md` from this pack into the repo root.
3. Create `.kiro/steering/ghost-defender.md` with the same content. Kiro loads steering files into every chat by default, and Claude Code loads `CLAUDE.md` from the repo root automatically, so both tools see the same rules.
4. Put the competition CSVs into `data/raw/`.
5. Paste **Prompt S0** below into the agent.
6. Commit, push, and have the other person clone.

### Prompt S0 — skeleton

```text
Create the project skeleton described in CLAUDE.md. Do not write any logic yet.

1. Create folders: data/raw, data/processed, data/mock, tests.
2. Create requirements.txt containing, one per line: pandas, numpy, pytest, streamlit, plotly.
3. Create .gitignore ignoring: .venv/, __pycache__/, .pytest_cache/, data/raw/, data/processed/, *.html.
4. Create empty placeholder files: physics.py, data_processing.py, field.py, app.py, make_mock_data.py, tests/__init__.py.
5. Create a virtual environment in .venv and install requirements.txt into it.
6. Run `python -c "import pandas, numpy, streamlit, plotly; print('ok')"` inside the venv and show the output.

Do not touch CLAUDE.md or anything in data/raw.
```

## Step 2 — Rules for prompting (both people)

1. **Paste prompts verbatim, one at a time.** Each one is a single micro-task with a built-in check.
2. **Read the "Check" line under each prompt** and confirm it yourself before moving on. The agent saying "done" is not the check.
3. **Commit after every passing step.** For example: `git add -A && git commit -m "P1-3 identify actors"`. If the agent wrecks something later, you roll back one step instead of ten.
4. **For the two large prompts (P1-4 and P2-3)**, put this line in front of the prompt: `Plan first: list the functions you will write and their signatures, then wait for my OK.` Read the plan, reply "OK", then let it build.
5. **If the agent drifts**, reply: `Stop. Re-read CLAUDE.md. Only do <the task>. Undo changes to any other file.`
6. **In Kiro, use a normal chat (Vibe) session, not a Spec session.** These prompts already are the spec; generating requirements, design and task files would cost you time.
7. **Start a fresh chat every two or three prompts.** Long chats make agents sloppy. `CLAUDE.md` carries the context across, which is why it exists.
8. **Never let the agent change expected numbers in a test.** The golden-play numbers in `CLAUDE.md` were computed independently. If a test fails, the code is wrong.

## Step 3 — Checkpoints

**Checkpoint A** (Person 1 finishes P1-1, Person 2 finishes P2-0)
Spend two minutes together. Person 1's physics tests pass. Person 2's mock prints `wasted_yards 11.00` for play 1. Two independent implementations agreeing on 11.00 is strong evidence that the maths is right.

**Checkpoint B** (Person 1 finishes P1-6, Person 2 finishes P2-3)
Person 1 hands over `data/processed/` (copy the two CSVs; they are git-ignored). Go to `03_INTEGRATION_AND_DEMO.md`.

**Checkpoint C** (after integration)
Record the demo, take the screenshot, write the README.

## Fallbacks if time runs short

- **Full dataset too slow:** process one tracking file only (`--weeks 1`). A few hundred plays is plenty for a demo.
- **Real-data parsing stuck:** the app still runs on mock data. If you demo on mock data, say so clearly in the video.
- **Leaderboard (P2-5) unfinished:** skip it. The play viewer is the core deliverable.
