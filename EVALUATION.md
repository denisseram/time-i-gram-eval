# Scoring the runs

After the 60 runs (`runner.py status` says 60/60). Decisions (2026-11-05): one human evaluator plus an
automatic judge; partially blind; scored in a local app; before/after screenshots as evidence of interaction.

## Design

| Phase | What | How | Blind? |
|---|---|---|---|
| 1 Blind | static requirements (most of them) | the official `render.png` of each run, under an anonymous code (`E3-07`), examples grouped, runs in random order | yes: tool and run hidden |
| 2 Live & code | interactive requirements (E3 R5; E5 R2, R3, R5) and code requirements (E5 R6) | the live render and the code; before/after screenshots saved as evidence | no: tool visible |
| Judge | the same static requirements as phase 1 | Claude (`claude-opus-5-5`) sees the same anonymous screenshot, requirements, rubric and ground truth | yes |

Which requirement is in which phase: `scripts/score_config.json`. Final scores are the human's (after
reviewing the disagreements with the judge); the judge only measures agreement.

## Steps

1. **Libraries for the live phase** (once): `cd gallery && npm install && cd ..`
2. **Anonymous codes** (once): `python3 scripts/score.py blind` → `results/blind_key.csv`. Do not open this
   file until phase 1 is finished.
3. **Phase 1, blind**: `python3 scripts/score.py serve`, open http://127.0.0.1:8800, tab *1 · Blind*. For
   each screenshot, score every requirement 0/1/2 with its rubric (shown under it); ground-truth checks are at
   the bottom. Each click is saved immediately in `results/scores-denisse.csv`; you can stop (Ctrl+C) and
   continue later. `python3 scripts/score.py progress` shows how far you are.
4. **Phase 2, live & code**: same app, tab *2 · Live & code* (E3 and E5 only). For each run: take a screenshot
   *before*, do the interaction (brush in the linear view for E3; brush/zoom in the overview and zoom into the
   detail for E5), take a screenshot *after*, paste both into the boxes, and score. For E5 R6 open the code.
   ggtime outputs are static; score them by the rubric (static linking = 0 for E3 R5).
5. **Judge** (Docker running, external disk connected, `.env` with the token):
   `caffeinate -i python3 scripts/judge.py`. Resumable; stops at the usage limit (run again later).
   It is independent of steps 3–4 and can run before, during or after them.
6. **Agreement and disagreements**: `python3 scripts/score.py summary` → `results/summary.md`,
   `results/disagreements.csv`. Look at each disagreement (code, requirement, your score, the judge's score
   and reason). If you now think your score was wrong, change it in the app (phase 1); if not, keep it.
   Record the number of changed scores in the paper. Then run `summary` again.
7. **Results**: `results/summary.md` (score per example and tool, requirements met, effort, agreement),
   `results/scores.csv` (one row per run, used by the gallery). `python3 scripts/build_gallery.py` and
   `cd gallery && npm run dev` to see every run with its code, scores and evidence.
8. **Commit**: `git add results runs && git commit -m "Scores" && git push` (never `git add -A`: `.env`).

## Notes for the paper

- Report: one human evaluator, partially blind (static requirements on anonymized screenshots; interactive
  and code requirements unblinded), agreement with an automatic judge (exact agreement and quadratic-weighted
  Cohen's kappa, per example), and how many human scores changed after reviewing the disagreements.
- The judge is from the same model family as the agents (possible self-preference); its scores are not used
  in the results.
- Screenshots can reveal the tool through its default style (e.g. ggplot2's grey background), so the blind
  phase is only partly blind.
